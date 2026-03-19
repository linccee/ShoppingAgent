from langchain_openai import ChatOpenAI
from backend.app.config import Config
from langchain.tools import tool
import serpapi
import json


@tool
def analyze_reviews(product_sku: str, platform: str) -> str:
    """
    分析某商品的用户评论，提取核心优缺点和情感倾向。
    当需要了解用户对某商品的真实评价时调用此工具。

    Args:
        product_sku: 商品的唯一编号（Amazon 用 ASIN，如 B0GHRHXVN1；eBay 用 product_id）
        platform: 平台名称，只能是 "Amazon" 或 "eBay"

    Returns:
        结构化的评论分析报告，包含优点、缺点、情感评分
    """
    platform_lower = platform.strip().lower()

    # 验证平台参数
    if platform_lower not in ["amazon", "ebay"]:
        return _format_error("不支持的平台，请使用 'Amazon' 或 'eBay'")

    # 获取评论数据
    try:
        if platform_lower == "amazon":
            reviews_data = _fetch_amazon_reviews(product_sku)
        else:
            reviews_data = _fetch_ebay_reviews(product_sku)
    except Exception as e:
        return _format_error(f"获取评论失败: {str(e)}")

    # 检查是否有评论数据
    if not reviews_data.get("reviews") or len(reviews_data.get("reviews", [])) == 0:
        return _format_error(f"未能获取到 {product_sku} 的评论数据")

    # 统一返回 JSON 字符串（保持与工具签名一致）
    return json.dumps(reviews_data, ensure_ascii=False)


def _fetch_amazon_reviews(asin: str) -> dict:
    """获取Amazon商品评论"""
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

    reviews = []
    product_results = result.get("product_results", {})
    reviews_info = result.get("reviews_information", {})
    reviews_summary = reviews_info.get("summary", {"text": "(获取评价总结失败，可能是没有此条目)"}).get("text")

    overall_rating = product_results.get("rating", "")
    reviews_count = product_results.get("reviews", 0)

    authors_reviews = reviews_info.get("authors_reviews", [])
    for review in authors_reviews:
        reviews.append({
            "title": review.get("title", ""),
            "content": review.get("text", ""),
            "rating": review.get("rating", ""),
            "author": review.get("author", ""),
            "date": review.get("date", ""),
            "verified": review.get("verified_purchase", False)
        })

    summary_text = reviews_info.get("summary", {}).get("text", "")

    return {
        "platform": "Amazon",
        "product_id": asin,
        "overall_rating": overall_rating,
        "reviews_count": reviews_count,
        "summary_text": summary_text,
        "reviews_summary": reviews_summary,
        "reviews": reviews
    }


def _fetch_ebay_reviews(product_id: str) -> dict:
    """获取eBay商品评论"""
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

    seller_results = result.get("seller_results", {})
    reviews_groups = seller_results.get("reviews", {}).get("groups", {})
    this_product = reviews_groups.get("this_product", reviews_groups.get("all_products", {}))
    this_product_list = this_product.get("list", [])[:10]
    reviews_count = this_product.get("count", 0)

    return {
        "platform": "eBay",
        "product_id": product_id,
        "reviews_count": reviews_count,
        "reviews": this_product_list
    }


def _format_error(message: str) -> str:
    """格式化错误消息"""
    return json.dumps({
        "success": False,
        "error": message,
        "note": "请停止对此商品发送评论分析请求，并向用户报告此问题。"
    }, ensure_ascii=False)
