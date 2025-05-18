"""
任务管理器模块 - 负责任务的创建、执行和状态管理
"""
from typing import Dict, Any, List, Optional
import asyncio
import uuid
from uuid import UUID
import time
from datetime import datetime
from app.core.config import get_config


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
        self.semaphore = asyncio.Semaphore(
            get_config().inference.max_concurrent_tasks
        )
        self._start_time = time.time()
        self._completed_count = 0
        self._failed_count = 0
    
    async def create_task(self, payload: Dict[str, Any]) -> Task:
        """创建新任务
        
        Args:
            payload: 任务负载数据
            
        Returns:
            新创建的任务对象
        """
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