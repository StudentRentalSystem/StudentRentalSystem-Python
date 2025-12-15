from typing import Optional

from src.query_generator.utils import get_string_json
from src.rag_service.client import LLMClient
from src.rag_service.llm_config import LLMConfig, LLMMode
from src.config import Config
from src.query_generator.prompts import QUERY_PARSER_PROMPT


class MiniRagApp:
    def __init__(self, llm_config: Optional[LLMConfig] = None):
        if llm_config is None:
            llm_config = LLMConfig(
                mode=LLMMode.CHAT,
                server_address=Config.LLM_SERVER_ADDRESS,
                server_port=Config.LLM_SERVER_PORT,
                model_type=Config.LLM_MODEL_TYPE,
                stream=False
            )

        self.llm_config = llm_config
        self.llm_client = LLMClient(self.llm_config)
        self.query_prompt_template = QUERY_PARSER_PROMPT


    def format_query(self, query: str) -> dict:
        formatted_prompt = self.query_prompt_template.replace("{user_query}", query)
        response = self.llm_client.call_local_model(formatted_prompt)

        try:
            response = get_string_json(response)
            json_resp = response["filters"]
            return json_resp
        except Exception as e:
            print("LLM 解析失敗，回退到純文字搜尋: ", e)
            print(response)
            return {"search_text": query, "filters": {}}
