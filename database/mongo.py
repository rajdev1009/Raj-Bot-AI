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
        self.cache = self.db.qa_cache  # Memory Bank
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

    # --- ADVANCED MEMORY SYSTEM ---
    
    def clean_text(self, text):
        """Text ko clean karta hai taaki matching achi ho"""
        # Sirf letters aur numbers rakho, extra space hatao, lowercase karo
        # Example: "Who is PM??" -> "who is pm"
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text) 
        return text.strip()

    async def get_cached_response(self, query):
        """Check karta hai ki ye sawal pehle save hua hai ya nahi"""
        try:
            clean_query = self.clean_text(query)
            
            # Database mein dhoondo
            result = await self.cache.find_one({"query": clean_query})
            
            if result:
                return result['answer']
            return None
        except Exception as e:
            return None

    async def save_to_cache(self, query, answer):
        """Naya jawab database mein save karta hai"""
        try:
            # Time aur Date wale sawal save MAT karna (Kyunki wo badalte rehte hain)
            ignore_words = ["time", "date", "tarikh", "samay", "baj", "aaj", "kal"]
            if any(word in query.lower() for word in ignore_words):
                return

            clean_query = self.clean_text(query)
            
            # Pehle check karo exist karta hai kya, taaki duplicate na ho
            existing = await self.cache.find_one({"query": clean_query})
            if not existing:
                await self.cache.insert_one({
                    "query": clean_query,
                    "answer": answer,
                    "timestamp": datetime.now()
                })
        except Exception as e:
            logger.error(f"Cache Save Error: {e}")

    async def log_event(self, collection_name, data):
        try:
            await self.db[collection_name].insert_one(data)
        except:
            pass

db = Database()
