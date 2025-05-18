"""
API请求和响应数据模型
"""
from pydantic import BaseModel, Field
from typing import Dict, Any, List


class InferenceRequest(BaseModel):
    """推理请求模型"""
    input: str = Field(..., description="用户输入文本")
    options: Dict[str, Any] = Field(default_factory=dict, description="可选参数")


class InferenceResponse(BaseModel):
    """推理任务创建响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")


class TaskStatusResponse(BaseModel):
    """任务状态查询响应"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    result: Dict[str, Any] | None = Field(default=None, description="任务结果")
    created_at: str | None = Field(default=None, description="任务创建时间")
    started_at: str | None = Field(default=None, description="任务开始时间")
    completed_at: str | None = Field(default=None, description="任务完成时间")
    error: str | None = Field(default=None, description="错误信息")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(default="1.0.0", description="服务版本")
    tasks_count: int = Field(default=0, description="当前任务数量") 