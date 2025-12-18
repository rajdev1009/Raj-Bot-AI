import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.environ.get("API_ID", 12345))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    MONGO_URI = os.environ.get("MONGO_URI", "")
    
    # 🔑 Yahan multiple keys daal sakte ho (comma se separate karke)
    # Example: KEY1,KEY2,KEY3
    GEMINI_API_KEYS = os.environ.get("GEMINI_API_KEY", "").split(",")
    
    ADMIN_ID = int(os.environ.get("ADMIN_ID", 0))
    LOG_CHANNEL_ID = int(os.environ.get("LOG_CHANNEL_ID", 0))
    PORT = int(os.environ.get("PORT", 8080))
    SMART_DELAY = 1 
