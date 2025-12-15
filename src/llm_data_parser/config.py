import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from queue import Queue
from dotenv import load_dotenv
from src.llm_data_parser.registry import ModelRegistry

load_dotenv()

class LLMMode(Enum):
    CHAT = "chat"
    GENERATE = "generate"
    EMBEDDINGS = "embeddings"

@dataclass
class LLMConfig:
    """
    LLM 配置類別
    """
    mode: LLMMode = LLMMode.GENERATE
    server_address: str = os.getenv("LLM_SERVER_ADDRESS", "http://localhost")
    server_port: int = int(os.getenv("LLM_SERVER_PORT", 11434))
    model_type: str = os.getenv("LLM_MODEL_TYPE", "llama3:8b")
    token: Optional[str] = os.getenv("LLM_CLIENT_TOKEN")
    stream: bool = False
    queue: Optional[Queue] = None
    
    def __post_init__(self):
        """
        在初始化後執行驗證與 URL 建構
        """
        # 建構完整的請求 URL
        # self.mode = LLMMode.GENERATE
        # self.server_address = os.getenv("LLM_SERVER_ADDRESS")
        # self.server_port = os.getenv("LLM_SERVER_PORT")
        # self.token = os.getenv("LLM_TOKEN")
        # self.model_type = os.getenv("LLM_MODEL_TYPE")

        target = self.mode.value
        
        # 判斷是否需要將 port 加入 URL
        # 如果 server_address 已經是完整的 URL (例如包含 https:// 或 http:// 且不是 localhost)，
        # 並且 server_port 是預設值 11434，或者 .env 中沒有明確設定 LLM_SERVER_PORT，
        # 則可能不需要在 URL 中明確指定 port。
        # 這裡的邏輯是：如果 LLM_SERVER_PORT 在 .env 中有明確設定，則總是使用它。
        # 如果沒有設定，且 server_address 看起來像一個完整的 domain URL (非 localhost 且有 scheme)，
        # 則不添加預設 port 11434。否則，添加 port。
        
        # 檢查 LLM_SERVER_PORT 是否在 .env 中被明確設定
        server_port_explicitly_set = os.getenv("LLM_SERVER_PORT") is not None

        if server_port_explicitly_set:
            # 如果 port 被明確設定，則總是使用它
            self.request_url = f"{self.server_address}:{self.server_port}/api/{target}"
        elif "://" in self.server_address and "localhost" not in self.server_address:
            # 如果 server_address 包含 scheme (如 http://, https://) 且不是 localhost，
            # 則假設 port 已經包含在 address 中或使用標準 port (80/443)，不額外添加 port。
            self.request_url = f"{self.server_address}/api/{target}"
        else:
            # 其他情況 (例如 localhost 或沒有 scheme 的地址)，則添加 port
            self.request_url = f"{self.server_address}:{self.server_port}/api/{target}"


        # 檢查模型是否存在 (對應 Java 建構子中的檢查)
        # 注意：為了避免在測試時必須連網，可以選擇性地註解掉這行，或者用 try-catch 包裹
        try:
            # 如果有 token，通常表示連接到遠端服務，ModelRegistry.is_available 可能不適用或需要不同的驗證方式。
            # 因此，只有在沒有 token (假設為本地模式) 時才執行 ModelRegistry 檢查。
            if not self.token:
                # 為了 ModelRegistry.is_available 函數，我們需要一個 port。
                # 如果 URL 構造時沒有包含 port (因為是 https://... 且沒有明確指定 port)，
                # 這裡需要一個合理的 port 來檢查。對於 https，通常是 443。
                # 但 ModelRegistry.is_available 可能是針對本地 ollama 服務，其預設 port 是 11434。
                # 這裡暫時使用 self.server_port，它會是從 .env 讀取或預設的 11434。
                # 如果 ModelRegistry.is_available 真的需要不同的 port (例如 443)，則需要進一步調整。
                
                # 為了避免在遠端服務上執行本地檢查，我們只在沒有 token 的情況下執行此檢查。
                # 並且，如果 server_address 是一個完整的 URL (如 https://...)，
                # 則 ModelRegistry.is_available 可能不適用。
                # 這裡假設 ModelRegistry.is_available 僅用於本地 ollama 服務。
                if "localhost" in self.server_address or not ("http://" in self.server_address or "https://" in self.server_address):
                    if not ModelRegistry.is_available(self.server_address, self.server_port, self.model_type):
                        raise ValueError(f"Model '{self.model_type}' does not exist in this machine at {self.server_address}:{self.server_port}!")
            # 如果有 token，則假設服務是遠端的，不執行本地模型可用性檢查。
            # 遠端服務的模型可用性檢查應由服務本身處理。
        except Exception as e:
            print(f"Warning: Could not verify model availability: {e}")
