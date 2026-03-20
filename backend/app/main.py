"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

# Configure logging - output to both file and console
log_dir = Path(__file__).resolve().parents[2] / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"api_{date.today()}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[2]
    project_root_str = str(project_root)
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.config import Config
from backend.app.api.routes.auth import router as auth_router
from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.health import router as health_router
from backend.app.api.routes.session import router as session_router
from backend.app.api.routes.users import router as users_router

app = FastAPI(title="Sales Agent Backend", version="1.0.0")
logger.info("[MAIN] Application starting...")


@app.middleware("http")
async def log_requests(request, call_next):
    """Log all incoming requests for debugging."""
    auth_header = request.headers.get("authorization", "NONE")
    logger.info(f"[HTTP] {request.method} {request.url.path} Authorization: {auth_header[:50] if auth_header != 'NONE' else 'NONE'}...")
    response = await call_next(request)
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(session_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")


def main() -> None:
    """Run the FastAPI app so this file can be executed directly."""
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
