import sys
import os

import streamlit

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
src_dir = os.path.dirname(current_dir)
llm_data_parser_dir = os.path.join(src_dir, "llm_data_parser")

if project_root not in sys.path:
    sys.path.append(project_root)
if llm_data_parser_dir not in sys.path:
    sys.path.append(llm_data_parser_dir)

from src.query_generator.app import MiniRagApp
from src.llm_data_parser.config import LLMConfig, LLMMode
from src.frontend.config import Config

# Avoid multiple time initialized
@streamlit.cache_resource
class LLMService:
    def __init__(self):
        print(f"🔄 初始化系統中...")
        print(f"📍 連線目標: {Config.LLM_SERVER_ADDRESS}:{Config.LLM_SERVER_PORT} (Model: {Config.LLM_MODEL_TYPE})")
        if Config.LLM_CLIENT_TOKEN:
            print(f"🔑 API Key: 已載入 ({Config.LLM_CLIENT_TOKEN[:4]}***)")
        else:
            print(f"⚠️ API Key: 未設定 (如果遇到 403 錯誤，請在 settings.py 加入 LLM_API_KEY)")
        self.llm_config = LLMConfig(
            mode=LLMMode.CHAT,
            server_address=Config.LLM_SERVER_ADDRESS,
            server_port=Config.LLM_SERVER_PORT,
            model_type=Config.LLM_MODEL_TYPE,
            stream=False,
            token=Config.LLM_CLIENT_TOKEN,
        )
        self.mini_rag = MiniRagApp(self.llm_config)
        
    def generate_mongo_query(self, user_input) -> dict:
        """
        Convert natural language input into a MongoDB JSON query.
        """
        print("⏳ 正在分析並生成資料庫查詢語句...")
        json_response = self.mini_rag.get_mongodb_search_cmd_json(user_input)
        print(json_response)
        return json_response
