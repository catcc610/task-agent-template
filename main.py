"""
任务代理应用入口点
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 导入组件
from app.api.routes import router
from app.core.config import get_config

# 创建FastAPI应用
app = FastAPI(
    title="Task Agent API",
    description="任务代理API",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加路由
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径处理
    
    Returns:
        欢迎信息和应用名称
    """
    config = get_config()
    return {
        "message": "欢迎使用任务代理API",
        "app_name": config.app_name
    }


def start_server(host="0.0.0.0", port=8000, dev_mode=True):
    """启动服务器
    
    Args:
        host: 监听主机
        port: 监听端口
        dev_mode: 是否为开发模式(启用热重载)
    """
    if dev_mode:
        # 开发模式：使用reload=True需要字符串引用
        uvicorn.run(
            "main:app",  # 模块路径
            host=host,
            port=port,
            reload=True
        )
    else:
        # 生产模式：直接使用app对象
        uvicorn.run(
            app,  # 直接引用app对象
            host=host,
            port=port,
            reload=False
        )


if __name__ == "__main__":
    # 从环境变量获取配置
    port = int(os.getenv("PORT", "8000"))
    dev_mode = os.getenv("DEV_MODE", "true").lower() in ("true", "1", "yes")
    
    # 启动服务器
    start_server(port=port, dev_mode=dev_mode) 