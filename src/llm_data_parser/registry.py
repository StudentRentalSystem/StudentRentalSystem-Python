import requests
from typing import Set


class ModelRegistry:
    _loaded: bool = False
    _available_models: Set[str] = set()

    @classmethod
    def load_models_from_ollama(cls, address: str, port: int) -> None:
        """
        從 Ollama API 載入模型列表
        """
        url = f"{address}:{port}/api/tags"
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            cls._available_models.clear()
            for model in data.get("models", []):
                cls._available_models.add(model["name"])
            
            cls._loaded = True
        except Exception as e:
            raise RuntimeError(f"Cannot load models from Ollama: {e}")

    @classmethod
    def is_available(cls, address: str, port: int, model_name: str) -> bool:
        """
        檢查指定模型是否可用
        """
        if not cls._loaded:
            try:
                cls.load_models_from_ollama(address, port)
            except Exception as e:
                # 為了避免初始化失敗導致程式崩潰，這裡可以選擇拋出異常或返回 False
                print(f"Registry Warning: {e}")
                return False
                
        # 簡單的比對，有時候使用者輸入 'llama3' 但系統是 'llama3:latest'，這裡做精確比對
        return model_name in cls._available_models

    @classmethod
    def get_all_models(cls) -> Set[str]:
        return cls._available_models.copy()