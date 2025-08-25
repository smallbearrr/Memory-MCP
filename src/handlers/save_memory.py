"""
Save memory API handler
"""

import logging
from typing import Dict, Any

from ..models.memory import SaveMemoryRequest, SaveMemoryResponse, APIError
from ..storage.memory_storage import MemoryStorageInterface, StorageError

logger = logging.getLogger(__name__)


class SaveMemoryHandler:
    """保存记忆处理器"""
    
    def __init__(self, storage: MemoryStorageInterface):
        self.storage = storage
    
    async def handle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理保存记忆请求
        
        Args:
            request_data: 请求数据
            
        Returns:
            Dict[str, Any]: 响应数据
        """
        try:
            # 验证请求数据
            request = SaveMemoryRequest(**request_data)
            
            # 保存记忆
            response = await self.storage.save_memory(request)
            
            logger.info(f"Successfully saved memory with context_id: {response.context_id}")
            
            # 返回保存响应
            try:
                # 尝试使用新版本 Pydantic 的方法，使用 mode='json' 来处理 datetime
                return response.model_dump(mode='json')
            except AttributeError:
                # 回退到旧版本 Pydantic 的方法
                response_dict = response.model_dump()
                # 手动处理 datetime 序列化
                if 'created_at' in response_dict and response_dict['created_at']:
                    response_dict['created_at'] = response_dict['created_at'].isoformat()
                return response_dict
            
        except StorageError as e:
            logger.error(f"Storage error while saving memory: {str(e)}")
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
            logger.error(f"Unexpected error while saving memory: {str(e)}")
            return {
                "error": "internal_error",
                "message": "内部服务器错误",
                "details": {"exception": str(e)}
            }


async def save_memory_endpoint(request_data: Dict[str, Any], storage: MemoryStorageInterface) -> Dict[str, Any]:
    """
    保存记忆端点函数
    
    Args:
        request_data: 请求数据
        storage: 存储接口
        
    Returns:
        Dict[str, Any]: 响应数据
    """
    handler = SaveMemoryHandler(storage)
    return await handler.handle(request_data)
