"""SharedState TypedDict for StateGraph nodes."""
from typing import TypedDict, Any, NotRequired
from langchain_core.messages import BaseMessage


class SearchResult(TypedDict):
    """Search results from product search."""
    query: str
    results: list[dict]  # Product list
    total: int


class PriceInfo(TypedDict):
    """Price information for a product."""
    product_sku: str
    platform: str
    price: dict  # Price details
    title: str
    url: str


class ReviewAnalysis(TypedDict):
    """Review analysis result for a product."""
    product_sku: str
    platform: str
    sentiment: str
    pros: list[str]
    cons: list[str]
    summary: str


class Recommendation(TypedDict):
    """Product recommendation."""
    rank: int
    product: dict
    recommendation_reason: str
    price_range: str
    best_platform: str
    purchase_link: str


class WorkflowStep(TypedDict):
    """Workflow execution step."""
    node: str
    status: str  # "pending", "running", "completed", "error"
    input_data: NotRequired[dict]
    output_data: NotRequired[dict]
    error: NotRequired[str]


class SharedState(TypedDict):
    """
    Shared state流转于 StateGraph 各节点之间.

    Design principle: 使用新对象更新状态，保持不可变性。
    每个节点返回 dict 更新部分字段，而非直接修改状态。

    Fields:
        user_query: 用户原始查询
        session_id: 会话 ID，用于记忆隔离
        messages: 消息历史 (BaseMessage 列表)

        search_results: 搜索结果
        candidate_products: 候选商品列表

        price_info: 价格信息列表
        review_analyses: 评论分析列表
        currency_result: 货币转换结果

        recommendations: 推荐列表
        final_response: 最终回复

        workflow_status: 工作流状态 (success/error/pending/running)
        error_message: 错误信息
        steps: 工作流执行步骤列表
    """
    # ---- 输入/会话 ----
    user_query: str
    session_id: str
    messages: list[BaseMessage]

    # ---- 搜索阶段 ----
    search_results: NotRequired[SearchResult]
    candidate_products: NotRequired[list[dict]]

    # ---- 比价阶段 ----
    price_info: NotRequired[list[PriceInfo]]

    # ---- 评论分析阶段 ----
    review_analyses: NotRequired[list[ReviewAnalysis]]

    # ---- 货币转换阶段 ----
    currency_result: NotRequired[dict]

    # ---- 推荐阶段 ----
    recommendations: NotRequired[list[Recommendation]]

    # ---- 输出 ----
    final_response: NotRequired[str]
    workflow_status: NotRequired[str]  # "pending", "running", "success", "error"
    error_message: NotRequired[str]

    # ---- 调试/追踪 ----
    steps: NotRequired[list[WorkflowStep]]
