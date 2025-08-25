# http_server.py
"""
HTTP proxy for MCP Memory Server

Expose MCP tools over HTTP:
- POST /mcp/save_memory
- POST /mcp/query_memory
- GET  /mcp/tools
- GET  /healthz
"""

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 你的现有代码模块（保持原有结构即可）
from .main import MCPMemoryServer, MCP_TOOLS   # 如果你的 MCP_TOOLS 在 main 内
from .storage.memory_storage import MemoryStorageInterface, create_storage
from .models.memory import (
    SaveMemoryRequest,
    SaveMemoryResponse,
    QueryMemoryRequest,
    QueryMemoryResponse,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="MCP Memory HTTP Proxy", version="1.0.0")

# 可选：允许跨域（前端调试时很方便）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请收紧
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- 依赖注入：Server 单例 ----------

class ServerHolder:
    server: Optional[MCPMemoryServer] = None

holder = ServerHolder()

@app.on_event("startup")
async def on_startup():
    # 使用你的工厂方法自动选择存储（环境变量控制）
    storage = create_storage()
    holder.server = MCPMemoryServer(storage=storage)
    logger.info("MCP Memory HTTP Proxy started.")

def get_server() -> MCPMemoryServer:
    if holder.server is None:
        raise HTTPException(status_code=503, detail="Server not initialized")
    return holder.server

# ---------- 健康检查 & 工具发现 ----------

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/mcp/tools")
async def list_tools():
    # 直接返回你在代码里定义的 MCP_TOOLS
    return {"tools": MCP_TOOLS}

# ---------- MCP 工具：HTTP 代理 ----------

@app.post("/mcp/save_memory", response_model=dict)
async def http_save_memory(
    payload: SaveMemoryRequest,
    server: MCPMemoryServer = Depends(get_server),
):
    """
    通过 HTTP 调用 MCP 的 save_memory 工具
    请求体：SaveMemoryRequest（Pydantic 自动校验）
    返回：和原来 endpoint 返回的 dict 保持一致
    """
    # 注意：你的 handlers.save_memory_endpoint 接受 dict；这里转一下
    request_dict: Dict[str, Any] = payload.model_dump()
    result = await server.handle_save_memory(request_dict)
    # 统一错误返回
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result

@app.post("/mcp/query_memory", response_model=dict)
async def http_query_memory(
    payload: QueryMemoryRequest,
    server: MCPMemoryServer = Depends(get_server),
):
    """
    通过 HTTP 调用 MCP 的 query_memory 工具
    请求体：QueryMemoryRequest
    返回：和原来 endpoint 返回的 dict 保持一致
    """
    request_dict: Dict[str, Any] = payload.model_dump()
    result = await server.handle_query_memory(request_dict)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result)
    return result
