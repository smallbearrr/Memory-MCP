"""
Memory data models for simplified MCP Memory system
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class SaveMemoryRequest(BaseModel):
    content: str = Field(..., description="记忆内容")
    

    @field_validator('content')
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('记忆内容不能为空')
        return v.strip()


class SaveMemoryResponse(BaseModel):
    """保存记忆响应模型"""
    content: str = Field(..., description="记忆内容")



class QueryMemoryRequest(BaseModel):
    """查询记忆请求模型 - POST /memory/query"""
    search_text: str = Field(..., description="搜索文本")
    limit: int = Field(default=10, ge=1, le=100, description="返回数量限制")
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0, description="最小相似度阈值")


class MemoryItem(BaseModel):
    """记忆项模型"""
    content: str = Field(..., description="记忆内容")


class QueryMemoryResponse(BaseModel):
    """查询记忆响应模型"""
    memories: List[MemoryItem] = Field(..., description="记忆列表")
    total: int = Field(..., description="总数量")


class APIError(BaseModel):
    """API错误响应模型"""
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误信息")
    details: Optional[Dict[str, Any]] = Field(default=None, description="错误详情")
