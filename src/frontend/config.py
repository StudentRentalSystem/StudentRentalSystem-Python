import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # MongoDB connection URI
    MONGO_URI = os.getenv("SPRING_DATA_MONGODB_URI", "mongodb://localhost:27017/student_rental")
    
    # Redis configuration
    REDIS_HOST = os.getenv("SPRING_REDIS_HOST", "localhost")
    REDIS_PORT = 6379
    
    # LLM Server configuration
    LLM_SERVER_ADDRESS = os.getenv("LLM_SERVER_ADDRESS", "http://localhost")
    LLM_SERVER_PORT = os.getenv("LLM_SERVER_PORT", "")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "llama3:8b")
    LLM_CLIENT_TOKEN = os.getenv("LLM_CLIENT_TOKEN")
    
    # Optional token for API access if required
    CLIENT_TOKEN = os.getenv("CLIENT_TOKEN")