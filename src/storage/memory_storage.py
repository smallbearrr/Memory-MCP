"""
Memory storage interface for simplified MCP Memory system
"""

import sys
import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from ..models.memory import SaveMemoryRequest, SaveMemoryResponse, QueryMemoryRequest, QueryMemoryResponse

from ..a_mem.agentic_memory.memory_system import AgenticMemorySystem, MemoryNote
AGENTIC_MEMORY_AVAILABLE = True
DEBUG = True

logger = logging.getLogger(__name__)


class MemoryStorageInterface(ABC):
    @abstractmethod
    async def save_memory(self, request: SaveMemoryRequest) -> SaveMemoryResponse:
        pass
    
    @abstractmethod
    async def query_memory(self, request: QueryMemoryRequest) -> QueryMemoryResponse:
        pass


class StorageError(Exception):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class AgenticMemoryStorage(MemoryStorageInterface):
    """
    Agentic Memory 后端
    
    - 自动内容分析和元数据生成
    - 语义搜索和向量检索
    - 智能记忆演化和链接
    - ChromaDB持久化存储
    """
    
    def __init__(self, 
                 model_name: str = 'all-MiniLM-L6-v2',
                 llm_backend: str = "glm",
                 llm_model: str = "glm-4-flash",
                 evo_threshold: int = 100,
                 api_key: Optional[str] = None):
        
        if not AGENTIC_MEMORY_AVAILABLE:
            raise StorageError("Agentic Memory System不可用，初始化失败")
        
        try:
            self.agentic_memory = AgenticMemorySystem(
                model_name=model_name,
                llm_backend=llm_backend,
                llm_model=llm_model,
                evo_threshold=evo_threshold,
                api_key=api_key
            )
            self._task_counter = 1
            logger.info("Agentic Memory Storage 初始化成功")
        except Exception as e:
            raise StorageError(f"初始化Agentic Memory失败: {str(e)}")
    
    async def save_memory(self, request: SaveMemoryRequest) -> SaveMemoryResponse:
        """保存记忆到Agentic Memory系统"""
        try:
            
            a_mem_kwargs = {
                'content': request.content,
            }
            
            memory_id = self.agentic_memory.add_note(**a_mem_kwargs)
            # if DEBUG == True:
            #     memory = self.agentic_memory.read(memory_id)
            #     print(f"Content: {memory.content}")
            #     print(f"Auto-generated Keywords: {memory.keywords}")  # e.g., ['machine learning', 'neural networks', 'datasets']
            #     print(f"Auto-generated Context: {memory.context}")    # e.g., "Discussion about ML algorithms and data processing"
            #     print(f"Auto-generated Tags: {memory.tags}")          # e.g., ['artificial intelligence', 'data science', 'technology']
            
            logger.info(f"记忆保存成功: memory_id={memory_id}")
            
            return SaveMemoryResponse(
                content=request.content,
            )
            
        except Exception as e:
            logger.error(f"保存记忆失败: {str(e)}")
            raise StorageError(f"保存记忆失败: {str(e)}")
    
    async def query_memory(self, request: QueryMemoryRequest) -> QueryMemoryResponse:
        """从Agentic Memory系统查询记忆"""
        try:
            from ..models.memory import MemoryItem
            
            # 使用a_mem的search_agentic进行智能搜索
            search_results = self.agentic_memory.search_agentic(
                query=request.search_text,
                k=request.limit
            )

            # if DEBUG == True:
            #     for result in search_results:
            #         print(f"ID: {result['id']}")
            #         print(f"Content: {result['content'][:100]}...")
            #         print(f"Tags: {result['tags']}")
            #         print("---")
            
            memories = []
            
            for result in search_results:
                memory_id = result['id']
                
                # 构建内存项
                memory_item = MemoryItem(
                    content=result.get('content', ''),
                )
                
                memories.append(memory_item)
            
            logger.info(f"查询成功: 找到 {len(memories)} 条记忆")
            
            return QueryMemoryResponse(
                memories=memories,
                total=len(memories)
            )
            
        except Exception as e:
            logger.error(f"查询记忆失败: {str(e)}")
            raise StorageError(f"查询记忆失败: {str(e)}")
    

class MockMemoryStorage(MemoryStorageInterface):
    """
    简化的内存存储实现（用于测试）
    """
    
    def __init__(self):
        self._memories = {}
        self._task_counter = 1
    
    async def save_memory(self, request: SaveMemoryRequest) -> SaveMemoryResponse:
        """保存记忆到内存"""
        from datetime import datetime
        
        task_id = request.related_task_id or self._task_counter
        if not request.related_task_id:
            self._task_counter += 1
        
        context_id = f"{task_id}_{request.memory_type.value}"
        
        created_at = datetime.utcnow()
        
        memory_data = {
            "task_id": task_id,
            "memory_type": request.memory_type,
            "content": request.content,
            "created_at": created_at,
            "meta": {
                "importance": request.importance.value,
                "tags": request.tags or []
            }
        }
        
        self._memories[context_id] = memory_data
        
        return SaveMemoryResponse(
            context_id=context_id,
            task_id=task_id,
            memory_type=request.memory_type,
            content=request.content,
            created_at=created_at,
            embedding_generated=True  # Mock实现不生成嵌入
        )
    
    async def query_memory(self, request: QueryMemoryRequest) -> QueryMemoryResponse:
        """从内存中查询记忆"""
        from ..models.memory import MemoryItem
        
        filtered_memories = []
        search_text_lower = request.search_text.lower()
        
        for context_id, memory_data in self._memories.items():
            if search_text_lower not in memory_data["content"].lower():
                continue
            
            if request.memory_types and memory_data["memory_type"] not in request.memory_types:
                continue
            
            similarity = self._calculate_similarity(request.search_text, memory_data["content"])
            
            if similarity < request.min_similarity:
                continue
            
            memory_item = MemoryItem(
                task_id=memory_data["task_id"],
                memory_type=memory_data["memory_type"],
                content=memory_data["content"],
                similarity=similarity,
                created_at=memory_data["created_at"],
                meta=memory_data["meta"]
            )
            
            filtered_memories.append(memory_item)
        
        filtered_memories.sort(key=lambda x: x.similarity, reverse=True)
        
        result_memories = filtered_memories[:request.limit]
        
        return QueryMemoryResponse(
            memories=result_memories,
            total=len(filtered_memories)
        )
    
    def _calculate_similarity(self, query: str, content: str) -> float:
        """计算简单的相似度分数"""
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words:
            return 0.0
        
        intersection = query_words & content_words
        return len(intersection) / len(query_words)


def create_storage() -> MemoryStorageInterface:
    """
    - MEMORY_STORAGE=mock: 使用Mock存储（测试用）
    - 其他值或未设置: 默认使用Agentic Memory存储
    """
    storage_type = os.getenv("MEMORY_STORAGE", "agentic").lower()
    
    if storage_type == "mock":
        logger.info(" 使用Mock存储（由环境变量MEMORY_STORAGE=mock指定）")
        return MockMemoryStorage()
    
    # 默认尝试使用Agentic Memory
    if AGENTIC_MEMORY_AVAILABLE:
        if storage_type == "agentic":
            try:
                logger.info("使用Agentic Memory存储（默认模式）")
                storage = AgenticMemoryStorage()
                print(" Agentic Memory 初始化成功!", file=sys.stderr, flush=True)
                return storage
            except Exception as e:
                logger.warning(f"Agentic Memory初始化失败，回退到Mock存储: {str(e)}")
                return MockMemoryStorage()
        if storage_type == "":
            pass
    else:
        logger.warning("Agentic Memory不可用，使用Mock存储")
        return MockMemoryStorage()
