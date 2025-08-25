# Memory-MCP

一个基于 Model Context Protocol (MCP) 的智能记忆管理系统，为 AI 代理提供强大的记忆存储和检索能力。

## API 说明

### 1. 保存记忆 API

**端点**: `POST /mcp/save_memory`

**请求格式**:
```json
{
    "content": "记忆内容",
    "memory_type": "experience|knowledge|conversation|context",
    "importance": "critical|high|medium|low|temporary",
    "tags": ["标签1", "标签2"],
    "related_task_id": "可选的任务ID"
}
```

**响应格式**:
```json
{
    "context_id": "生成的上下文ID",
    "task_id": ,
    "memory_type": "experience",
    "content": "记忆内容",
    "created_at": "2025-01-01T00:00:00.000Z",
    "embedding_generated": true
}
```

### 2. 查询记忆 API

**端点**: `POST /mcp/query_memory`

**请求格式**:
```json
{
    "search_text": "搜索关键词",
    "memory_types": ["experience", "knowledge"],
    "limit": 10,
    "min_similarity": 0.3
}
```

**响应格式**:
```json
{
    "memories": [
        {
            "task_id": ,
            "memory_type": "experience",
            "content": "记忆内容",
            "similarity": 0.85,
            "created_at": "2025-01-01T00:00:00.000Z",
            "meta": {
                "importance": "high",
                "tags": ["e-coli", "isolation"],
                "agentic_keywords": "关键词提取",
                "agentic_context": "上下文分析"
            }
        }
    ],
    "total": 1
}
```

### 3. 其他 API 端点

#### 健康检查

**端点**: `GET /healthz`

#### 获取 MCP 工具列表

**端点**: `GET /mcp/tools`

## 使用流程

#### 1. 启动 MCP

HTTP API 访问。


```python
uvicorn.run(app, host="127.0.0.1", port=8000)
```

#### 2. 存储记忆

```python

payloads = [
    {
        "content": "The biofilm formation ability of Pseudomonas aeruginosa is significantly enhanced under hypoxic conditions",
        "memory_type": "experience",
        "importance": "high",
        "tags": ["biofilm", "pseudomonas", "anaerobic"],
        "related_task_id": 2003
    },
    {
        "content": "16S rRNA gene sequencing remains the gold standard for bacterial identification",
        "memory_type": "conversation",
        "importance": "medium",
        "tags": ["16s-rRNA", "bacterial-identification"],
        "related_task_id": 2004
    }
]

for i, payload in enumerate(payloads, 1):
        r = requests.post(f"{base_url}/mcp/save_memory", json=payload)
```

#### 3. 查询记忆

```python
query_payload = {
    "search_text": "CRISPR gene editing technology",
    "memory_types": ["knowledge", "conversation"],
    "limit": 10,
    "min_similarity": 0.4
}

r = requests.post(f"{base_url}/mcp/query_memory", json=query_payload)
```


## 替换其他记忆模型

Memory-MCP 系统设计为模块化架构，支持轻松替换不同的记忆存储后端。

### 实现自定义存储

**继承存储接口**

```python

class CustomMemoryStorage(MemoryStorageInterface):
    async def save_memory(self, request: SaveMemoryRequest) -> SaveMemoryResponse:
        pass
    
    async def query_memory(self, request: QueryMemoryRequest) -> QueryMemoryResponse:
        pass
```


## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 相关项目

- [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/pdf/2502.12110) - 论文链接
- [AgenticMemory Repository](https://github.com/WujiangXu/AgenticMemory) - 完整研究实现
