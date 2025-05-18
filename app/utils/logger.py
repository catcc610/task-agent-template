"""
日志配置模块 - 提供统一的日志配置和获取功能
"""
import os
import logging
import logging.handlers
from pathlib import Path
from typing import Dict, Optional, Union, Any

from app.core.config import get_config


# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}


def configure_logging() -> None:
    """配置全局日志设置
    
    从配置文件读取日志级别和格式，设置全局日志配置
    """
    config = get_config()
    log_config = config.logging
    
    # 获取日志级别
    log_level = LOG_LEVELS.get(log_config.level.upper(), logging.INFO)
    
    # 配置根日志器
    logging.basicConfig(
        level=log_level,
        format=log_config.format,
        handlers=[]
    )
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_config.format))
    
    # 如果启用了文件日志
    if log_config.file_enabled:
        # 确保日志目录存在
        log_dir = os.path.dirname(log_config.file_path)
        os.makedirs(log_dir, exist_ok=True)
        
        # 创建文件处理器 (按天滚动)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_config.file_path,
            when='midnight',
            backupCount=7,  # 保留7天的日志
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_config.format))
        
        # 添加到根日志器
        logging.getLogger().addHandler(file_handler)
    
    # 添加控制台处理器到根日志器
    logging.getLogger().addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器
    
    Args:
        name: 日志器名称，通常为模块名
        
    Returns:
        配置好的日志器实例
    """
    return logging.getLogger(name) 