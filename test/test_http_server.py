# python -m test.test_http_server
import uvicorn
from src.main import MCPMemoryServer, MCP_TOOLS
from src.storage.memory_storage import create_storage
from src.models.memory import (
    SaveMemoryRequest, SaveMemoryResponse,
    QueryMemoryRequest, QueryMemoryResponse,
)
import requests, time
from multiprocessing import Process

def run_uvicorn():
    uvicorn.run(
        "src.http_server:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )

def wait_for_server(base_url="http://127.0.0.1:8000", timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{base_url}/healthz")
            if r.status_code == 200:
                print("服务器已就绪")
                return True
        except Exception:
            pass
        time.sleep(0.2)
    raise RuntimeError("等待服务器启动超时")


if __name__ == "__main__":
    p = Process(target=run_uvicorn, daemon=True)
    p.start()

    wait_for_server()

    base_url = "http://127.0.0.1:8000"

    # 1. 检查
    try:
        r = requests.get(f"{base_url}/healthz")
        print("Healthz:", r.json())
    except Exception as e:
        print("Healthz 请求失败:", e)

    # 2. 保存
    payloads = [
        {
            "content": "Today I isolated E. coli from soil samples. The bacteria showed lactose fermentation on MacConkey agar and tested gram-negative. Planning 16S rRNA sequencing for species confirmation.",
            "memory_type": "experience",
            "importance": "high",
            "tags": ["e-coli", "isolation", "soil-sample", "16s-rRNA"],
            "related_task_id": 2001
        },
        {
            "content": "Dr. Chen mentioned that CRISPR-Cas9 can be used for precise gene editing in E. coli. She suggested trying to knockout the lacZ gene to create a white colony phenotype on X-gal plates.",
            "memory_type": "conversation",
            "importance": "medium",
            "tags": ["CRISPR-Cas9", "gene-editing", "lacZ", "knockout"],
            "related_task_id": 2002
        },
        {
            "content": "Observed that biofilm formation in Pseudomonas aeruginosa increases dramatically under low oxygen conditions. The bacteria switch to anaerobic metabolism and produce more exopolysaccharides.",
            "memory_type": "experience",
            "importance": "high",
            "tags": ["biofilm", "Pseudomonas", "anaerobic", "exopolysaccharides"],
            "related_task_id": 2003
        },
        {
            "content": "Lab meeting discussion: 16S rRNA gene sequencing is still the gold standard for bacterial identification, but MALDI-TOF mass spectrometry is faster for routine clinical diagnostics.",
            "memory_type": "conversation",
            "importance": "medium",
            "tags": ["16s-rRNA", "MALDI-TOF", "bacterial-identification", "clinical-diagnostics"],
            "related_task_id": 2004
        }
    ]
    
    for i, payload in enumerate(payloads, 1):
        try:
            r = requests.post(f"{base_url}/mcp/save_memory", json=payload)
            print(f"SaveMemory{i}:", r.status_code, r.json())
        except Exception as e:
            print(f"SaveMemory{i} 请求失败:", e)

    # 3. 查询
    try:
        payload = {
            "search_text": "E. coli isolation soil bacteria",
            "memory_types": ["experience"],
            "limit": 10,
            "min_similarity": 0.3
        }
        r = requests.post(f"{base_url}/mcp/query_memory", json=payload)
        print("QueryMemory:", r.status_code, r.json())
    except Exception as e:
        print("QueryMemory 请求失败:", e)


    p.terminate()
    p.join()
