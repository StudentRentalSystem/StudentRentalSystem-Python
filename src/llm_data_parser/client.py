import requests
import json
import logging
from typing import Optional
from queue import Queue
from src.llm_data_parser.config import LLMConfig, LLMMode


# 定義一個簡單的資料類別，確保 main.py 能正確讀取屬性
class LLMResponseData:
    def __init__(self, token: Optional[str] = None, completed: bool = False, complete_text: str = ""):
        self.token = token
        self.completed = completed
        self.complete_text = complete_text
        # 相容舊版屬性
        self.text = token
        self.content = token


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.config = config
        # 整理 Base URL (移除結尾斜線)
        base_url = f"{config.server_address}:{config.server_port}"
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url

    def call_local_model(self, prompt: str):
        """
        對外公開的呼叫方法，自動判斷正確的 API Endpoint
        """
        # 根據模式選擇正確的 Ollama Endpoint
        if self.config.mode == LLMMode.CHAT:
            endpoint = "/api/chat"
        elif self.config.mode == LLMMode.EMBEDDINGS:
            endpoint = "/api/embeddings"
        else:
            endpoint = "/api/generate"

        url = f"{self.base_url}{endpoint}"

        # 嘗試從 config 取得 api_key (如果有的話)
        token = getattr(self.config, 'token', None)

        return self._call_local_model_internal(
            prompt=prompt,
            mode=self.config.mode,
            url=url,
            model=self.config.model_type,
            stream=self.config.stream,
            queue=self.config.queue,
            token=token  # 傳遞 API Key
        )

    def _call_local_model_internal(self, prompt: str, mode: LLMMode, url: str, model: str, stream: bool,
                                   queue: Optional[Queue], token: Optional[str] = None) -> str:
        try:
            # 1. 建構 Payload
            payload = {
                "model": model,
                "stream": stream
            }

            if mode == LLMMode.CHAT:
                payload["messages"] = [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            else:
                payload["prompt"] = prompt

            # 2. 建構 Headers (加入 User-Agent 防止被擋)
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            if token:
                headers["Authorization"] = f"Bearer {token}"

            # 3. 發送請求
            with requests.post(url, json=payload, stream=stream, headers=headers) as response:
                # 如果回傳 403/401，這裡會拋出異常
                if response.status_code in [401, 403]:
                    error_msg = f"權限錯誤 ({response.status_code}): 請檢查 .env 中的 LLM_API_KEY 是否正確。"
                    print(f"❌ {error_msg}")
                    if queue:
                        queue.put(LLMResponseData(token=error_msg, completed=True))
                    return error_msg

                response.raise_for_status()

                # --- 非串流模式 (一次回傳) ---
                if not stream:
                    json_response = response.json()
                    if mode == LLMMode.EMBEDDINGS:
                        return str(json_response.get("embedding", []))

                    if mode == LLMMode.CHAT:
                        return json_response.get("message", {}).get("content", "")
                    return json_response.get("response", "")

                # --- 串流模式 (逐字回傳) ---
                full_text_buffer = ""

                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        try:
                            json_obj = json.loads(decoded_line)

                            if json_obj.get("done") and json_obj.get("done_reason") == "load":
                                continue

                            content_piece = ""
                            if mode == LLMMode.CHAT:
                                content_piece = json_obj.get("message", {}).get("content", "")
                            else:
                                content_piece = json_obj.get("response", "")

                            if content_piece:
                                full_text_buffer += content_piece
                                if queue:
                                    queue.put(LLMResponseData(token=content_piece, completed=False))

                            if json_obj.get("done", False):
                                if queue:
                                    queue.put(
                                        LLMResponseData(token=None, completed=True, complete_text=full_text_buffer))
                                break

                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            # 捕獲其他連線錯誤
            error_text = f"LLMClient Error: {e}"
            print(f"❌ {error_text}")
            if queue:
                queue.put(LLMResponseData(token=f"Error: {e}", completed=True))
            return ""

        return ""

    def get_detail_message(self, json_response):
        if self.config.mode == LLMMode.CHAT:
            return json_response.get("message", {}).get("content", "")
        return json_response.get("response", "")