import os
from pathlib import Path

from src.config import Config

BASE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = BASE_DIR / "prompts"

QUERY_PROMPT_PATH = PROMPT_DIR / "query_prompt.txt"
MONGO_QUERY_PROMPT_PATH = PROMPT_DIR / "mongo_query_prompt.txt"


LLM_SERVER_ADDRESS = Config.LLM_SERVER_ADDRESS
LLM_SERVER_PORT = Config.LLM_SERVER_PORT
LLM_MODEL_TYPE = Config.LLM_MODEL_TYPE
LLM_CLIENT_TOKEN = Config.LLM_CLIENT_TOKEN