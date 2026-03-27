import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class Config:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    BACKEND_DIR = PROJECT_ROOT / "backend"

    # —— 主模型配置 ——
    API_KEY = os.getenv("LLM_API_KEY") or os.getenv("api_key")
    BASE_URL = os.getenv("LLM_BASE_URL") or os.getenv("base_url")
    MODEL = os.getenv("LLM_MODEL_ID") or os.getenv("QWEN_MODEL_ID")

    LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL_PATH")

    # —— 对话历史摘要LLM ——
    LITE_API_KEY = os.getenv("zhipu_api_key")
    LITE_BASE_URL = os.getenv("zhipu_base_url")
    LITE_MODEL = os.getenv("zhipu_module_id")

    # —— 搜索API配置 ——
    SERPAPI_KEY = os.getenv("SERPAPI_API_KEY")
    TAVILY_KEY = os.getenv("TAVILY_API_KEY")


    # ── Agent配置 ──
    MAX_ITERATIONS = 150     # Agent最大思考轮数，防止无限循环（购物流程：搜索1+价格4+评论4+汇总1≈10次）
    TEMPERATURE = 0.3       # 较低温度，保证输出稳定性
    MAX_TOKENS = 2048       # 单次输出最大token数
    MEMORY_TURNS = 10       # 记忆轮数

    # ── 记忆压缩配置 ──
    ENABLE_MEMORY_COMPRESSION = True   # 是否启用记忆压缩
    COMPRESSION_THRESHOLD = 1500       # 超过此 token 数时触发压缩
    RECENT_HISTORY_TOKEN_BUDGET = 1500 # 最近消息保留的 token 预算
    RECENT_TURNS_TO_KEEP = 2           # 兼容旧配置；当前 recent 保留策略已改为 token 预算
    COMPRESSION_MAX_RETRIES = 10                    # 最大重试次数
    COMPRESSION_INITIAL_RETRY_DELAY = 2.0         # 初始重试延迟(秒)
    COMPRESSION_MAX_RETRY_DELAY = 60.0            # 最大重试延迟(秒)
    COMPRESSION_RETRY_SCAN_INTERVAL = 10          # 重试扫描间隔(秒)
    COMPRESSION_TASK_MAX_AGE_HOURS = 24           # 失败任务最大保存时间(小时)
    COMPRESSION_DEGRADATION_COOLDOWN_MINUTES = 5  # 降级后恢复冷却时间(分钟)
    _raw_tiktoken_cache_dir = os.getenv("TIKTOKEN_CACHE_DIR", "")
    if _raw_tiktoken_cache_dir:
        _resolved_tiktoken_cache_dir = Path(_raw_tiktoken_cache_dir).expanduser()
        if not _resolved_tiktoken_cache_dir.is_absolute():
            _resolved_tiktoken_cache_dir = (PROJECT_ROOT / _resolved_tiktoken_cache_dir).resolve()
    else:
        _resolved_tiktoken_cache_dir = (BACKEND_DIR / "tiktoken-cache").resolve()
    TIKTOKEN_CACHE_DIR = str(_resolved_tiktoken_cache_dir)

    MONGO_URI = os.getenv("MONGO_URI")

    # ── 调试配置 ──
    VERBOSE = True          # 开启后可在终端看到Agent思考过程

    # ── 货币转换API配置 ──
    EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

    # ── JWT配置 ──
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS = 1

    # ── 密码策略 ──
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_LETTER = True

    # ── CORS配置 ──
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
