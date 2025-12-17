from src.config import Config
import platform
import os


class CrawlerConfig(Config):
    @staticmethod
    def get_chrome_user_data():
        system = platform.system()
        user_home = os.path.expanduser("~")
        if system == "Windows":
            return os.path.join(user_home, "fb-crawler")
        elif system == "Darwin":  # macOS
            return os.path.join(user_home, "fb-crawler")
        elif system == "Linux":
            return os.path.join(user_home, "fb-crawler")
        else:
            raise OSError(f"Unsupported OS: {system}")

