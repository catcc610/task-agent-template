"""
任务代理应用入口点
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入日志配置
from app.utils.logger import configure_logging, get_logger

# 导入组件
from app.core.config import get_config
from app.api.routes import router
from app.core.task_manager import get_task_manager

# 配置日志
configure_logging()
logger = get_logger(__name__)

# 获取配置
config = get_config()

# 创建FastAPI应用 (同步操作)
app = FastAPI(
    title=config.api.title,
    description=config.api.description,
    version=config.api.version,
    docs_url=f"{config.api.prefix}/docs",
    redoc_url=f"{config.api.prefix}/redoc",
    openapi_url=f"{config.api.prefix}/openapi.json"
)

# 添加路由
app.include_router(router, prefix=config.api.prefix)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径处理
    
    Returns:
        欢迎信息和应用名称
    """
    return {
        "message": "欢迎使用任务代理API",
        "app_name": config.app_name
    }

# 设置启动事件 - 用于异步初始化操作
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的异步操作"""
    logger.info("应用程序启动中...")
    
    # 启动任务清理
    task_manager = get_task_manager()
    await task_manager.start_periodic_cleanup()
    
    logger.info("应用程序启动完成")

# 设置关闭事件 - 用于优雅地清理资源
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的清理操作"""
    logger.info("应用程序关闭中...")
    
    # 获取任务管理器
    task_manager = get_task_manager()
    
    # 如果有清理任务在运行，应该取消它
    if hasattr(task_manager, "_cleanup_task") and task_manager._cleanup_task:
        if not task_manager._cleanup_task.done():
            task_manager._cleanup_task.cancel()
            try:
                # 等待任务取消完成
                await task_manager._cleanup_task
            except:
                # 忽略取消异常
                pass
    
    # 最后一次清理任务
    try:
        await task_manager.cleanup_expired_tasks()
    except Exception as e:
        logger.error(f"最终任务清理失败: {str(e)}")
    
    logger.info("应用程序关闭完成")


def start_server(host="0.0.0.0", port=8000, dev_mode=True):
    """启动服务器
    
    Args:
        host: 监听主机
        port: 监听端口
        dev_mode: 是否为开发模式(启用热重载)
    """
    log_level = config.logging.level.lower()
    
    if dev_mode:
        # 开发模式：使用reload=True需要字符串引用
        logger.info(f"以开发模式启动服务，监听 {host}:{port}")
        uvicorn.run(
            "main:app",  # 模块路径
            host=host,
            port=port,
            reload=True,
            log_level=log_level
        )
    else:
        # 生产模式：直接使用app实例
        logger.info(f"以生产模式启动服务，监听 {host}:{port}")
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,
            log_level=log_level
        )


if __name__ == "__main__":
    # 从环境变量获取配置
    port = int(os.getenv("PORT", "8000"))
    dev_mode = os.getenv("DEV_MODE", "true").lower() in ("true", "1", "yes")
    
    # 启动服务器
    start_server(port=port, dev_mode=dev_mode) 