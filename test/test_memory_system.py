"""
MCP Memory 系统测试
"""

import asyncio
import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.main import MCPMemoryServer
from src.models.memory import MemoryType, ImportanceLevel

async def test_memory_system():
    """测试MCP Memory系统功能"""
    
    print("开始测试MCP Memory系统...")
    
    # 显示当前存储配置
    storage_type = os.getenv("MEMORY_STORAGE", "agentic")
    print(f"存储类型: {'Mock (测试模式)' if storage_type == 'mock' else 'Agentic Memory (智能模式)'}")

    # 创建服务器实例（使用新的环境变量配置）
    print("\n初始化Memory系统...")
    server = MCPMemoryServer()
    print("Memory系统初始化成功!")
    
    # 测试数据 - 包含不同类型的记忆
    test_memories = [
        {
            "content": "用户反馈界面响应速度太慢，希望能够优化加载时间",
            "memory_type": "experience",
            "importance": "high",
            "tags": ["ui", "performance", "user-feedback"],
            "related_task_id": 101
        },
        {
            "content": "Python中的list comprehension比传统for循环更高效",
            "memory_type": "knowledge",
            "importance": "medium",
            "tags": ["python", "optimization", "programming"],
            "related_task_id": 102
        },
        {
            "content": "今天与客户讨论了新功能需求，客户特别强调要简洁易用",
            "memory_type": "conversation",
            "importance": "high",
            "tags": ["client", "requirements", "ui-design"],
            "related_task_id": 103
        },
        {
            "content": "当前项目采用微服务架构，使用Docker容器化部署",
            "memory_type": "context",
            "importance": "medium",
            "tags": ["architecture", "microservices", "docker"],
            "related_task_id": 104
        },
        {
            "content": "机器学习模型需要大量训练数据，数据质量直接影响模型性能",
            "memory_type": "knowledge",
            "importance": "high",
            "tags": ["machine-learning", "data-quality", "training"],
            "related_task_id": 105
        }
    ]
    
    print(f"\n测试保存 {len(test_memories)} 条记忆...")
    saved_contexts = []
    
    for i, memory_data in enumerate(test_memories, 1):
        print(f"\n保存记忆 {i}: {memory_data['memory_type']}")
        result = await server.handle_save_memory(memory_data)
        
        if "error" not in result:
            context_id = result.get("context_id")
            saved_contexts.append(context_id)
            print(f"保存成功: {context_id}")
            print(f"   内容: {memory_data['content']}")
        else:
            print(f"保存失败: {result['message']}")
    
    print(f"\n成功保存了 {len(saved_contexts)} 条记忆!")
    
    # 测试智能查询
    print("\n测试智能语义搜索...")
    
    search_queries = [
        {
            "query": "用户界面优化",
            "description": "查找与用户界面相关的记忆",
            "types": ["experience", "conversation"]
        },
        {
            "query": "Python编程技巧",
            "description": "查找编程相关知识",
            "types": ["knowledge"]
        },
        {
            "query": "机器学习数据",
            "description": "查找ML相关内容",
            "types": ["knowledge"]
        },
        {
            "query": "项目架构设计",
            "description": "查找技术架构信息",
            "types": ["context"]
        }
    ]
    
    for search in search_queries:
        print(f"\n{search['description']}")
        print(f"   查询: '{search['query']}'")
        
        query_request = {
            "search_text": search["query"],
            "memory_types": search["types"],
            "limit": 3,
            "min_similarity": 0.1
        }
        
        result = await server.handle_query_memory(query_request)
        
        if "error" not in result:
            memories = result.get("memories", [])
            print(f"找到 {len(memories)} 条相关记忆")
            print(memories)
            
            for j, memory in enumerate(memories, 1):
                similarity = memory.get('similarity', 0.0)
                content = memory.get('content', '')
                memory_type = memory.get('memory_type', '')
                print(f"   {j}. [{memory_type}] 相似度: {similarity:.3f}")
                print(f"      {content}")
                
                # 显示A_MEM增强的元数据
                meta = memory.get('meta', {})
                if meta.get('agentic_keywords'):
                    print(f"      关键词: {meta['agentic_keywords']}")
                if meta.get('agentic_context'):
                    print(f"      上下文: {meta['agentic_context']}")
        else:
            print(f"查询失败: {result['message']}")
    
    # 测试跨类型关联查询
    print("\n测试跨类型关联查询...")
    cross_query = {
        "search_text": "用户体验和性能优化",
        "memory_types": [],  # 不限制类型
        "limit": 5,
        "min_similarity": 0.1
    }
    
    result = await server.handle_query_memory(cross_query)
    if "error" not in result:
        memories = result.get("memories", [])
        print(f"跨类型查询找到 {len(memories)} 条记忆")
        
        # 按类型分组显示
        by_type = {}
        for memory in memories:
            mem_type = memory.get('memory_type', 'unknown')
            if mem_type not in by_type:
                by_type[mem_type] = []
            by_type[mem_type].append(memory)
        
        for mem_type, mems in by_type.items():
            print(f"   {mem_type}: {len(mems)} 条")
    
    print("\n A_MEM集成测试完成")
    


if __name__ == "__main__":
    print("=" * 70)
    print("        MCP Memory 系统功能测试")
    print("=" * 70)
    
    try:
        asyncio.run(test_memory_system())
    except Exception as e:
        print(f"\n测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
