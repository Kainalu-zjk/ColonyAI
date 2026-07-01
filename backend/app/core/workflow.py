"""工作流模块，编排多 Agent 协作完成数学建模任务。"""

import asyncio
from app.core.agents import WriterAgent, CoderAgent, CoordinatorAgent, ModelerAgent
from app.schemas.request import Problem
from app.schemas.response import SystemMessage
from app.tools.openalex_scholar import OpenAlexScholar
from app.utils.log_util import logger
from app.utils.common_utils import create_work_dir, get_config_template
from app.models.user_output import UserOutput
from app.config.setting import settings
from app.tools.interpreter_factory import create_interpreter
from app.services.redis_manager import redis_manager
from app.tools.notebook_serializer import NotebookSerializer
from app.core.flows import Flows
from app.core.llm.llm_factory import LLMFactory
from app.schemas.enums import CompTemplate
from app.utils.i18n import t


class WorkFlow:
    """工作流基类。"""

    def __init__(self):
        pass

    def execute(self) -> None:
        pass


class MathModelWorkFlow(WorkFlow):
    """数学建模工作流，协调协调者、建模手、代码手和写作手完成完整建模任务。"""
    task_id: str  #
    work_dir: str  # worklow work dir
    ques_count: int = 0  # 问题数量
    questions: dict[str, str | int] = {}  # 问题
    cancel_event: asyncio.Event | None = None  # 取消信号

    async def _check_cancelled(self) -> None:
        """检查是否收到取消信号，若已取消则发布通知并抛出 CancelledError。"""
        if self.cancel_event and self.cancel_event.is_set():
            await redis_manager.publish_message(
                self.task_id,
                SystemMessage(content=t("messages.workflow.task_stopped", lang=self.lang), type="warning"),
            )
            raise asyncio.CancelledError("任务被用户停止")

    async def execute(self, problem: Problem):  # type: ignore[reportIncompatibleMethodOverride]
        """执行数学建模工作流。

        Args:
            problem: 包含题目信息、模板配置等的 Problem 对象。
        """
        self.task_id = problem.task_id
        self.work_dir = create_work_dir(self.task_id)
        # Determine language from competition template
        self.lang = "en" if problem.comp_template == CompTemplate.AMERICAN else "zh"

        llm_factory = LLMFactory(self.task_id)
        coordinator_llm, modeler_llm, coder_llm, writer_llm = llm_factory.get_all_llms()

        coordinator_agent = CoordinatorAgent(
            self.task_id, coordinator_llm,
            context_window=settings.COORDINATOR_CONTEXT_WINDOW,
            cancel_event=self.cancel_event,
            lang=self.lang,
        )

        await redis_manager.publish_message(
            self.task_id,
            SystemMessage(content=t("messages.workflow.coordinator_start", lang=self.lang)),
        )

        await self._check_cancelled()

        try:
            coordinator_response = await coordinator_agent.run(problem.ques_all)
            self.questions = coordinator_response.questions
            self.ques_count = coordinator_response.ques_count
        except Exception as e:
            logger.error(f"CoordinatorAgent 执行失败: {e}")
            raise e

        await redis_manager.publish_message(
            self.task_id,
            SystemMessage(content=t("messages.workflow.coordinator_done", lang=self.lang)),
        )

        await redis_manager.publish_message(
            self.task_id,
            SystemMessage(content=t("messages.workflow.modeler_start", lang=self.lang)),
        )

        await self._check_cancelled()

        modeler_agent = ModelerAgent(
            self.task_id, modeler_llm,
            context_window=settings.MODELER_CONTEXT_WINDOW,
            cancel_event=self.cancel_event,
            lang=self.lang,
        )

        modeler_response = await modeler_agent.run(coordinator_response)

        user_output = UserOutput(work_dir=self.work_dir, ques_count=self.ques_count)

        await redis_manager.publish_message(
            self.task_id,
            SystemMessage(content=t("messages.workflow.sandbox_creating", lang=self.lang)),
        )

        notebook_serializer = NotebookSerializer(work_dir=self.work_dir)
        code_interpreter = await create_interpreter(
            kind="local",
            task_id=self.task_id,
            work_dir=self.work_dir,
            notebook_serializer=notebook_serializer,
            timeout=3000,
        )

        assert settings.OPENALEX_EMAIL is not None, t("messages.scholar.email_required", lang=self.lang)
        scholar = OpenAlexScholar(
            task_id=self.task_id,
            email=settings.OPENALEX_EMAIL,
            api_key=settings.OPENALEX_API_KEY,
        )

        await redis_manager.publish_message(
            self.task_id,
            SystemMessage(content=t("messages.workflow.sandbox_created", lang=self.lang)),
        )

        await redis_manager.publish_message(
            self.task_id,
            SystemMessage(content=t("messages.workflow.coder_init", lang=self.lang)),
        )

        coder_agent = CoderAgent(
            task_id=problem.task_id,
            model=coder_llm,
            work_dir=self.work_dir,
            max_chat_turns=settings.MAX_CHAT_TURNS,
            max_retries=settings.MAX_RETRIES,
            code_interpreter=code_interpreter,
            context_window=settings.CODER_CONTEXT_WINDOW,
            cancel_event=self.cancel_event,
            lang=self.lang,
        )

        writer_agent = WriterAgent(
            task_id=problem.task_id,
            model=writer_llm,
            comp_template=problem.comp_template,
            format_output=problem.format_output,
            scholar=scholar,
            context_window=settings.WRITER_CONTEXT_WINDOW,
            cancel_event=self.cancel_event,
            lang=self.lang,
        )

        flows = Flows(self.questions)

        ################################################ solution steps
        solution_flows = flows.get_solution_flows(self.questions, modeler_response)
        config_template = get_config_template(problem.comp_template)

        for key, value in solution_flows.items():
            await self._check_cancelled()

            await redis_manager.publish_message(
                self.task_id,
                SystemMessage(content=t("messages.workflow.coder_start", lang=self.lang, task=key)),
            )

            coder_response = await coder_agent.run(
                prompt=value["coder_prompt"], subtask_title=key
            )

            await redis_manager.publish_message(
                self.task_id,
                SystemMessage(content=t("messages.workflow.coder_done", lang=self.lang, task=key), type="success"),
            )

            writer_prompt = flows.get_writer_prompt(
                key, coder_response.code_response or "", code_interpreter, config_template
            )

            await redis_manager.publish_message(
                self.task_id,
                SystemMessage(content=t("messages.workflow.writer_start", lang=self.lang, task=key)),
            )

            writer_response = await writer_agent.run(
                writer_prompt,
                available_images=coder_response.created_images,
                sub_title=key,
            )

            await redis_manager.publish_message(
                self.task_id,
                SystemMessage(content=t("messages.workflow.writer_done", lang=self.lang, task=key)),
            )

            user_output.set_res(key, writer_response)

        await code_interpreter.cleanup()
        logger.info(user_output.get_res())

        ################################################ write steps

        write_flows = flows.get_write_flows(
            user_output, config_template, problem.ques_all
        )
        for key, value in write_flows.items():
            await self._check_cancelled()

            await redis_manager.publish_message(
                self.task_id,
                SystemMessage(content=t("messages.workflow.writer_start", lang=self.lang, task=key)),
            )

            writer_response = await writer_agent.run(prompt=value, sub_title=key)

            user_output.set_res(key, writer_response)

        logger.info(user_output.get_res())

        user_output.save_result()
