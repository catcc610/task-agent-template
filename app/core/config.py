"""
配置管理模块
"""
import os
from pathlib import Path
from typing import Dict, Any
import yaml
from pydantic import BaseModel, Field


class InferenceConfig(BaseModel):
    """推理服务配置"""
    max_concurrent_tasks: int = Field(default=5, description="最大并发任务数", gt=0)
    timeout_seconds: int = Field(default=60, description="任务超时时间(秒)", gt=0)
    task_retention_hours: int = Field(default=24, description="已完成任务保留时间(小时)", ge=0)
    max_tasks_count: int = Field(default=1000, description="最大保存任务数量", gt=0)


class AppConfig(BaseModel):
    """应用全局配置"""
    app_name: str = "task-agent"
    inference: InferenceConfig = Field(default_factory=InferenceConfig)


class ApiConfig(BaseModel):
    """API配置"""
    title: str = "Task Agent API"
    description: str = "异步任务代理API服务"
    version: str = "1.0.0"
    prefix: str = "/api/v1"


class Config(BaseModel):
    """应用程序配置"""
    app_name: str = "task-agent"
    api: ApiConfig = Field(default_factory=ApiConfig)
    inference: InferenceConfig = Field(default_factory=InferenceConfig)


def load_config_from_file(config_dir: Path, environment: str = "local") -> Dict[str, Any]:
    """从配置文件加载配置
    
    Args:
        config_dir: 配置文件目录
        environment: 环境名称
        
    Returns:
        配置字典
    """
    config_file = config_dir / f"{environment}.yaml"
    if not config_file.exists():
        return {}
    
    with open(config_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# 全局配置对象
global_config = None


def get_config() -> Config:
    """获取全局配置对象
    
    Returns:
        全局配置对象
    """
    global global_config
    if global_config is None:
        environment = os.environ.get("ENV", "local")
        config_dir = Path("config")
        config_data = load_config_from_file(config_dir, environment)
        global_config = Config(**config_data)
    return global_config 