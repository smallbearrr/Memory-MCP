"""
MCP Memory Server - Main Entry Point

This module implements a Model Context Protocol (MCP) server for memory management.
It provides endpoints for saving and querying memories for AI agents.
"""

import asyncio
import logging
import sys
from typing import Dict, Any, Optional
import json

# MCP imports (假设使用标准MCP库)
# from mcp import Server, RequestContext
# from mcp.types import Tool, TextContent

from .models.memory import (
    SaveMemoryRequest, 
    QueryMemoryRequest, 
    SaveMemoryResponse,
    QueryMemoryResponse,
    APIError
)
from .storage.memory_storage import MemoryStorageInterface, create_storage
from .handlers.save_memory import save_memory_endpoint
from .handlers.query_memory import query_memory_endpoint

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPMemoryServer:
    """MCP Memory服务器"""
    
    def __init__(self, storage: Optional[MemoryStorageInterface] = None):
        """
        初始化MCP Memory服务器
        
        Args:
            storage: 存储接口，如果为None则使用默认存储（通过环境变量配置）
        """
        if storage is not None:
            self.storage = storage
        else:
            # 使用工厂函数根据环境变量创建存储
            self.storage = create_storage()
            
        logger.info("MCP Memory Server initialized")
    
    async def handle_save_memory(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理保存记忆请求
        
        Args:
            request_data: 请求数据
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        logger.info("Handling save memory request")
        
        try:
            result = await save_memory_endpoint(request_data, self.storage)
            
            if "error" in result:
                logger.warning(f"Save memory failed: {result['error']}")
            else:
                logger.info(f"Memory saved successfully with context_id: {result.get('context_id')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in save_memory: {str(e)}")
            return {
                "error": "internal_error",
                "message": "内部服务器错误",
                "details": {"exception": str(e)}
            }
    
    async def handle_query_memory(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理查询记忆请求
        
        Args:
            request_data: 请求数据
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        logger.info("Handling query memory request")
        
        try:
            result = await query_memory_endpoint(request_data, self.storage)
            
            if "error" in result:
                logger.warning(f"Query memory failed: {result['error']}")
            else:
                memories_count = len(result.get('memories', []))
                logger.info(f"Query completed successfully, returned {memories_count} memories")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error in query_memory: {str(e)}")
            return {
                "error": "internal_error",
                "message": "内部服务器错误",
                "details": {"exception": str(e)}
            }


# 简化的MCP工具定义
MCP_TOOLS = [
    {
        "name": "save_memory",
        "description": "保存记忆到存储系统",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "记忆内容文本"
                },
                "memory_type": {
                    "type": "string",
                    "enum": ["conversation", "experience", "knowledge", "context"],
                    "description": "记忆类型"
                },
                "importance": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "重要性级别"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "标签列表"
                },
                "related_task_id": {
                    "type": "integer",
                    "description": "关联任务ID"
                }
            },
            "required": ["content", "memory_type", "importance"]
        }
    },
    {
        "name": "query_memory",
        "description": "查询记忆",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search_text": {
                    "type": "string",
                    "description": "搜索文本"
                },
                "memory_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "记忆类型过滤"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 10,
                    "description": "返回数量限制"
                },
                "min_similarity": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.5,
                    "description": "最小相似度阈值"
                }
            },
            "required": ["search_text"]
        }
    }
]


async def main():
    """主函数"""
    
    # 创建服务器实例
    server = MCPMemoryServer()
    
    logger.info("MCP Memory Server starting...")
    
    # 临时测试
    print("MCP Memory Server Framework Initialized")
    print("Available tools:")
    for tool in MCP_TOOLS:
        print(f"  - {tool['name']}: {tool['description']}")
    
    print("\nServer is ready to handle MCP requests...")
    print("Note: This is a framework implementation. Integrate with actual MCP server library.")


if __name__ == "__main__":
    """直接运行时的入口点"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)