import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MONGO_URI = os.getenv("MONGO_URI")
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    PORT = int(os.getenv("PORT", 8080))
    
    # AI Settings
    AI_COOLDOWN = 60
    SMART_DELAY = 10 
    
    # ✅ LOG CHANNEL FIX (Ye line missing thi)
    # Default 0 rakha hai taaki error na aaye agar ID na mile
    LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))
    
