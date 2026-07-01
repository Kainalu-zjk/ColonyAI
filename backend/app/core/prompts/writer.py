"""写作手 Agent 的系统提示词（i18n-ready）。

提供双语系统提示词：
- get_writer_prompt(format_output, lang="zh") → 中文写作提示
- get_writer_prompt(format_output, lang="en") → 英文 MCM/ICM 写作提示
"""

from app.schemas.enums import FormatOutPut
from app.utils.i18n import t


def get_writer_prompt(
    format_output: FormatOutPut = FormatOutPut.Markdown,
    lang: str = "zh",
):
    """根据输出格式和语言生成写作手的系统提示词。

    Args:
        format_output: 输出格式（Markdown 或 LaTeX）。
        lang: 语言代码（"zh" 或 "en"）。

    Returns:
        写作手系统提示词字符串。
    """
    fmt = "LaTeX" if format_output == FormatOutPut.LaTeX else "Markdown"
    key = "prompts.writer.system_en" if lang == "en" else "prompts.writer.system_zh"
    return t(key, lang=lang, format=fmt)
