import os
import platform
from dotenv import load_dotenv

load_dotenv()

class Config:
    FACEBOOK_URL = "https://www.facebook.com/"
    GROUP_URL = os.getenv("FACEBOOK_GROUP_URL")
    DB_URL = os.getenv("DB_URL", "mongodb://localhost:27017")
    DB_NAME = "app"
    DB_COLLECTION = "house_rental"
    
    LLM_SERVER_ADDRESS = os.getenv("LLM_SERVER_ADDRESS", "http://localhost")
    LLM_SERVER_PORT = os.getenv("LLM_SERVER_PORT", "")
    LLM_MODEL_TYPE = os.getenv("LLM_MODEL_TYPE", "llama3:8b")
    LLM_CLIENT_TOKEN = os.getenv("LLM_CLIENT_TOKEN", "")
    RETRY_ATTEMPTS = 1

    @staticmethod
    def get_chrome_user_data():
        system = platform.system()
        user_home = os.path.expanduser("~")
        if system == "Windows":
            return os.path.join(user_home, "fb-crawler")
        elif system == "Darwin": # macOS
            return os.path.join(user_home, "fb-crawler")
        elif system == "Linux":
            return os.path.join(user_home, "fb-crawler")
        else:
            raise OSError(f"Unsupported OS: {system}")

