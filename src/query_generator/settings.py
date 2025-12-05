import os
from pathlib import Path
from dotenv import load_dotenv

# 載入環境變數 (會自動尋找專案根目錄的 .env)
load_dotenv()

# 定義路徑
# __file__ 是 settings.py 的位置
# parent 是 query_generator 資料夾
BASE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = BASE_DIR / "prompts"

QUERY_PROMPT_PATH = PROMPT_DIR / "query_prompt.txt"
MONGO_QUERY_PROMPT_PATH = PROMPT_DIR / "mongo_query_prompt.txt"

# 讀取環境變數設定
LLM_SERVER_ADDRESS = os.getenv("LLM_SERVER_ADDRESS", "http://localhost")
LLM_SERVER_PORT = int(os.getenv("LLM_SERVER_PORT", 11434))
LLM_MODEL_TYPE = os.getenv("LLM_MODEL_TYPE", "llama3:8b")
LLM_API_KEY = os.getenv("LLM_CLIENT_TOKEN")