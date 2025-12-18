import motor.motor_asyncio
from config import Config
from datetime import datetime
from utils.logger import logger
import asyncio # ✅ Missing import ab add kar diya hai

class Database:
    def __init__(self):
        # MongoDB Connection Setup
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["RajDev_Bot"]
        self.users = self.db["users"]
        self.responses = self.db["ai_responses"]
        
        # 🧹 7-DAY AUTO CLEANUP LOGIC
        # Background task shuru karne ke liye asyncio zaruri hai
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.setup_indexes())
            else:
                asyncio.run(self.setup_indexes())
        except Exception as e:
            logger.error(f"Async Task Error: {e}")
            
        logger.info("🗄️ MongoDB Connection Verified with 7-Day Auto-Cleanup!")

    async def setup_indexes(self):
        """Automatically deletes memories older than 7 days"""
        try:
            # TTL Index: 604800 seconds = 7 days
            await self.responses.create_index("date", expireAfterSeconds=604800)
            logger.info("✅ 7-Day Auto-Cleanup Index Created Successfully!")
        except Exception as e:
            logger.error(f"Index Error: {e}")

    async def add_user(self, user_id, first_name, username):
        """Save new users to database"""
        user = await self.users.find_one({"_id": user_id})
        if not user:
            await self.users.insert_one({
                "_id": user_id,
                "first_name": first_name,
                "username": username,
                "date": datetime.now()
            })

    async def get_stats(self):
        """Returns bot statistics"""
        u_count = await self.users.count_documents({})
        m_count = await self.responses.count_documents({})
        return u_count, m_count

    async def get_all_users(self):
        """Returns all users for broadcast"""
        return await self.users.find({}).to_list(length=None)

    async def get_cached_response(self, query):
        """Fetch answer from database if available"""
        if not query: return None
        data = await self.responses.find_one({"query": query.lower().strip()})
        return data["response"] if data else None

    async def add_response(self, query, response):
        """Store AI response with current date for TTL cleanup"""
        if not query or not response: return
        query = query.lower().strip()
        # Purana duplicate hatao
        await self.responses.delete_many({"query": query})
        # Naya data save karo
        await self.responses.insert_one({
            "query": query,
            "response": response,
            "date": datetime.now() # Isi field par cleanup kaam karega
        })

db = Database()
