from langchain.tools import tool
import json
import re

from backend.app.config import Config
from backend.app.utils.logging_config import tools_logger


@tool
def search_products(query: str) -> str:
    """
    根据用户需求搜索商品。
    当用户想要了解某类商品有哪些选择时调用此工具。

    参数说明：
        query: 搜索关键词，必须为英文，例如 'PlayStation 5 Slim'
               注意：禁止在 query 中添加年份、日期或时间范围（如 2024、2025），直接使用核心关键词即可。

    返回：
        JSON 格式的候选商品列表，仅保留后续工具调用所需的最小字段：
        title、platform、product_sku
    """
    import serpapi

    tools_logger.info(f"[TOOLS] search_products called with query: {query}")

    # SerpApi 购物搜索平台配置
    # 每个平台最多返回5个商品
    platforms_config = [
        {
            "name": "Google Shopping",
            "engine": "google",
            "search_param": "q",
            "params": {"tbm": "shop"},
            "max_results": 5
        },
        {
            "name": "Amazon",
            "engine": "amazon",
            "search_param": "k",
            "params": {"amazon_domain": "amazon.com"},
            "max_results": 5
        },
        {
            "name": "eBay",
            "engine": "ebay",
            "search_param": "_nkw",
            "params": {},
            "max_results": 5
        }
    ]


    api_key = Config.SERPAPI_KEY

    if not api_key:
        tools_logger.error("[TOOLS] SerpApi API Key not configured")
        return json.dumps({
            "success": False,
            "error": "未配置 SerpApi API Key，请设置 SERPAPI_API_KEY 环境变量",
            "results": []
        }, ensure_ascii=False)

    all_results = []

    # 并行搜索多个平台
    for platform in platforms_config:
        try:
            # 根据不同平台使用正确的搜索参数
            search_param = platform.get("search_param", "q")
            params = {
                "api_key": api_key,
                "engine": platform["engine"],
                search_param: query,
                "num": platform["max_results"]
            }
            params.update(platform["params"])

            tools_logger.debug(f"[TOOLS] Searching {platform['name']} with query: {query}")
            search_result = serpapi.search(**params)

            # 提取 shopping_results 或 organic_results
            shopping_results = search_result.get("shopping_results", [])
            organic_results = search_result.get("organic_results", [])


            # 优先使用 shopping_results
            items = shopping_results if shopping_results else organic_results
            tools_logger.debug(f"[TOOLS] {platform['name']} returned {len(items)} results")

            for item in items:
                item["_platform"] = platform["name"]
                item["_engine"] = platform["engine"]
                all_results.append(item)

        except Exception as e:
            tools_logger.warning(f"[TOOLS] {platform['name']} search failed: {e}")
            continue

    if not all_results:
        tools_logger.info(f"[TOOLS] No results found for query: {query}")
        return json.dumps({
            "success": True,
            "query": query,
            "results": [],
            "message": "未找到相关商品，请尝试其他搜索词"
        }, ensure_ascii=False)

    # 构建结构化结果，每个平台最多5个
    platform_count = {}
    max_per_platform = 5
    structured_results = []

    for result in all_results:
        title = result.get("title", "未知商品")
        url = result.get("link", result.get("url", ""))
        platform = result.get("_platform", "")

        # 过滤无效的 URL
        if not _is_valid_product_url(url, title):
            continue

        # 每个平台最多5个结果
        count = platform_count.get(platform, 0)
        if count >= max_per_platform:
            continue
        platform_count[platform] = count + 1

        # 提取 product_sku (eBay: product_id, Amazon: asin)
        product_sku = None
        if platform.lower() == "ebay":
            product_sku = result.get("product_id")
        elif platform.lower() == "amazon":
            product_sku = result.get("asin")

        # 只保留后续 prices / analyze_reviews 所需的候选项。
        if not product_sku:
            continue

        structured_results.append({
            "title": title,
            "platform": platform,
            "product_sku": product_sku
        })

    tools_logger.info(f"[TOOLS] search_products returning {len(structured_results)} results for query: {query}")
    return json.dumps({
        "success": True,
        "query": query,
        "total": len(structured_results),
        "results": structured_results
    }, ensure_ascii=False)

def _is_valid_product_url(url: str, title: str = "") -> bool:
    """检查 URL 是否为有效的商品详情页"""
    if not url:
        return False

    url_lower = url.lower()
    title_lower = title.lower() if title else ""

    # 过滤非详情页 URL
    invalid_patterns = [
        "login", "signin", "member login",
        "err=", "error", "404",
        "access denied",
    ]

    # 特殊处理 Amazon
    if "/dp/" in url_lower or "/gp/product/" in url_lower:
        return True

    # eBay
    if "/itm/" in url_lower:
        return True

    # Google Shopping
    if "shopping.google" in url_lower or "/url?" in url_lower:
        return True

    for pattern in invalid_patterns:
        if pattern in url_lower:
            return False

    # 过滤无效标题
    invalid_titles = ["登录", "sign in", "access denied", "error", "404"]
    for t in invalid_titles:
        if t in title_lower:
            return False

    return True
