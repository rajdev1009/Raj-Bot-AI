import motor.motor_asyncio
from config import Config
from datetime import datetime, timedelta
from utils.logger import logger

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["RajDev_Bot"]
        self.users = self.db["users"]
        self.responses = self.db["ai_responses"]
        
        # 🧹 7-DAY AUTO CLEANUP LOGIC (TTL Index)
        # Ye line check karegi ki 'date' field se 7 din (604800 seconds) purana data khud delete ho jaye.
        asyncio.create_task(self.setup_indexes())
        logger.info("🗄️ MongoDB Connection Verified with 7-Day Auto-Cleanup!")

    async def setup_indexes(self):
        """Automatically deletes memories older than 7 days"""
        try:
            await self.responses.create_index("date", expireAfterSeconds=604800)
            logger.info("✅ 7-Day Auto-Cleanup Index Created!")
        except Exception as e:
            logger.error(f"Index Error: {e}")

    async def add_user(self, user_id, first_name, username):
        user = await self.users.find_one({"_id": user_id})
        if not user:
            await self.users.insert_one({
                "_id": user_id,
                "first_name": first_name,
                "username": username,
                "date": datetime.now()
            })

    async def get_stats(self):
        u_count = await self.users.count_documents({})
        m_count = await self.responses.count_documents({})
        return u_count, m_count

    async def get_cached_response(self, query):
        if not query: return None
        data = await self.responses.find_one({"query": query.lower().strip()})
        return data["response"] if data else None

    async def add_response(self, query, response):
        if not query or not response: return
        query = query.lower().strip()
        await self.responses.delete_many({"query": query})
        await self.responses.insert_one({
            "query": query,
            "response": response,
            "date": datetime.now() # Isi date se 7 din count honge
        })

db = Database()
