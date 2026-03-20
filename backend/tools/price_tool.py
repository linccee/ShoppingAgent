import json
import serpapi
from langchain.tools import tool
from backend.app.config import Config
from backend.app.utils.logging_config import tools_logger

# 货币符号映射
CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CNY": "¥",
    "AUD": "A$",
    "CAD": "C$",
    "INR": "₹",
    "KRW": "₩",
}


def _get_currency_symbol(currency: str) -> str:
    """根据货币类型获取对应的货币符号"""
    return CURRENCY_SYMBOLS.get(currency.upper(), currency)


@tool
def prices(product_sku: str, platform: str) -> str:
    """
    获取指定商品在特定平台的实时价格信息。
    当已知商品编号（SKU）时调用，获取精确价格。

    Args:
        product_sku: 商品的唯一编号（Amazon 用 ASIN，如 B0GHRHXVN1；eBay 用 product_id）
        platform: 平台名称，只能是 "Amazon" 或 "eBay"

    Returns:
        结构化的价格信息，包含价格、平台、商品ID、标题和链接
    """
    tools_logger.info(f"[TOOLS] prices called for SKU: {product_sku} on platform: {platform}")
    platform_lower = platform.strip().lower()

    # 验证平台参数
    if platform_lower not in ["amazon", "ebay"]:
        tools_logger.warning(f"[TOOLS] prices failed: invalid platform {platform}")
        return json.dumps({
            "success": False,
            "error": "不支持的平台，请使用 'Amazon' 或 'eBay'"
        }, ensure_ascii=False)

    try:
        if platform_lower == "amazon":
            tools_logger.debug(f"[TOOLS] Fetching Amazon price for ASIN: {product_sku}")
            price_data = _fetch_amazon_price(product_sku)
        else:
            tools_logger.debug(f"[TOOLS] Fetching eBay price for product_id: {product_sku}")
            price_data = _fetch_ebay_price(product_sku)
    except Exception as e:
        tools_logger.error(f"[TOOLS] prices failed for SKU {product_sku}: {e}")
        return json.dumps({
            "success": False,
            "error": f"获取价格失败: {str(e)}"
        }, ensure_ascii=False)

    if not price_data:
        tools_logger.warning(f"[TOOLS] prices: no data found for SKU {product_sku}")
        return json.dumps({
            "success": False,
            "error": f"未能获取到 {product_sku} 的价格数据"
        }, ensure_ascii=False)

    tools_logger.info(f"[TOOLS] prices success for SKU {product_sku}: {price_data.get('price')}")
    return json.dumps({
        "success": True,
        "price": price_data.get("price"),
        "platform": price_data.get("platform"),
        "product_id": price_data.get("product_id"),
        "title": price_data.get("title"),
        "url": price_data.get("url"),
        "delivery": price_data.get("delivery", ['没有提供具体信息'])
    }, ensure_ascii=False)


def _fetch_amazon_price(asin: str) -> dict:
    """获取Amazon商品价格"""
    api_key = Config.SERPAPI_KEY

    if not api_key:
        raise ValueError("未配置 SerpApi API Key")

    params = {
        "api_key": api_key,
        "engine": "amazon_product",
        "asin": asin,
    }

    result = serpapi.search(**params)

    if hasattr(result, 'get'):
        result = dict(result)

    product_results = result.get("product_results", {})

    price = product_results.get("price", {})
    price_discount = product_results.get("discount", 1)
    old_price = product_results.get("old_price", price)
    delivery = product_results.get("delivery", [])

    title = product_results.get("title", "")
    url = product_results.get("link_clean", "")

    return {
        "price": {
            "amount": price,
            "discount": price_discount,
            "old_price": old_price
        },
        "platform": "Amazon",
        "delivery": delivery,
        "product_id": asin,
        "title": title,
        "url": url
    }


def _fetch_ebay_price(product_id: str) -> dict:
    """获取eBay商品价格"""
    api_key = Config.SERPAPI_KEY

    if not api_key:
        raise ValueError("未配置 SerpApi API Key")

    params = {
        "api_key": api_key,
        "engine": "ebay_product",
        "product_id": product_id,
        "ebay_domain": "ebay.com"
    }

    result = serpapi.search(**params)

    if hasattr(result, 'get'):
        result = dict(result)

    product_results = result.get("product_results", {})

    price = product_results.get("buy", {}).get("buy_it_now", {}).get("price", {})
    if isinstance(price, dict):
        price_amount = price.get("amount", "")
        price_currency = price.get("currency", "USD")
    else:
        price_amount = price
        price_currency = "USD"

    currency_symbol = _get_currency_symbol(price_currency)

    title = product_results.get("title", "")
    url = product_results.get("product_link", "")

    return {
        "price": {
            "amount": f"{currency_symbol}{price_amount}",
            "currency": price_currency,
        },
        "platform": "eBay",
        "product_id": product_id,
        "title": title,
        "url": url
    }
