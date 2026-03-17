"""StateGraph node functions for the shopping workflow."""
import json
import re
from typing import Any

from agent.state import SharedState, SearchResult, PriceInfo, ReviewAnalysis, Recommendation


# ---- Node Functions ----
# Each node function follows: (state: SharedState) -> dict (partial state update)


def input_node(state: SharedState) -> dict:
    """
    输入节点 - 处理用户查询，初始化状态。

    Args:
        state: 当前状态

    Returns:
        更新 messages, workflow_status
    """
    from langchain_core.messages import HumanMessage

    user_input = state.get("user_query", "")

    return {
        "messages": state.get("messages", []) + [
            HumanMessage(content=user_input)
        ],
        "workflow_status": "running",
    }


def search_node(state: SharedState) -> dict:
    """
    搜索节点 - 调用 search_products 工具搜索候选商品。

    Args:
        state: 当前状态，需包含 user_query

    Returns:
        更新 search_results, candidate_products, steps
    """
    from tools.search_tool import search_products

    query = state.get("user_query", "")

    # 记录步骤
    steps = state.get("steps", [])
    steps.append({
        "node": "search",
        "status": "running",
        "input_data": {"query": query},
    })

    try:
        result = search_products.invoke(query)
        search_data = json.loads(result)

        if search_data.get("success") is False:
            error_message = search_data.get("error", "搜索工具执行失败")
            steps[-1]["status"] = "error"
            steps[-1]["error"] = error_message
            return {
                "workflow_status": "error",
                "error_message": f"搜索失败: {error_message}",
                "steps": steps,
            }

        results = search_data.get("results", [])
        candidate_products = results[:5]  # 取前5个

        # 更新步骤为完成
        steps[-1]["status"] = "completed"
        steps[-1]["output_data"] = {
            "total": len(results),
            "candidates": [p.get("title") for p in candidate_products],
        }

        return {
            "search_results": {
                "query": query,
                "results": results,
                "total": search_data.get("total", len(results)),
            },
            "candidate_products": candidate_products,
            "steps": steps,
        }
    except Exception as e:
        steps[-1]["status"] = "error"
        steps[-1]["error"] = str(e)
        return {
            "workflow_status": "error",
            "error_message": f"搜索失败: {str(e)}",
            "steps": steps,
        }


def price_node(state: SharedState) -> dict:
    """
    比价节点 - 获取候选商品的实时价格。

    可以与 search_node 并行执行。

    Args:
        state: 当前状态，需包含 candidate_products

    Returns:
        更新 price_info, steps
    """
    from tools.price_tool import prices

    candidates = state.get("candidate_products", [])

    # 记录步骤
    steps = state.get("steps", [])
    steps.append({
        "node": "price",
        "status": "running",
        "input_data": {"candidates_count": len(candidates)},
    })

    try:
        price_results: list[PriceInfo] = []

        for product in candidates[:3]:  # 最多处理3个
            product_sku = product.get("product_sku")
            platform = product.get("platform")

            if product_sku and platform:
                result = prices.invoke({
                    "product_sku": product_sku,
                    "platform": platform,
                })
                price_data = json.loads(result)
                if price_data.get("success"):
                    price_results.append({
                        "product_sku": product_sku,
                        "platform": platform,
                        "price": price_data.get("price", {}),
                        "title": price_data.get("title", product.get("title", "")),
                        "url": price_data.get("url", product.get("url", "")),
                    })

        # 更新步骤为完成
        steps[-1]["status"] = "completed"
        steps[-1]["output_data"] = {"prices_count": len(price_results)}

        return {
            "price_info": price_results,
            "steps": steps,
        }
    except Exception as e:
        steps[-1]["status"] = "error"
        steps[-1]["error"] = str(e)
        return {
            "workflow_status": "error",
            "error_message": f"价格查询失败: {str(e)}",
            "steps": steps,
        }


def review_node(state: SharedState) -> dict:
    """
    评论分析节点 - 分析候选商品的评论。

    可以与 search_node 并行执行。

    Args:
        state: 当前状态，需包含 candidate_products

    Returns:
        更新 review_analyses, steps
    """
    from tools.review_tool import analyze_reviews

    candidates = state.get("candidate_products", [])

    # 记录步骤
    steps = state.get("steps", [])
    steps.append({
        "node": "review",
        "status": "running",
        "input_data": {"candidates_count": len(candidates)},
    })

    try:
        review_results: list[ReviewAnalysis] = []

        for product in candidates[:3]:  # 最多处理3个
            product_sku = product.get("product_sku")
            platform = product.get("platform", "Amazon")

            if product_sku and platform:
                # 正确调用方式：传入 product_sku 和 platform
                result = analyze_reviews.invoke({
                    "product_sku": product_sku,
                    "platform": platform
                })
                review_data = json.loads(result)

                # 检查是否有错误（success=False 表示错误）
                if review_data.get("success") is False:
                    continue

                # 提取可用字段（兼容 Amazon 和 eBay 不同返回格式）
                platform_result = review_data.get("platform", platform)
                product_id = review_data.get("product_id", product_sku)
                overall_rating = review_data.get("overall_rating", "")
                reviews_count = review_data.get("reviews_count", 0)
                summary_text = review_data.get("summary_text", "")
                reviews_summary = review_data.get("reviews_summary", "")

                # 获取评论列表
                reviews_list = review_data.get("reviews", [])

                # 简单情感分析：根据评分判断
                sentiment = "neutral"
                if overall_rating:
                    try:
                        rating_float = float(overall_rating)
                        if rating_float >= 4.0:
                            sentiment = "positive"
                        elif rating_float <= 2.5:
                            sentiment = "negative"
                    except (ValueError, TypeError):
                        pass

                # 提取评论内容作为摘要
                pros = []
                cons = []
                if reviews_list:
                    # 取前5条评论内容作为参考
                    sample_reviews = reviews_list[:5]
                    review_texts = [r.get("content", "")[:200] for r in sample_reviews if r.get("content")]

                    review_results.append({
                        "product_sku": product_id,
                        "platform": platform_result,
                        "sentiment": sentiment,
                        "pros": pros,
                        "cons": cons,
                        "summary": reviews_summary or summary_text or f"共 {reviews_count} 条评论，评分 {overall_rating}",
                        # 保留原始数据供后续使用
                        "raw_reviews": reviews_list,
                        "overall_rating": overall_rating,
                        "reviews_count": reviews_count,
                    })

        # 更新步骤为完成
        steps[-1]["status"] = "completed"
        steps[-1]["output_data"] = {"reviews_count": len(review_results)}

        return {
            "review_analyses": review_results,
            "steps": steps,
        }
    except Exception as e:
        steps[-1]["status"] = "error"
        steps[-1]["error"] = str(e)
        return {
            "workflow_status": "error",
            "error_message": f"评论分析失败: {str(e)}",
            "steps": steps,
        }


def currency_node(state: SharedState) -> dict:
    """
    货币转换节点 - 处理预算货币转换。

    Args:
        state: 当前状态，需包含 user_query

    Returns:
        更新 currency_result, steps
    """
    from tools.currency_exchange_tool import currency_exchange

    user_query = state.get("user_query", "")

    # 记录步骤
    steps = state.get("steps", [])
    steps.append({
        "node": "currency",
        "status": "running",
        "input_data": {"query": user_query},
    })

    try:
        # 检测用户货币
        user_currency = _detect_currency(user_query)

        # 检测预算并转换
        budget = _extract_budget(user_query)
        converted_amount = None

        if budget and user_currency and user_currency != "USD":
            result = currency_exchange.invoke({
                "amount": str(budget),
                "base_code": user_currency,
                "target_code": "USD",
            })
            data = json.loads(result)
            if data.get("success"):
                converted_amount = data.get("conversion_result")

        # 更新步骤为完成
        steps[-1]["status"] = "completed"
        steps[-1]["output_data"] = {
            "original_currency": user_currency,
            "converted_amount": converted_amount,
        }

        return {
            "currency_result": {
                "original_currency": user_currency or "USD",
                "budget": budget,
                "converted_amount": converted_amount,
            },
            "steps": steps,
        }
    except Exception as e:
        steps[-1]["status"] = "error"
        steps[-1]["error"] = str(e)
        return {
            "steps": steps,
        }


def recommend_node(state: SharedState) -> dict:
    """
    推荐节点 - 综合所有信息生成推荐。

    依赖: price_node, review_node, currency_node

    Args:
        state: 当前状态，需包含 candidate_products, price_info, review_analyses

    Returns:
        更新 recommendations, final_response, workflow_status, steps
    """
    candidates = state.get("candidate_products", [])
    prices = state.get("price_info", [])
    reviews = state.get("review_analyses", [])
    currency_result = state.get("currency_result", {})

    # 记录步骤
    steps = state.get("steps", [])
    steps.append({
        "node": "recommend",
        "status": "running",
    })

    try:
        # 综合评分并排序
        recommendations = _rank_products(candidates, prices, reviews)

        # 生成推荐报告
        report = _generate_report(
            recommendations,
            currency_result.get("original_currency", "USD"),
        )

        # 更新步骤为完成
        steps[-1]["status"] = "completed"
        steps[-1]["output_data"] = {"recommendations_count": len(recommendations)}

        return {
            "recommendations": recommendations,
            "final_response": report,
            "workflow_status": "success",
            "steps": steps,
        }
    except Exception as e:
        steps[-1]["status"] = "error"
        steps[-1]["error"] = str(e)
        return {
            "workflow_status": "error",
            "error_message": f"推荐生成失败: {str(e)}",
            "steps": steps,
        }


def output_node(state: SharedState) -> dict:
    """
    输出节点 - 格式化最终输出。

    依赖: recommend_node

    Args:
        state: 当前状态，需包含 final_response, recommendations

    Returns:
        更新 final_response
    """
    response = state.get("final_response", "")
    recommendations = state.get("recommendations", [])

    # 如果没有推荐，生成默认回复
    if not response and not recommendations:
        response = "抱歉，未找到符合条件的商品。"

    return {"final_response": response}


# ---- Helper Functions ----


def _detect_currency(query: str) -> str | None:
    """检测用户使用的货币"""
    if "¥" in query or "人民币" in query or "元" in query or "CNY" in query.upper():
        return "CNY"
    if "£" in query or "英镑" in query:
        return "GBP"
    if "€" in query or "欧元" in query:
        return "EUR"
    if "$" in query or "美元" in query:
        return "USD"
    return None


def _extract_budget(query: str) -> float | None:
    """从查询中提取预算金额"""
    # 匹配预算模式: ¥3000, $500, 3000元, 预算: 3000 等
    patterns = [
        r"[¥$£€]\s*(\d+(?:\.\d+)?)",
        r"(\d+(?:\.\d+)?)\s*(?:元|人民币)",
        r"预算\s*[：:]\s*(\d+(?:\.\d+)?)",
        r"价位?\s*[：:]\s*(\d+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, query)
        if match:
            return float(match.group(1))
    return None


def _rank_products(
    candidates: list[dict],
    prices: list[dict],
    reviews: list[dict],
) -> list[Recommendation]:
    """
    根据价格和评论综合评分排序商品。

    Args:
        candidates: 候选商品列表
        prices: 价格信息列表
        reviews: 评论分析列表

    Returns:
        推荐列表 (按排名排序)
    """
    scored_products: list[tuple[int, int, Recommendation]] = []

    for i, product in enumerate(candidates):
        # 匹配价格信息
        price_info = next(
            (
                p
                for p in prices
                if p.get("title") == product.get("title")
                or p.get("product_sku") == product.get("product_sku")
            ),
            None,
        )

        # 匹配评论信息
        review_info = next(
            (
                r
                for r in reviews
                if r.get("product_sku") == product.get("product_sku")
            ),
            None,
        )

        # 综合评分逻辑 (简化版)
        score = 0
        if price_info:
            score += 1
        if review_info:
            sentiment = review_info.get("sentiment", "neutral")
            if sentiment == "positive":
                score += 2
            elif sentiment == "neutral":
                score += 1

        scored_products.append((
            score,
            i,
            {
                "rank": i + 1,
                "product": product,
                "recommendation_reason": _generate_reason(price_info, review_info),
                "price_range": _format_price(price_info),
                "best_platform": price_info.get("platform", "未知") if price_info else "未知",
                "purchase_link": price_info.get("url", product.get("url", "")) if price_info else "",
            },
        ))

    # 按评分降序排序；同分时保持原搜索顺序稳定
    scored_products.sort(key=lambda item: (-item[0], item[1]))

    ranked: list[Recommendation] = []
    for rank, (_, _, recommendation) in enumerate(scored_products[:3], start=1):
        recommendation["rank"] = rank
        ranked.append(recommendation)

    return ranked


def _generate_reason(price_info: dict | None, review_info: dict | None) -> str:
    """生成推荐理由"""
    reasons = []

    if price_info:
        reasons.append(f"价格: {price_info.get('price', {}).get('amount', '待查询')}")

    if review_info:
        sentiment = review_info.get("sentiment", "neutral")
        if sentiment == "positive":
            reasons.append("用户评价正面")
        elif sentiment == "negative":
            reasons.append("存在负面评价，注意筛选")

    return "; ".join(reasons) if reasons else "综合比较后推荐"


def _format_price(price_info: dict | None) -> str:
    """格式化价格区间"""
    if not price_info:
        return "待查询"

    price = price_info.get("price", {})
    amount = price.get("amount")
    currency = price.get("currency", "USD")

    if amount:
        return f"{currency} {amount}"
    return "待查询"


def _generate_report(
    recommendations: list[Recommendation],
    currency: str,
) -> str:
    """生成推荐报告"""
    if not recommendations:
        return "抱歉，未找到符合条件的商品。"

    lines = ["## 购物推荐\n"]

    for rec in recommendations:
        product = rec.get("product", {})
        lines.append(f"### {rec.get('rank', '')}. {product.get('title', '未知商品')}")
        lines.append(f"- **推荐理由**: {rec.get('recommendation_reason', '综合比较后推荐')}")
        lines.append(f"- **价格**: {rec.get('price_range', '待查询')}")
        lines.append(f"- **平台**: {rec.get('best_platform', '未知')}")

        link = rec.get("purchase_link", "")
        if link:
            lines.append(f"- **购买链接**: {link}")

        lines.append("")

    # 添加注意事项
    lines.append("---")
    lines.append("**温馨提示**: 请在购买前核实商品信息和价格，价格可能随时变动。")

    return "\n".join(lines)
