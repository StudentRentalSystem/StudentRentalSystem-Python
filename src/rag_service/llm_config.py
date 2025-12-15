import os
from enum import Enum
from dataclasses import dataclass
from typing import Optional
from queue import Queue
from src.llm_data_parser.registry import ModelRegistry
from src.config import Config


class LLMMode(Enum):
    CHAT = "chat"
    GENERATE = "generate"
    EMBEDDINGS = "embeddings"

@dataclass
class LLMConfig:
    mode: LLMMode = LLMMode.GENERATE
    server_address: str = Config.LLM_SERVER_ADDRESS
    server_port: int = int(Config.LLM_SERVER_PORT)
    model_type: str = Config.LLM_MODEL_TYPE
    token: Optional[str] = Config.LLM_CLIENT_TOKEN
    stream: bool = False
    queue: Optional[Queue] = None
    
    def __post_init__(self):
        target = self.mode.value

        server_port_explicitly_set = os.getenv("LLM_SERVER_PORT") is not None

        if server_port_explicitly_set:
            self.request_url = f"{self.server_address}:{self.server_port}/api/{target}"
        elif "://" in self.server_address and "localhost" not in self.server_address:
            self.request_url = f"{self.server_address}/api/{target}"
        else:
            self.request_url = f"{self.server_address}:{self.server_port}/api/{target}"

        try:
            if not self.token:
                if "localhost" in self.server_address or not ("http://" in self.server_address or "https://" in self.server_address):
                    if not ModelRegistry.is_available(self.server_address, self.server_port, self.model_type):
                        raise ValueError(f"Model '{self.model_type}' does not exist in this machine at {self.server_address}:{self.server_port}!")
        except Exception as e:
            print(f"Warning: Could not verify model availability: {e}")
