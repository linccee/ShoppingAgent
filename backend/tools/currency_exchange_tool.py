import json

import requests
from langchain.tools import tool
from backend.app.config import Config


@tool
def currency_exchange(base_code: str, target_code: str, amount: str) -> str:
    """
    当用户的货币单位不是 USD，或者需要将价格转换为其他货币时，调用此工具进行汇率转换。

    Args:
        base_code: 原货币单位的 ISO 4217 代码，如 CNY、EUR、JPY
        target_code: 目标货币单位的 ISO 4217 代码，如 USD、GBP
        amount: 需要转换的金额（字符串形式），如 "3000"

    Returns:
        JSON 格式的结果，包含 conversion_rate（汇率）和 conversion_result（转换后金额）
    """
    url = f"https://v6.exchangerate-api.com/v6/{Config.EXCHANGE_RATE_API_KEY}/pair/{base_code}/{target_code}/{amount}"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
    except Exception as e:
        return json.dumps({"success": False, "error": f"网络请求失败: {e}"}, ensure_ascii=False)

    if data.get("result") != "success":
        return json.dumps({
            "success": False,
            "error": f"API 请求失败，错误类型: {data.get('error-type', '未知错误')}"
        }, ensure_ascii=False)

    # 返回精简后的有效字段，避免把无关字段投入 context
    return json.dumps({
        "success": True,
        "base_code": data.get("base_code"),
        "target_code": data.get("target_code"),
        "conversion_rate": data.get("conversion_rate"),
        "conversion_result": data.get("conversion_result"),
    }, ensure_ascii=False)
