# Memory-MCP

基于 Model Context Protocol (MCP) 的智能记忆管理系统，为 AI Agent提供强大的记忆存储和检索能力。

## 环境配置

设置 LLM API Key
```
export GLM_API_KEY=<your_api_key>

export MEM0_API_KEY=<your_api_key>
```
Memory System:
默认MOCK测试模式
```
export MEMORY_STORAGE="mock"|"amem"|"mem0"
```

## API 说明

### 1. 保存记忆 API

**端点**: `POST /mcp/save_memory`

**请求格式**:
```json
{
    "content": "记忆内容",
}
```

**响应格式**:
```json
{
    "content": "记忆内容",
}
```

### 2. 查询记忆 API

**端点**: `POST /mcp/query_memory`

**请求格式**:
```json
{
    "search_text": "搜索关键词",
}
```

**响应格式**:
```json
{
    "memories": [
        {
            "content": "记忆内容",
        }
    ],
    "total":
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
uvicorn.run("src.http_server:app", host="127.0.0.1", port=8000)
```

#### 2. 存储记忆

```python

payloads = [
    {
        "content": "context 1",
    },
    {
        "content": "context 2",
    }
]

for i, payload in enumerate(payloads, 1):
        r = requests.post(f"{base_url}/mcp/save_memory", json=payload)
```

#### 3. 查询记忆

```python
query_payload = {
    "search_text": "CRISPR gene editing technology",
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
