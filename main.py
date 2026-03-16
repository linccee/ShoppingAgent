"""Streamlit frontend for the 镜澜导购 shopping assistant."""
import pathlib
import random
import streamlit as st

from agent.agent_core import create_shopping_agent, stream_agent
from agent.agent_core import _memory_saver  # noqa: F401 — imported to keep singleton alive
from ui.sidebar import render_sidebar
from ui.chat import render_welcome, render_timeline, render_history
from ui.stop_injection import inject_stop_button_js, remove_stop_button_js

# ── 页面配置 (必须在 Streamlit 启动之前) ────────────────────────────────
st.set_page_config(
    page_title="镜澜导购 · 智能选购助手",
    page_icon="🪞",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── 注入外部 CSS ───────────────────────────────────────────────────────
def _load_css(path: str) -> None:
    """Read a CSS file and inject it via st.markdown."""
    css_path = pathlib.Path(__file__).parent / path
    if css_path.exists():
        css_text = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css_text}</style>", unsafe_allow_html=True)


_load_css("assets/style.css")


# ── Session 状态初始化 ────────────────────────────────────────────────────────
from utils.db import get_or_create_session_id, load_session, save_session

if "session_id" not in st.session_state:
    st.session_state.session_id = get_or_create_session_id()
    
if "messages" not in st.session_state:
    session_data = load_session(st.session_state.session_id)
    st.session_state.messages = session_data.get("messages", [])

# Agent 全局只创建一次（MongoDBSaver 内部管理所有会话的历史）
if "agent" not in st.session_state or st.session_state.agent is None:
    with st.spinner("正在唤醒镜澜导购…"):
        st.session_state.agent = create_shopping_agent()

if "total_input_tokens" not in st.session_state:
    session_data = load_session(st.session_state.session_id)
    st.session_state.total_input_tokens = session_data.get("input_tokens", 0)

if "total_output_tokens" not in st.session_state:
    session_data = load_session(st.session_state.session_id)
    st.session_state.total_output_tokens = session_data.get("output_tokens", 0)

if "hero_art_variant" not in st.session_state:
    st.session_state.hero_art_variant = random.choice(["liquid-core", "floating-prisms"])


def _get_agent():
    """返回全局唯一的 Agent 实例（MongoDBSaver 负责记忆隔离）。"""
    if st.session_state.agent is None:
        st.session_state.agent = create_shopping_agent()
    return st.session_state.agent


# ── 侧边栏 ───────────────────────────────────────────────────────────────────
render_sidebar()


# ── 主聊天区域 ────────────────────────────────────────────────────────────
st.markdown(
    f"""
    <section class="ag-hero glass-panel">
      <div class="ag-hero-copy">
        <p class="ag-hero-kicker">MIRROR CURATION · 镜澜导购</p>
        <h1>把复杂购物决策，整理成一眼就能判断的答案。</h1>
        <p class="ag-hero-text">
          连接 Google Shopping、Amazon 与 eBay，帮你完成比价、评论归纳与购买建议，
          在一轮对话里得到更清晰的购买判断。
        </p>
        <div class="ag-hero-tags">
          <span>多平台比价</span>
          <span>评论洞察</span>
          <span>预算决策</span>
        </div>
      </div>
      <div class="ag-hero-aside">
        <div class="ag-hero-art ag-hero-art--{st.session_state.hero_art_variant}">
          <div class="ag-hero-art-shell">
            <span class="ag-hero-glow ag-hero-glow-a"></span>
            <span class="ag-hero-glow ag-hero-glow-b"></span>
            <span class="ag-hero-glow ag-hero-glow-c"></span>
            <span class="ag-prism ag-prism-a"></span>
            <span class="ag-prism ag-prism-b"></span>
            <span class="ag-prism ag-prism-c"></span>
            <span class="ag-hero-sheen"></span>
          </div>
          <div class="ag-hero-art-label">{'液态光核' if st.session_state.hero_art_variant == 'liquid-core' else '漂浮棱镜'}</div>
        </div>
        <p>为犹豫不决的购买时刻，提供更清晰的结论。</p>
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

# 回放现有的对话历史
if st.session_state.messages:
    render_history(st.session_state.messages)

example_input = None
if not st.session_state.messages:
    example_input = render_welcome()

# ── Chat Input ────────────────────────────────────────────────────────────────
user_input = st.chat_input("描述你的购买目标，例如：帮我挑一台预算 ¥3000 左右的降噪耳机")

if example_input:
    user_input = example_input

if user_input:

    # 1. 保存 + 立即显示用户消息
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    # 2. 提前在 session 中占位，保证被强制停止时也能保留片段
    agent_executor = _get_agent()
    steps: list[dict] = []

    assistant_msg = {"role": "assistant", "content": "", "steps": steps}
    st.session_state.messages.append(assistant_msg)

    with st.chat_message("assistant", avatar="🪞"):
        # timeline_box: 动态更新思考和工具调用
        timeline_box = st.empty()
        # text_box: 流式传输最终 LLM 字符串
        text_box = st.empty()

        import sys

        final_answer = ""
        
        # 注入自定义的 Stop 按钮覆盖在输入框上
        inject_stop_button_js()
        
        try:
            for kind, data in stream_agent(agent_executor, user_input, session_id=st.session_state.session_id):
                if kind == "token":
                    # Tool Calling 模式下，所有 token 直接就是最终回复，无需解析 Final Answer: 前缀
                    final_answer += data
                    assistant_msg["content"] = final_answer
                    text_box.markdown(final_answer + " ▋")

                    # 收到第一个 token 时，锁定时间线（工具调用已全部完成）
                    html_tl = render_timeline(steps, None, is_complete=True)
                    if html_tl:
                        timeline_box.markdown(html_tl, unsafe_allow_html=True)

                elif kind == "tool_start":
                    steps.append({"type": "tool", "tool": data["tool"], "input": data["input"], "output": ""})
                    html_tl = render_timeline(steps, None)
                    if html_tl:
                        timeline_box.markdown(html_tl, unsafe_allow_html=True)

                elif kind == "tool_end":
                    if steps and steps[-1]["type"] == "tool":
                        steps[-1]["output"] = data
                    html_tl = render_timeline(steps, None)
                    if html_tl:
                        timeline_box.markdown(html_tl, unsafe_allow_html=True)

                elif kind == "error":
                    final_answer += f"\n\n⚠️ 错误：{data}"
                    text_box.markdown(final_answer)
                    assistant_msg["content"] = final_answer

                elif kind == "token_usage":
                    st.session_state.total_input_tokens += data.get("input_tokens", 0)
                    st.session_state.total_output_tokens += data.get("output_tokens", 0)

        except Exception as exc:
            import traceback
            from streamlit.runtime.scriptrunner.script_runner import StopException
            if not isinstance(exc, StopException):
                traceback.print_exc(file=sys.stderr)
                final_answer += f"\n\n⚠️ Agent 执行出错：{exc}"
                text_box.markdown(final_answer)
                assistant_msg["content"] = final_answer
            else:
                raise exc # let StopException bubble up to halt script execution
        finally:
            # 无论正常结束还是被 StopException 打断，都执行最终渲染
            html_tl = render_timeline(steps, None, is_complete=True)
            if html_tl:
                timeline_box.markdown(html_tl, unsafe_allow_html=True)
            else:
                timeline_box.empty()

            # 去除光标光标并更新内容
            text_box.markdown(final_answer)
            assistant_msg["content"] = final_answer

            # 恢复输入框到空闲态，并移除自定义 Stop 按钮
            remove_stop_button_js()

            # 立即保存到 MongoDB，以免关闭/停止后丢失数据
            # 由于这里在 finally 中，点击 Stop 也能触发状态落库
            save_session(
                session_id=st.session_state.session_id,
                messages=st.session_state.messages,
                input_tokens=st.session_state.total_input_tokens,
                output_tokens=st.session_state.total_output_tokens
            )

    st.rerun()
else:
    # 不在生成状态时，确保移除 Stop 按钮恢复原状
    remove_stop_button_js()
