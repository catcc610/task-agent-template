"""
API路由定义
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.api.schemas import (
    InferenceRequest, 
    InferenceResponse, 
    TaskStatusResponse,
    HealthResponse
)
from app.core.task_manager import get_task_manager
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/task/inference", response_model=InferenceResponse)
async def create_inference_task(
    request: InferenceRequest, 
    background_tasks: BackgroundTasks
):
    """创建推理任务
    
    Args:
        request: 推理请求
        background_tasks: 后台任务
        
    Returns:
        任务创建响应，包含任务ID和状态
    """
    logger.info(f"收到推理任务请求: {request.input[:50]}...")
    
    task_manager = get_task_manager()
    task = await task_manager.create_task(request.model_dump())
    
    # 将任务放入后台执行
    background_tasks.add_task(task_manager.run_task, task)
    
    logger.info(f"已创建任务: {task.task_id}, 状态: {task.status}")
    return InferenceResponse(
        task_id=task.task_id,
        status=task.status
    )


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
        
    Raises:
        HTTPException: 当任务不存在时
    """
    logger.info(f"查询任务状态: {task_id}")
    task = await get_task_manager().get_task(task_id)
    if not task:
        logger.warning(f"任务不存在: {task_id}")
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    logger.info(f"获取到任务: {task_id}, 状态: {task.status}")
    return TaskStatusResponse(
        task_id=task.task_id,
        status=task.status,
        result=task.result,
        created_at=task.created_at.isoformat() if task.created_at else None,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        error=task.error
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点
    
    Returns:
        健康状态信息
    """
    logger.debug("收到健康检查请求")
    task_manager = get_task_manager()
    tasks = await task_manager.get_all_tasks()
    
    response = HealthResponse(
        status="healthy",
        version="1.0.0",
        tasks_count=len(tasks)
    )
    logger.debug(f"健康检查响应: {response.model_dump()}")
    return response 