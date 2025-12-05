from typing import Dict, Any, Callable, List
from config import LLMMode

def receive_chat_mode_handler(json_data: Dict[str, Any]) -> str:
    """提取 Chat 模式的內容"""
    return json_data.get("message", {}).get("content", "")

def receive_generate_mode_handler(json_data: Dict[str, Any]) -> str:
    """提取 Generate 模式的內容"""
    return json_data.get("response", "")

def receive_embeddings_mode_handler(json_data: Dict[str, Any]) -> List[float]:
    """提取 Embeddings 模式的向量"""
    return json_data.get("embedding", [])

class LLMAPIRules:
    """
    定義處理回應的規則映射
    """
    _receive_rules: Dict[LLMMode, Callable[[Dict[str, Any]], Any]] = {
        LLMMode.CHAT: receive_chat_mode_handler,
        LLMMode.GENERATE: receive_generate_mode_handler,
        LLMMode.EMBEDDINGS: receive_embeddings_mode_handler
    }

    @classmethod
    def get_receive_rules(cls) -> Dict[LLMMode, Callable[[Dict[str, Any]], Any]]:
        return cls._receive_rules