import motor.motor_asyncio
from config import Config
from database.models import User
from utils.logger import logger
from datetime import datetime
import re

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client.RajBotDB
        
        # Collections
        self.users = self.db.users
        self.cache = self.db.qa_cache
        self.logs = self.db.logs

    async def add_user(self, user_id, first_name, username):
        try:
            user = await self.users.find_one({"_id": user_id})
            if not user:
                new_user = User(user_id, first_name, username)
                await self.users.insert_one(new_user.to_dict())
                logger.info(f"New User Registered: {user_id}")
                return True
            return False
        except Exception as e:
            pass

    # --- SMART MEMORY LOGIC ---
    
    def clean_text(self, text):
        """
        Query ko clean karta hai taaki 'Dev' word hatne ke baad match ho sake.
        Example: "  Who is PM?  " -> "who is pm"
        """
        text = text.lower().strip()
        
        # Agar query galti se "dev " se shuru ho rahi hai (check ke waqt), to use bhi hata do
        text = re.sub(r'^\s*dev\s+', '', text)
        
        # Special chars hatao (optional, par matching ke liye acha hai)
        # text = re.sub(r'[^\w\s]', '', text) 
        
        return text.strip()

    async def get_cached_response(self, query):
        try:
            clean_query = self.clean_text(query)
            
            # Exact Match Dhoondo
            result = await self.cache.find_one({"query": clean_query})
            
            if result:
                return result['answer']
            return None
        except Exception as e:
            return None

    async def save_to_cache(self, query, answer):
        try:
            # Query ko clean karke save karo
            clean_query = self.clean_text(query)
            
            # Duplicate Check
            existing = await self.cache.find_one({"query": clean_query})
            if not existing:
                await self.cache.insert_one({
                    "query": clean_query,
                    "answer": answer,
                    "timestamp": datetime.now()
                })
                logger.info(f"💾 Saved to Memory: {clean_query}")
        except Exception as e:
            logger.error(f"Cache Error: {e}")

    async def log_event(self, collection_name, data):
        try:
            await self.db[collection_name].insert_one(data)
        except:
            pass

db = Database()
