"""协调者 Agent 的系统提示词（i18n-ready）。

用法：
    COORDINATOR_PROMPT 和 FORMAT_QUESTIONS_PROMPT 是默认中文版本。
    get_coordinator_prompt(lang="en") 返回指定语言的提示词。
"""

from app.utils.i18n import t


def get_coordinator_prompt(lang: str = "zh") -> str:
    """获取协调者系统提示词。

    Args:
        lang: 语言代码（"zh" 或 "en"）。

    Returns:
        系统提示词字符串。
    """
    return t("prompts.coordinator.system", lang=lang,
             format=t("prompts.coordinator.format", lang=lang))


# 默认中文版本（向后兼容）
COORDINATOR_PROMPT = get_coordinator_prompt("zh")
FORMAT_QUESTIONS_PROMPT = t("prompts.coordinator.format", lang="zh")

