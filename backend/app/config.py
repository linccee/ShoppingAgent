import os

from dotenv import load_dotenv

load_dotenv()


class Config:

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
    COMPRESSION_THRESHOLD = 3000        # 超过此 token 数时触发压缩
    RECENT_TURNS_TO_KEEP = 2            # 保留最近2轮完整对话

    MONGO_URI = os.getenv("MONGO_URI")

    # ── 调试配置 ──
    VERBOSE = True          # 开启后可在终端看到Agent思考过程

    # ── 货币转换API配置 ──
    EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

    # ── JWT配置 ──
    JWT_SECRET = os.getenv("JWT_SECRET")
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS = 7

    # ── 密码策略 ──
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_LETTER = True

    # ── CORS配置 ──
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
