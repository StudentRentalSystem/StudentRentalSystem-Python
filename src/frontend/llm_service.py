from src.query_generator.app import MiniRagApp
from src.llm_data_parser.config import LLMConfig, LLMMode
from src.frontend.config import Config

# Avoid multiple time initialized
class LLMService:
    def __init__(self):
        print(f"Initializing")
        print(f"Connecting to: {Config.LLM_SERVER_ADDRESS}:{Config.LLM_SERVER_PORT} (Model: {Config.LLM_MODEL_TYPE})")
        if Config.LLM_CLIENT_TOKEN:
            print(f"API Key Loaded:  ({Config.LLM_CLIENT_TOKEN[:4]}***)")
        else:
            print(f"API Key: Unset (如果遇到 403 錯誤，請在 settings.py 加入 LLM_API_KEY)")
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
        print("Generating database query")
        json_response = self.mini_rag.get_mongodb_search_cmd_json(user_input)
        print(json_response)
        return json_response
