import json
import re
from typing import Optional, Dict, Any
import os
import sys


current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
llm_data_parser_dir = os.path.join(src_dir, "llm_data_parser")

if src_dir not in sys.path:
    sys.path.append(src_dir)


from llm_data_parser.client import LLMClient
from llm_data_parser.config import LLMConfig, LLMMode

from .settings import (
    QUERY_PROMPT_PATH,
    MONGO_QUERY_PROMPT_PATH,
    LLM_SERVER_ADDRESS,
    LLM_SERVER_PORT,
    LLM_MODEL_TYPE
)
from .utils import get_string_json
from .fixer import MongoSearchStatementFixer


class MiniRagApp:
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        # 如果沒有傳入 config，則使用環境變數建立預設 config
        if llm_config is None:
            llm_config = LLMConfig(
                mode=LLMMode.CHAT,
                server_address=LLM_SERVER_ADDRESS,
                server_port=LLM_SERVER_PORT,
                model_type=LLM_MODEL_TYPE,
                stream=False
            )

        self.llm_config = llm_config
        self.llm_client = LLMClient(self.llm_config)
        self.query_prompt_template = ""
        self.mongo_query_prompt_template = ""

        self._load_prompts()

    def _load_prompts(self):
        try:
            # 使用 pathlib 的 read_text 方法，更簡潔
            self.query_prompt_template = QUERY_PROMPT_PATH.read_text(encoding="utf-8")
            self.mongo_query_prompt_template = MONGO_QUERY_PROMPT_PATH.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            raise RuntimeError(f"Cannot find prompt files at {QUERY_PROMPT_PATH.parent}: {e}")

    def format_query(self, query: str) -> str:
        formatted_prompt = self.query_prompt_template.replace("{query}", query)
        response = self.llm_client.call_local_model(formatted_prompt)

        response = response.replace("可", "是否可")
        response = response.replace("有", "是否有")

        # 嘗試從回應中提取內容，如果是 JSON 格式
        try:
            json_resp = json.loads(response)
            return self.llm_client.get_detail_message(json_resp)
        except:
            return response

    def format_mongodb_query(self, query: str) -> str:
        formatted_prompt = self.mongo_query_prompt_template.replace("{query}", query)
        return self.llm_client.call_local_model(formatted_prompt)

    def get_mongodb_search_cmd(self, query: str) -> str:
        raw_response = self.format_mongodb_query(query)

        try:
            # 嘗試解析 LLM 回傳的標準 JSON 格式
            json_obj = json.loads(raw_response)
            response_text = self.llm_client.get_detail_message(json_obj)
        except:
            # 如果解析失敗，可能已經是純文字或格式不標準，直接使用
            response_text = raw_response

        # 移除 <think> 標籤 (針對 DeepSeek 等模型)
        response_text = re.sub(r"(?s)<think>.*?</think>", "", response_text).strip()

        # 關鍵字替換
        response_text = response_text.replace("可", "是否可")
        response_text = response_text.replace("有", "是否有")

        return response_text

    def get_mongodb_search_cmd_json(self, query: str) -> Optional[Dict[str, Any]]:
        response_text = self.get_mongodb_search_cmd(query)
        return get_string_json(response_text)

    def get_fixed_mongo_query_cmd(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not query:
            return None
        return MongoSearchStatementFixer.fix_query(query)