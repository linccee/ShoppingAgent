import queue
import threading
import logging
import sys
from datetime import date

# ── Debug logger — writes to file so Streamlit stdout capture doesn't hide it ──
_log = logging.getLogger("agent_stream")
_log.setLevel(logging.DEBUG)

# 避免重复添加 handler
if not _log.handlers:
    # 控制台 handler — 输出到 stderr 避免被 Streamlit 捕获
    _ch = logging.StreamHandler(sys.stderr)
    _ch.setLevel(logging.DEBUG)
    _ch.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%H:%M:%S"))
    _log.addHandler(_ch)

# 文件 handler 目录 — 延迟初始化（在 _get_log_filehandler 中）
_log_dir: str | None = None


def _get_log_filehandler(session_id: str) -> logging.FileHandler:
    """为指定 session 创建或获取文件 handler，实现每个 session 一个日志文件。"""
    global _log_dir

    import os

    # 初始化日志目录
    if _log_dir is None:
        _log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        os.makedirs(_log_dir, exist_ok=True)

    today = date.today().strftime("%Y-%m-%d")
    # 文件名格式: {date}_{session_id}_agent_debug.log
    log_filename = f"{today}_{session_id}_agent_debug.log"
    log_path = os.path.join(_log_dir, log_filename)

    fh = logging.FileHandler(log_path, mode="a")
    fh.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%H:%M:%S"))
    return fh

from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.mongodb import MongoDBSaver
from agent.compressed_checkpointer import CompressedCheckpointer
from utils.db import client

from agent.prompt import SYSTEM_PROMPT
from config import Config


# ── 全局 checkpointer：CompressedCheckpointer 跨请求共享，持久化保存用户的对话记忆 ───────────────────
# 使用惰性初始化，避免导入模块时就建立 MongoDB 相关依赖。
_memory_saver: CompressedCheckpointer | None = None


def _get_memory_saver() -> CompressedCheckpointer:
    global _memory_saver
    if _memory_saver is None:
        _memory_saver = CompressedCheckpointer(MongoDBSaver(client))
    return _memory_saver


def create_shopping_agent():
    """
    创建并返回购物决策 Agent 实例（含 MongoDBSaver checkpointer）。
    应用启动时调用一次，实例存入 st.session_state 复用。

    记忆机制：
        使用 LangGraph 原生 MongoDBSaver，每次调用时通过
        config={"configurable": {"thread_id": <session_id>}} 隔离不同用户会话，
        LangGraph 自动将完整消息历史持久化到内存中。
    """
    # 1. 初始化 LLM
    llm = ChatOpenAI(
        model=Config.MODEL,
        api_key=Config.API_KEY,
        base_url=Config.BASE_URL,
        temperature=Config.TEMPERATURE,
        streaming=True,
        stream_usage=True
    )

    # 2. 注册工具列表
    from tools.currency_exchange_tool import currency_exchange
    from tools.price_tool import prices
    from tools.review_tool import analyze_reviews
    from tools.search_tool import search_products
    from tools.tavily_tool import tavily_search, tavily_extract

    tools = [search_products, prices, analyze_reviews, currency_exchange, tavily_search, tavily_extract]

    # 3. 创建 LangGraph ReAct Agent，注入 MongoDBSaver 作为持久化后端
    #    MongoDBSaver 会在每次调用后自动把完整 messages state 保存进 MongoDB 数据库，
    #    下次同一 thread_id 调用时自动从数据库恢复，完美支持跨重启记忆。
    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SystemMessage(content=SYSTEM_PROMPT),
        checkpointer=_get_memory_saver(),
    )

    return agent


def _make_config(session_id: str) -> dict:
    """构建 LangGraph 调用所需的 config，以 session_id 作为记忆隔离键。"""
    return {"configurable": {"thread_id": session_id}}


def run_agent(agent_executor, user_input: str, session_id: str = "default") -> dict:
    """
    执行 Agent，返回结果字典。

    返回格式：
        {
            'output': '最终推荐报告',
            'steps': [{'tool': ..., 'input': ..., 'output': ...}]
        }
    """
    result = agent_executor.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=_make_config(session_id),
    )

    # 从 LangGraph 返回的 messages 列表中提取步骤
    steps = []
    msgs = result.get("messages", [])

    for msg in msgs:
        if msg.type == "ai" and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tc_id = tc.get("id")
                tool_msg = next((m for m in msgs if m.type == "tool" and m.tool_call_id == tc_id), None)
                if tool_msg:
                    tool_content = str(tool_msg.content)
                    steps.append({
                        "tool": tc.get("name"),
                        "input": tc.get("args"),
                        "output": tool_content[:200] + '...' if len(tool_content) > 200 else tool_content
                    })

    final_output = msgs[-1].content if msgs else ""

    return {
        'output': final_output,
        'steps': steps
    }


class _QueueCallback(BaseCallbackHandler):
    """
    将 LLM 令牌和工具事件路由到线程安全的队列。

    流式策略：
        on_llm_new_token — 逐 token 流式传输（LangGraph 会通过 config callbacks 传播）。
        若无 token 到达，在 _run() 层有兜底逻辑从最终 state 中提取输出。
    """

    def __init__(self, q: queue.Queue, stop_event: threading.Event) -> None:
        super().__init__()
        self._q = q
        self._stop_event = stop_event
        self._got_tokens = False
        self._accumulated_output = ""  # 累积完整输出，用于日志记录
        self._token_buffer = []  # 缓冲区，用于控制台批量输出
        self._last_token_log_time = 0

    def _check_stop(self):
        if self._stop_event.is_set():
            raise Exception("Generation stopped by user")

    def _flush_token_buffer(self, force: bool = False):
        """将缓冲区中的 token 批量输出到控制台，减少日志频率。"""
        import time

        now = time.time()
        # 每秒或者强制刷新时输出
        if force or (self._token_buffer and now - self._last_token_log_time >= 1.0):
            if self._token_buffer:
                # 合并 token 并显示前几个和总长度
                buffered_text = "".join(self._token_buffer)
                preview = buffered_text[:50].replace("\n", "\\n")
                remaining = len(buffered_text) - 50
                if remaining > 0:
                    _log.debug(f"[TOKEN] {repr(preview)}... (+{remaining} chars)")
                else:
                    _log.debug(f"[TOKEN] {repr(preview)}")
                self._token_buffer = []
                self._last_token_log_time = now

    # ── 流式 token ────────────────────────────────────────────────────────────
    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self._check_stop()
        if token:
            self._got_tokens = True
            # 累积完整输出
            self._accumulated_output += token
            # 添加到缓冲区用于控制台批量显示
            self._token_buffer.append(token)
            self._flush_token_buffer()  # 定期刷新
            self._q.put(("token", token))

    def on_llm_end(self, response, **kwargs) -> None:
        """提取每次 LLM 调用后的 token 用量并推送到队列。"""
        self._flush_token_buffer(force=True)  # 强制刷新剩余 token

        # 将完整输出写入日志
        if self._accumulated_output:
            _log.debug(f"[FULL_OUTPUT] ----\n{self._accumulated_output}\n---- (END, {len(self._accumulated_output)} chars)")

        try:
            if response.generations and response.generations[0]:
                message = getattr(response.generations[0][0], "message", None)
                if message and hasattr(message, "usage_metadata") and message.usage_metadata:
                    self._q.put(("token_usage", message.usage_metadata))
        except Exception as e:
            _log.debug(f"[LLM_END] Error extracting usage: {e}")

    # ── 工具生命周期 ──────────────────────────────────────────────────────────
    def on_tool_start(
        self,
        serialized: dict,
        input_str: str,
        **kwargs,
    ) -> None:
        self._check_stop()
        tool_name = serialized.get("name", "unknown")
        _log.debug(f"[TOOL_START] {tool_name}")

        # 尝试将 JSON 字符串反序列化，输出更友好的 dict 给前端
        import json
        try:
            parsed_input = json.loads(input_str) if isinstance(input_str, str) else input_str
        except (json.JSONDecodeError, TypeError):
            parsed_input = input_str

        self._q.put(("tool_start", {
            "tool":   tool_name,
            "input":  parsed_input,
            "output": "",
        }))

    def on_tool_end(self, output: str, **kwargs) -> None:
        raw = str(output)
        _log.debug(f"[TOOL_END] len={len(raw)}")
        _log.debug(f"[TOOL_OUTPUT] ----\n{raw}\n---- (END, {len(raw)} chars)")
        self._q.put(("tool_end", raw[:300] + "…" if len(raw) > 300 else raw))


def stream_agent(agent_executor, user_input: str, session_id: str = "default"):
    """
    同步生成器，在后台线程中运行 LangGraph agent，产出 (kind, data) 事件元组。

    事件种类：
      "token"       str  — 一个 LLM 输出 token
      "tool_start"  dict — {tool, input, output}
      "tool_end"    str  — 截断的工具输出
      "token_usage" dict — token 用量统计
      "error"       str  — 异常消息
    """
    # 为当前 session 添加文件 handler（每个 session 一个日志文件）
    session_fh = _get_log_filehandler(session_id)
    _log.addHandler(session_fh)

    q: queue.Queue = queue.Queue()
    stop_event = threading.Event()
    cb = _QueueCallback(q, stop_event)

    def _run() -> None:
        _log.debug(f"[RUN] thread started, input={repr(user_input[:40])}, thread_id={session_id}")
        try:
            final_state = agent_executor.invoke(
                {"messages": [HumanMessage(content=user_input)]},
                config={
                    **_make_config(session_id),
                    "callbacks": [cb],
                },
            )
            _log.debug("[RUN] agent_executor call returned normally")

            # 兜底：如果 LangGraph 回调链未能触发 on_llm_new_token，
            # 直接从最终 state 中取出最后一条消息推送给前端
            if not cb._got_tokens:
                msgs = final_state.get("messages", [])
                if msgs:
                    output = msgs[-1].content
                    if output:
                        _log.debug("[RUN] Triggering fallback token emit")
                        # 记录完整输出到日志
                        _log.debug(f"[FULL_OUTPUT] ----\n{output}\n---- (END, {len(output)} chars)")
                        q.put(("token", output))
        except Exception as exc:
            if str(exc) == "Generation stopped by user":
                _log.debug("[RUN] Stopped by user")
            else:
                import traceback
                _log.debug(f"[RUN] EXCEPTION: {exc}")
                _log.debug(f"[RUN] Traceback: {traceback.format_exc()}")
                q.put(("error", str(exc)))
        finally:
            _log.debug("[RUN] thread finishing, putting sentinel")
            q.put(None)  # sentinel — always fires

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()

    try:
        while True:
            item = q.get()
            if item is None:
                break
            yield item
    except BaseException as e:
        _log.debug(f"[STREAM] Catching {type(e)}")
        stop_event.set()
        raise
    finally:
        stop_event.set()
        thread.join(timeout=1.0)
        # 移除当前 session 的文件 handler，避免日志混乱
        _log.removeHandler(session_fh)
        session_fh.close()


if __name__ == '__main__':
    agent = create_shopping_agent()
    print(run_agent(agent, "帮我推荐一款蓝牙耳机", session_id="test"))
