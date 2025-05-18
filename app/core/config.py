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


class AppConfig(BaseModel):
    """应用全局配置"""
    app_name: str = "task-agent"
    inference: InferenceConfig = Field(default_factory=InferenceConfig)


# 模块级单例
_config: AppConfig | None = None


def load_config() -> AppConfig:
    """加载配置文件
    
    根据环境变量ENV读取对应的配置文件，默认为local环境
    
    Returns:
        AppConfig: 应用配置对象
    """
    env = os.getenv("ENV", "local")
    config_path = f"config/{env}.yaml"
    
    try:
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)
        
        return AppConfig.model_validate(config_data)
    except FileNotFoundError:
        print(f"警告: 配置文件 {config_path} 不存在，使用默认配置")
        return AppConfig()
    except Exception as e:
        print(f"错误: 加载配置文件失败 - {str(e)}")
        return AppConfig()


def get_config() -> AppConfig:
    """获取全局配置单例
    
    如果配置未初始化，会先加载配置
    
    Returns:
        AppConfig: 应用配置对象
    """
    global _config 
    if _config is None:
        _config = load_config()
    return _config 