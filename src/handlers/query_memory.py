"""
Query memory API handler
"""

import logging
from typing import Dict, Any

from ..models.memory import QueryMemoryRequest, QueryMemoryResponse, APIError
from ..storage.memory_storage import MemoryStorageInterface, StorageError

logger = logging.getLogger(__name__)


class QueryMemoryHandler:
    """查询记忆处理器"""
    
    def __init__(self, storage: MemoryStorageInterface):
        self.storage = storage
    
    async def handle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理查询记忆请求
        
        Args:
            request_data: 请求数据
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        try:
            # 验证请求数据
            request = QueryMemoryRequest(**request_data)
            
            # 查询记忆
            response = await self.storage.query_memory(request)
            
            logger.info(f"Successfully queried memories: found {response.total} matches, returning {len(response.memories)} results")
            
            # 返回查询结果
            try:
                # 尝试使用新版本 Pydantic 的方法，使用 mode='json' 来处理 datetime
                return response.model_dump(mode='json')
            except AttributeError:
                # 回退到旧版本 Pydantic 的方法
                response_dict = response.dict()
                # 手动处理 datetime 序列化
                if 'memories' in response_dict:
                    for memory in response_dict['memories']:
                        if 'created_at' in memory and memory['created_at']:
                            memory['created_at'] = memory['created_at'].isoformat()
                return response_dict
            
        except StorageError as e:
            logger.error(f"Storage error while querying memories: {str(e)}")
            return {
                "error": "storage_error",
                "message": f"存储错误: {str(e)}",
                "details": {}
            }
        
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            return {
                "error": "validation_error",
                "message": f"数据验证错误: {str(e)}",
                "details": {}
            }
        
        except Exception as e:
            logger.error(f"Unexpected error while querying memories: {str(e)}")
            return {
                "error": "internal_error",
                "message": "内部服务器错误",
                "details": {"exception": str(e)}
            }


async def query_memory_endpoint(request_data: Dict[str, Any], storage: MemoryStorageInterface) -> Dict[str, Any]:
    """
    查询记忆端点函数
    
    Args:
        request_data: 请求数据
        storage: 存储接口
        
    Returns:
        Dict[str, Any]: 响应数据
    """
    handler = QueryMemoryHandler(storage)
    return await handler.handle(request_data)
