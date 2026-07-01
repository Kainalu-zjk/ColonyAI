"""代码手 Agent 的系统提示词（i18n-ready）。

用法：
    CODER_PROMPT 是默认中文版本。
    get_coder_prompt(lang="en") 返回英文版本。
"""

import platform
from app.utils.i18n import t


def get_coder_prompt(lang: str = "zh") -> str:
    """获取代码手系统提示词。

    Args:
        lang: 语言代码（"zh" 或 "en"）。

    Returns:
        系统提示词字符串。
    """
    return t("prompts.coder.system", lang=lang, platform=platform.system())


# 默认中文版本（向后兼容）
CODER_PROMPT = get_coder_prompt("zh")
