# 简化版任务代理 (Task Agent)

这是一个简化版的任务代理API实现，专注于核心功能，包括任务处理和健康状态检查。

## 核心功能

- 接收并异步处理推理任务
- 支持任务状态查询
- 健康检查接口
- 基于配置的并发任务控制
- 环境配置切换 (local/develop)

## 项目结构

```
.
├── app/
│   ├── api/
│   │   ├── schemas.py         # API请求和响应数据模型
│   │   └── routes.py          # API路由
│   ├── core/
│   │   ├── config.py          # 配置管理
│   │   └── task_manager.py    # 任务管理器
│   └── __init__.py            # 包初始化
├── config/
│   ├── local.yaml             # 本地环境配置
│   └── develop.yaml           # 开发环境配置
├── requirements.txt           # 项目依赖
└── main.py                    # 应用入口
```

## 如何使用

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行服务

```bash
# 本地环境 (默认)
python main.py

# 开发环境
ENV=develop python main.py

# 生产环境 (禁用热重载)
DEV_MODE=false python main.py
```

### API端点

- `POST /api/v1/task/inference`: 创建新推理任务
- `GET /api/v1/task/{task_id}`: 获取任务状态
- `GET /api/v1/health`: 健康检查

## API请求示例

### 创建推理任务

**请求：**

```bash
curl -X POST http://localhost:8000/api/v1/task/inference \
  -H "Content-Type: application/json" \
  -d '{
    "input": "这是一个测试输入",
    "options": {
      "model": "gpt-3.5-turbo",
      "temperature": 0.7
    }
  }'
```

**响应：**

```json
{
  "task_id": "3f2d8a9c-6e5b-4d1c-9a7f-8b3e5a4c2d6e",
  "status": "pending"
}
```

### 查询任务状态

**请求：**

```bash
curl http://localhost:8000/api/v1/task/3f2d8a9c-6e5b-4d1c-9a7f-8b3e5a4c2d6e
```

**响应：**

```json
{
  "task_id": "3f2d8a9c-6e5b-4d1c-9a7f-8b3e5a4c2d6e",
  "status": "completed",
  "result": {
    "output": "Processed input: 这是一个测试输入"
  },
  "created_at": "2023-10-24T08:15:30.123456",
  "started_at": "2023-10-24T08:15:30.234567",
  "completed_at": "2023-10-24T08:15:32.345678",
  "error": null
}
```

### 健康检查

**请求：**

```bash
curl http://localhost:8000/api/v1/health
```

**响应：**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "tasks_count": 5
}
```

## 配置管理

应用会根据`ENV`环境变量选择配置文件：

- `ENV=local` (默认): 使用`config/local.yaml`
- `ENV=develop`: 使用`config/develop.yaml`

### 配置项

- `app_name`: 应用名称
- `inference.max_concurrent_tasks`: 最大并发任务数
- `inference.timeout_seconds`: 任务超时时间
- `inference.task_retention_hours`: 已完成任务保留时间(小时)，设为0表示不清理
- `inference.max_tasks_count`: 最大保存任务数量

## 任务管理

### 任务清理机制

系统包含自动任务清理机制，防止内存泄漏和资源浪费：

1. 定期清理：系统每小时自动检查并清理过期任务
2. 创建任务时清理：每次创建新任务前会检查并清理过期任务
3. 清理规则：
   - 清理已完成/失败且超过保留期的任务
   - 如果任务总数超过最大限制，会按创建时间排序删除最早的已完成任务

可通过配置文件调整清理策略：
- `task_retention_hours`: 设置任务保留时间，0表示不清理
- `max_tasks_count`: 设置最大任务数量限制

## 开发说明

该实现采用了全局实例模式管理单例对象：


## 技术栈

- FastAPI: Web框架
- Pydantic: 数据验证和配置管理
- PyYAML: YAML配置解析
- Uvicorn: ASGI服务器 