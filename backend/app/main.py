"""Colony AI / 智衍 应用入口，配置 FastAPI 应用和中间件。

Usage:
  python -m app.main serve         # Start web server (default)
  python -m app.main cli           # Run in CLI mode (interactive/headless)
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from app.routers import modeling_router, ws_router, common_router, files_router
from app.utils.log_util import logger
from fastapi.staticfiles import StaticFiles
from app.utils.cli import get_ascii_banner, center_cli_str


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(get_ascii_banner())
    print(center_cli_str("GitHub: https://github.com/jihe520/MathModelAgent (Colony AI fork)"))
    logger.info("Starting Colony AI")

    PROJECT_FOLDER = "./project"
    os.makedirs(PROJECT_FOLDER, exist_ok=True)

    yield
    logger.info("Stopping Colony AI")


app = FastAPI(
    title="Colony AI (智衍)",
    description="Colony AI - Multi-Agent Collaboration Platform",
    version="0.3.0",
    lifespan=lifespan,
)

app.include_router(modeling_router.router)
app.include_router(ws_router.router)
app.include_router(common_router.router)
app.include_router(files_router.router)


# 跨域 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],  # 暴露所有响应头
)

app.mount(
    "/static",  # 这是访问时的前缀
    StaticFiles(directory="project/work_dir"),  # 这是本地文件夹路径
    name="static",
)


def main():
    """Entry point for CLI commands."""
    import asyncio
    from app.utils.cli import cli_main
    asyncio.run(cli_main(sys.argv[1:] if len(sys.argv) > 1 else ["serve"]))


if __name__ == "__main__":
    main()
