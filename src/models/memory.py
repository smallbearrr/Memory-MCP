"""
Memory data models for simplified MCP Memory system
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class MemoryType(str, Enum):
    """记忆类型枚举 - 对应task_contexts.label"""
    CONVERSATION = "conversation"
    EXPERIENCE = "experience"
    KNOWLEDGE = "knowledge"
    CONTEXT = "context"


class ImportanceLevel(str, Enum):
    """重要性级别枚举"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    TEMPORARY = "temporary"


class SaveMemoryRequest(BaseModel):
    content: str = Field(..., description="记忆内容")
    memory_type: MemoryType = Field(..., description="记忆类型，对应task_contexts.label")
    importance: ImportanceLevel = Field(..., description="重要性级别，存储在meta字段")
    tags: Optional[List[str]] = Field(default=None, description="标签列表，存储在meta字段")
    related_task_id: Optional[int] = Field(default=None, description="关联任务ID")

    @field_validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('记忆内容不能为空')
        return v.strip()


class SaveMemoryResponse(BaseModel):
    """保存记忆响应模型"""
    context_id: str = Field(..., description="task_id + label组合的上下文ID")
    task_id: int = Field(..., description="任务ID")
    memory_type: MemoryType = Field(..., description="记忆类型")
    content: str = Field(..., description="记忆内容")
    created_at: datetime = Field(..., description="创建时间")
    embedding_generated: bool = Field(..., description="是否已生成嵌入向量")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QueryMemoryRequest(BaseModel):
    """查询记忆请求模型 - POST /memory/query"""
    search_text: str = Field(..., description="搜索文本")
    memory_types: Optional[List[MemoryType]] = Field(default=None, description="记忆类型过滤，对应label过滤")
    limit: int = Field(default=10, ge=1, le=100, description="返回数量限制")
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0, description="最小相似度阈值")


class MemoryItem(BaseModel):
    """记忆项模型"""
    task_id: int = Field(..., description="任务ID")
    memory_type: MemoryType = Field(..., description="记忆类型")
    content: str = Field(..., description="记忆内容")
    similarity: float = Field(..., description="相似度分数")
    created_at: datetime = Field(..., description="创建时间")
    meta: Dict[str, Any] = Field(..., description="元数据，包含importance和tags")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class QueryMemoryResponse(BaseModel):
    """查询记忆响应模型"""
    memories: List[MemoryItem] = Field(..., description="记忆列表")
    total: int = Field(..., description="总数量")


class APIError(BaseModel):
    """API错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
