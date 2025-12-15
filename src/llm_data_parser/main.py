import time
from queue import Queue
from threading import Thread

from src.llm_data_parser.llm_config import LLMConfig, LLMMode
from src.llm_data_parser.client import LLMClient


def main():
    print("=== 測試 1: 一般生成模式 (Generate) ===")
    
    # 初始化配置
    # 注意：請確保您的 Ollama 已啟動，並且有 llama3:8b 模型
    # 如果沒有，請修改 model_type，例如 "mistral" 或 "gemma"
    config = LLMConfig(
        mode=LLMMode.GENERATE,
        stream=True
    )

    client = LLMClient(config)
    
    prompt = "請用一句話解釋什麼是 Python。"
    print(f"Prompt: {prompt}")
    
    start_time = time.time()
    response = client.call_local_model(prompt)
    end_time = time.time()
    
    print(f"Response: {response}")
    print(f"耗時: {end_time - start_time:.2f} 秒\n")

    print("=== 測試 2: 串流模式 (Stream via Queue) ===")
    
    # 建立一個 Queue 來接收串流資料
    stream_queue = Queue()
    
    stream_config = LLMConfig(
        mode=LLMMode.CHAT,
        stream=True,
        queue=stream_queue
    )
    
    stream_client = LLMClient(stream_config)
    stream_prompt = "請寫一個簡單的 Python Hello World 程式。"
    
    # 因為 client.call_local_model 在 stream=True 時仍會阻塞直到完成(但在過程中會塞 queue)，
    # 為了模擬即時讀取 Queue，我們在另一個執行緒呼叫 client
    def run_client():
        stream_client.call_local_model(stream_prompt)

    t = Thread(target=run_client)
    t.start()
    
    print(f"Stream Prompt: {stream_prompt}")
    print("正在接收串流回應...", end="", flush=True)
    
    while True:
        # 從 Queue 讀取資料
        data = stream_queue.get()
        
        if data.completed:
            print("\n[傳輸完成]")
            break
            
        if data.token:
            # 即時列印 token，不換行
            print(data.token, end="", flush=True)
            
    t.join()

if __name__ == "__main__":
    main()