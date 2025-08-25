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
        
        # 生成task_id（如果没有提供related_task_id）
        task_id = request.related_task_id or self._task_counter
        if not request.related_task_id:
            self._task_counter += 1
        
        # 生成context_id
        context_id = f"{task_id}_{request.memory_type.value}"
        
        # 创建记忆对象
        created_at = datetime.utcnow()
        
        # 存储记忆
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
            # 内容搜索
            if search_text_lower not in memory_data["content"].lower():
                continue
            
            # 记忆类型过滤
            if request.memory_types and memory_data["memory_type"] not in request.memory_types:
                continue
            
            # 计算简单的相似度分数（基于关键词匹配）
            similarity = self._calculate_similarity(request.search_text, memory_data["content"])
            
            # 相似度阈值过滤
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
        
        # 按相似度排序
        filtered_memories.sort(key=lambda x: x.similarity, reverse=True)
        
        # 限制返回数量
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


class AgenticMemoryStorage(MemoryStorageInterface):
    """
    基于a_mem的智能记忆存储实现
    
    提供完整的a_mem智能记忆管理功能：
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
            raise StorageError("Agentic Memory System不可用，请检查a_mem模块")
        
        try:
            self.agentic_memory = AgenticMemorySystem(
                model_name=model_name,
                llm_backend=llm_backend,
                llm_model=llm_model,
                evo_threshold=evo_threshold,
                api_key=api_key
            )
            self._task_counter = 1
            # 用于存储MCP特定的映射关系
            self._mcp_mappings = {}  # memory_id -> mcp_metadata
            logger.info("Agentic Memory Storage 初始化成功")
        except Exception as e:
            raise StorageError(f"初始化Agentic Memory失败: {str(e)}")
    
    def _generate_task_id(self, related_task_id: Optional[int]) -> int:
        """生成或使用任务ID"""
        if related_task_id:
            return related_task_id
        
        task_id = self._task_counter
        self._task_counter += 1
        return task_id
    
    def _generate_context_id(self, task_id: int, memory_type) -> str:
        """生成context_id"""
        return f"{task_id}_{memory_type.value}"
    
    async def save_memory(self, request: SaveMemoryRequest) -> SaveMemoryResponse:
        """保存记忆到Agentic Memory系统"""
        try:
            # 生成task_id和context_id
            task_id = self._generate_task_id(request.related_task_id)
            context_id = self._generate_context_id(task_id, request.memory_type)
            
            # 准备传递给a_mem的参数
            a_mem_kwargs = {
                'content': request.content,
                'tags': request.tags or [],
                'category': request.memory_type.value,
                'context': f"Task {task_id}",
                'timestamp': datetime.utcnow().strftime("%Y%m%d%H%M")
            }
            
            # 使用a_mem的add_note方法保存记忆
            memory_id = self.agentic_memory.add_note(**a_mem_kwargs)
            if DEBUG == True:
                memory = self.agentic_memory.read(memory_id)
                print(f"Content: {memory.content}")
                print(f"Auto-generated Keywords: {memory.keywords}")  # e.g., ['machine learning', 'neural networks', 'datasets']
                print(f"Auto-generated Context: {memory.context}")    # e.g., "Discussion about ML algorithms and data processing"
                print(f"Auto-generated Tags: {memory.tags}")          # e.g., ['artificial intelligence', 'data science', 'technology']

            # 存储MCP特定的映射信息
            self._mcp_mappings[memory_id] = {
                "context_id": context_id,
                "task_id": task_id,
                "memory_type": request.memory_type.value,
                "importance": request.importance.value,
                "mcp_tags": request.tags or []
            }
            
            logger.info(f"记忆保存成功: context_id={context_id}, memory_id={memory_id}")
            
            return SaveMemoryResponse(
                context_id=context_id,
                task_id=task_id,
                memory_type=request.memory_type,
                content=request.content,
                created_at=datetime.now(),
                embedding_generated=True  # a_mem系统会生成嵌入
            )
            
        except Exception as e:
            logger.error(f"保存记忆失败: {str(e)}")
            raise StorageError(f"保存记忆失败: {str(e)}")
    
    async def query_memory(self, request: QueryMemoryRequest) -> QueryMemoryResponse:
        """从Agentic Memory系统查询记忆"""
        try:
            from ..models.memory import MemoryItem, MemoryType
            
            # 使用a_mem的search_agentic进行智能搜索
            search_results = self.agentic_memory.search_agentic(
                query=request.search_text,
                k=request.limit * 2  # 获取更多结果用于过滤
            )

            if DEBUG == True:
                for result in search_results:
                    print(f"ID: {result['id']}")
                    print(f"Content: {result['content'][:100]}...")
                    print(f"Tags: {result['tags']}")
                    print("---")
            
            memories = []
            
            for result in search_results:
                memory_id = result['id']
                
                # 获取MCP映射信息
                mcp_info = self._mcp_mappings.get(memory_id, {})
                task_id = mcp_info.get("task_id", 1)
                importance = mcp_info.get("importance", "medium")
                mcp_tags = mcp_info.get("mcp_tags", [])
                
                # 推断memory_type
                memory_type_str = mcp_info.get("memory_type")
                if memory_type_str:
                    try:
                        memory_type = MemoryType(memory_type_str)
                    except ValueError:
                        memory_type = self._infer_memory_type_from_result(result)
                else:
                    memory_type = self._infer_memory_type_from_result(result)
                
                # 记忆类型过滤
                if request.memory_types and memory_type not in request.memory_types:
                    continue
                
                # 相似度处理
                similarity = result.get('score', 0.0)
                # a_mem返回的是距离，需要转换为相似度
                if similarity > 1.0:
                    similarity = max(0.0, 1.0 - (similarity / 2.0))
                elif similarity < 0:
                    similarity = 0.0
                
                # 相似度过滤
                if similarity < request.min_similarity:
                    continue
                
                # 解析创建时间
                try:
                    timestamp = result.get('timestamp', '')
                    if timestamp:
                        created_at = datetime.strptime(timestamp, "%Y%m%d%H%M")
                    else:
                        created_at = datetime.utcnow()
                except:
                    created_at = datetime.utcnow()
                
                # 构建内存项
                memory_item = MemoryItem(
                    task_id=task_id,
                    memory_type=memory_type,
                    content=result.get('content', ''),
                    similarity=similarity,
                    created_at=created_at,
                    meta={
                        "importance": importance,
                        "tags": mcp_tags,
                        "agentic_keywords": result.get('keywords', []),
                        "agentic_context": result.get('context', ''),
                        "agentic_category": result.get('category', ''),
                        "agentic_tags": result.get('tags', []),
                        "is_neighbor": result.get('is_neighbor', False)
                    }
                )
                
                memories.append(memory_item)
            
            # 按相似度排序并限制数量
            memories.sort(key=lambda x: x.similarity, reverse=True)
            result_memories = memories[:request.limit]
            
            logger.info(f"查询成功: 找到 {len(result_memories)} 条记忆")
            
            return QueryMemoryResponse(
                memories=result_memories,
                total=len(memories)
            )
            
        except Exception as e:
            logger.error(f"查询记忆失败: {str(e)}")
            raise StorageError(f"查询记忆失败: {str(e)}")
    
    def _infer_memory_type_from_result(self, result: Dict[str, Any]):
        """从a_mem结果推断记忆类型"""
        from ..models.memory import MemoryType
        
        # 首先尝试从category推断
        category = result.get('category', '').lower()
        for memory_type in MemoryType:
            if memory_type.value in category:
                return memory_type
        
        # 然后尝试从tags推断
        tags = result.get('tags', [])
        for tag in tags:
            try:
                return MemoryType(tag)
            except ValueError:
                continue
        
        # 最后尝试从context推断
        context = result.get('context', '').lower()
        if 'conversation' in context or 'chat' in context:
            return MemoryType.CONVERSATION
        elif 'knowledge' in context or 'fact' in context:
            return MemoryType.KNOWLEDGE
        elif 'experience' in context or 'task' in context:
            return MemoryType.EXPERIENCE
        elif 'context' in context:
            return MemoryType.CONTEXT
        
        # 默认返回conversation
        return MemoryType.CONVERSATION


def create_storage() -> MemoryStorageInterface:
    """
    工厂函数：根据环境变量创建存储实例
    
    环境变量：
    - MEMORY_STORAGE=mock: 使用Mock存储（测试用）
    - 其他值或未设置: 默认使用Agentic Memory存储
    
    Returns:
        MemoryStorageInterface: 存储实例
    """
    storage_type = os.getenv("MEMORY_STORAGE", "agentic").lower()
    
    if storage_type == "mock":
        logger.info(" 使用Mock存储（由环境变量MEMORY_STORAGE=mock指定）")
        return MockMemoryStorage()
    
    # 默认尝试使用Agentic Memory
    if AGENTIC_MEMORY_AVAILABLE:
        try:
            logger.info("使用Agentic Memory存储（默认模式）")
            print("正在初始化 Agentic Memory...", file=sys.stderr, flush=True)
            storage = AgenticMemoryStorage()
            print(" Agentic Memory 初始化成功!", file=sys.stderr, flush=True)
            return storage
        except Exception as e:
            logger.warning(f"Agentic Memory初始化失败，回退到Mock存储: {str(e)}")
            print(f" Agentic Memory初始化失败: {str(e)}", file=sys.stderr, flush=True)
            print("回退到 Mock 存储", file=sys.stderr, flush=True)
            return MockMemoryStorage()
    else:
        logger.warning("Agentic Memory不可用，使用Mock存储")
        print(" Agentic Memory 不可用，使用 Mock 存储", file=sys.stderr, flush=True)
        return MockMemoryStorage()
