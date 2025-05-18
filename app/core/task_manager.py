"""
任务管理器模块 - 负责任务的创建、执行和状态管理
"""
from typing import Dict, Any, List, Optional
import asyncio
import uuid
from uuid import UUID
import time
import logging
from datetime import datetime, timedelta
from app.core.config import get_config

logger = logging.getLogger(__name__)


class Task:
    """任务类，表示一个异步执行的任务"""
    
    def __init__(self, task_id: str, payload: Dict[str, Any]):
        """初始化任务
        
        Args:
            task_id: 任务唯一标识符
            payload: 任务负载数据
        """
        self.task_id: str = task_id
        self.id = task_id  # 兼容旧代码
        self.payload: Dict[str, Any] = payload
        self.type = payload.get("type", "inference")  # 兼容旧代码
        self.status: str = "pending"  # pending, running, completed, failed
        self.result: Dict[str, Any] | None = None
        self.created_at: datetime = datetime.now()
        self.updated_at: datetime = datetime.now()  # 兼容旧代码
        self.started_at: datetime | None = None
        self.completed_at: datetime | None = None
        self.error: str | None = None
        self.progress: float = 0.0  # 兼容旧代码


class TaskManager:
    """任务管理器 - 负责管理并发任务执行"""
    
    def __init__(self):
        """初始化任务管理器"""
        self.tasks: Dict[str, Task] = {}
        self.config = get_config()
        self.semaphore = asyncio.Semaphore(
            self.config.inference.max_concurrent_tasks
        )
        self._start_time = time.time()
        self._completed_count = 0
        self._failed_count = 0
        self._cleanup_task = None
    
    async def start_periodic_cleanup(self) -> None:
        """启动定期清理任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            logger.info("已启动定期任务清理")
    
    async def _periodic_cleanup(self) -> None:
        """定期清理过期任务"""
        while True:
            try:
                await self.cleanup_expired_tasks()
            except Exception as e:
                logger.error(f"清理过期任务时出错: {str(e)}")
            
            # 每小时清理一次
            await asyncio.sleep(3600)
    
    async def cleanup_expired_tasks(self) -> int:
        """清理过期的任务
        
        Returns:
            清理的任务数量
        """
        # 如果保留时间为0，表示不清理
        retention_hours = self.config.inference.task_retention_hours
        if retention_hours <= 0:
            return 0
            
        retention_limit = datetime.now() - timedelta(hours=retention_hours)
        expired_task_ids = []
        
        # 找出所有已完成或失败且超过保留期的任务
        for task_id, task in self.tasks.items():
            if task.status in ["completed", "failed", "cancelled"]:
                if task.completed_at and task.completed_at < retention_limit:
                    expired_task_ids.append(task_id)
        
        # 删除过期任务
        for task_id in expired_task_ids:
            del self.tasks[task_id]
        
        if expired_task_ids:
            logger.info(f"已清理 {len(expired_task_ids)} 个过期任务")
        
        # 检查是否超过最大任务数
        max_tasks = self.config.inference.max_tasks_count
        if len(self.tasks) > max_tasks:
            # 按创建时间排序，保留较新的任务
            sorted_tasks = sorted(
                [(task_id, task) for task_id, task in self.tasks.items() 
                 if task.status in ["completed", "failed", "cancelled"]],
                key=lambda x: x[1].created_at
            )
            
            # 计算需要删除的数量
            to_remove = len(self.tasks) - max_tasks
            if to_remove > 0:
                for task_id, _ in sorted_tasks[:to_remove]:
                    del self.tasks[task_id]
                logger.info(f"已删除 {to_remove} 个任务以满足最大任务数限制")
        
        return len(expired_task_ids)
    
    async def create_task(self, payload: Dict[str, Any]) -> Task:
        """创建新任务
        
        Args:
            payload: 任务负载数据
            
        Returns:
            新创建的任务对象
        """
        # 创建任务前检查是否需要清理
        await self.cleanup_expired_tasks()
        
        task_id = str(uuid.uuid4())
        task = Task(task_id, payload)
        self.tasks[task_id] = task
        return task
    
    async def get_task(self, task_id: str) -> Task | None:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如不存在返回None
        """
        return self.tasks.get(task_id)
    
    async def run_task(self, task: Task) -> None:
        """执行任务
        
        Args:
            task: 要执行的任务对象
        """
        task.status = "running"
        task.started_at = datetime.now()
        task.updated_at = datetime.now()  # 兼容旧代码
        
        async with self.semaphore:
            try:
                # 这里是任务执行逻辑
                # 为了演示，我们模拟一个处理时间
                await asyncio.sleep(2)
                
                # 假设任务处理成功
                task.result = {
                    "output": f"Processed input: {task.payload.get('input', '')}"
                }
                task.status = "completed"
                task.progress = 1.0  # 兼容旧代码
                self._completed_count += 1
            except Exception as e:
                task.error = str(e)
                task.status = "failed"
                task.result = {"error": str(e)}
                self._failed_count += 1
            finally:
                task.completed_at = datetime.now()
                task.updated_at = datetime.now()  # 兼容旧代码
    
    async def get_all_tasks(self) -> List[Task]:
        """获取所有任务列表
        
        Returns:
            所有任务对象列表
        """
        return list(self.tasks.values())

    # 兼容方法 - 为CLI和其他模块提供兼容性
    
    async def list_tasks(self, status: Optional[Any] = None, task_type: Optional[str] = None) -> List[Task]:
        """列出任务，兼容旧方法
        
        Args:
            status: 任务状态过滤
            task_type: 任务类型过滤
            
        Returns:
            任务列表
        """
        tasks = await self.get_all_tasks()
        
        if status:
            status_str = str(status).lower()
            tasks = [task for task in tasks if str(task.status).lower() == status_str]
        
        if task_type:
            tasks = [task for task in tasks if task.type == task_type]
        
        return tasks
    
    async def cancel_task(self, task_id: str) -> None:
        """取消任务，兼容旧方法
        
        Args:
            task_id: 任务ID
        """
        task = await self.get_task(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        task.status = "cancelled"
        task.updated_at = datetime.now()
        
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标，兼容旧方法
        
        Returns:
            指标字典
        """
        return {
            "task_count": len(self.tasks),
            "running_tasks": len([t for t in self.tasks.values() if t.status == "running"]),
            "pending_tasks": len([t for t in self.tasks.values() if t.status == "pending"]),
            "completed_tasks": self._completed_count,
            "failed_tasks": self._failed_count,
            "uptime": time.time() - self._start_time
        }


# 全局任务管理器实例
global_task_manager = None


def get_task_manager() -> TaskManager:
    """获取全局任务管理器实例
    
    Returns:
        全局任务管理器实例
    """
    global global_task_manager
    if global_task_manager is None:
        global_task_manager = TaskManager()
    return global_task_manager 