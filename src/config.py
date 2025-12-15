import os
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

    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/student_rental")

    # Redis configuration
    REDIS_HOST = os.getenv("REDIS_URI", "localhost")
    REDIS_PORT = 6379

    # Optional token for API access if required
    CLIENT_TOKEN = os.getenv("CLIENT_TOKEN")

