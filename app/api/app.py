import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as task_router
from app.core.config import get_config
from app.core.task_manager import get_task_manager

logger = logging.getLogger(__name__)


async def create_app(config_dir: Path | str = Path("config"), environment: str | None = None) -> FastAPI:
    """创建并配置FastAPI应用程序。
    
    Args:
        config_dir: 配置文件目录
        environment: 环境名称，用于加载特定环境的配置
        
    Returns:
        配置好的FastAPI应用实例
    """

    
    # 获取配置
    config = get_config()
    
    # 创建FastAPI应用
    app = FastAPI(
        title=config.api.title,
        description=config.api.description,
        version=config.api.version,
        docs_url=f"{config.api.prefix}/docs",
        redoc_url=f"{config.api.prefix}/redoc",
        openapi_url=f"{config.api.prefix}/openapi.json"
    )
    
    app.include_router(task_router, prefix=config.api.prefix)
    
    # 配置启动和关闭事件
    @app.on_event("startup")
    async def startup_event() -> None:
        """应用启动时初始化服务。"""
        logger.info("应用程序启动中...")
        
        # 启动定期任务清理
        task_manager = get_task_manager()
        await task_manager.start_periodic_cleanup()
        
        logger.info("应用程序启动完成")
    
    return app 