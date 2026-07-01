"""建模手 Agent 的系统提示词（i18n-ready）。

用法：
    MODELER_PROMPT 是默认中文版本。
    get_modeler_prompt(lang="en") 返回英文版本。
"""

from app.utils.i18n import t


def get_modeler_prompt(lang: str = "zh") -> str:
    """获取建模手系统提示词。

    Args:
        lang: 语言代码（"zh" 或 "en"）。

    Returns:
        系统提示词字符串。
    """
    return t("prompts.modeler.system", lang=lang)


# 默认中文版本（向后兼容）
MODELER_PROMPT = get_modeler_prompt("zh")
