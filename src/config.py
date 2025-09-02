"""
Configuration settings for MCP Memory Server
"""

import os
from typing import Optional


class Config:
    """服务器配置类"""
    
    # 服务器设置
    SERVER_NAME: str = "MCP Memory Server"
    SERVER_VERSION: str = "0.1.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # 存储设置
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "mock")  # mock, sqlite, postgres, etc.
    MEMORY_STORAGE: str = os.getenv("MEMORY_STORAGE", "mock")  # mock, agentic, or other models
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # 记忆设置
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", "10000"))
    MAX_TAGS_COUNT: int = int(os.getenv("MAX_TAGS_COUNT", "20"))
    MAX_TAG_LENGTH: int = int(os.getenv("MAX_TAG_LENGTH", "50"))
    MAX_METADATA_SIZE: int = int(os.getenv("MAX_METADATA_SIZE", "5000"))
    
    # 查询设置
    DEFAULT_QUERY_LIMIT: int = int(os.getenv("DEFAULT_QUERY_LIMIT", "50"))
    MAX_QUERY_LIMIT: int = int(os.getenv("MAX_QUERY_LIMIT", "1000"))
    MAX_SEARCH_KEYWORD_LENGTH: int = int(os.getenv("MAX_SEARCH_KEYWORD_LENGTH", "500"))
    
    # 语义搜索设置
    ENABLE_SEMANTIC_SEARCH: bool = os.getenv("ENABLE_SEMANTIC_SEARCH", "False").lower() == "true"
    SEMANTIC_MODEL_PATH: Optional[str] = os.getenv("SEMANTIC_MODEL_PATH")
    DEFAULT_SIMILARITY_THRESHOLD: float = float(os.getenv("DEFAULT_SIMILARITY_THRESHOLD", "0.7"))
    
    # 清理设置
    AUTO_CLEANUP_ENABLED: bool = os.getenv("AUTO_CLEANUP_ENABLED", "True").lower() == "true"
    CLEANUP_INTERVAL_HOURS: int = int(os.getenv("CLEANUP_INTERVAL_HOURS", "24"))
    
    # 日志设置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")


# 全局配置实例
config = Config()