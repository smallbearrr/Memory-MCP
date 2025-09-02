"""
Save memory API handler
"""

import logging
from typing import Dict, Any

from ..models.memory import SaveMemoryRequest, SaveMemoryResponse, APIError
from ..storage.memory_storage import MemoryStorageInterface, StorageError

logger = logging.getLogger(__name__)


class SaveMemoryHandler:
    def __init__(self, storage: MemoryStorageInterface):
        self.storage = storage
    
    async def handle(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            request = SaveMemoryRequest(**request_data)
            
            response = await self.storage.save_memory(request)
            
            logger.info(f"Successfully saved memory")
            
            try:
                return response.model_dump(mode='json')
            except AttributeError:
                response_dict = response.model_dump()
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
    保存记忆端点
    
    Args:
        request_data: 请求数据
        storage: 存储接口
    """
    handler = SaveMemoryHandler(storage)
    return await handler.handle(request_data)
