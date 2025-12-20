import motor.motor_asyncio
from config import Config
from datetime import datetime
from utils.logger import logger

class Database:
    def __init__(self):
        # 👇 FIX: Ye check karega ki Config me 'URI' hai ya 'URL'
        # Jo bhi milega use le lega, taaki 'AttributeError' na aaye
        self.mongo_url = getattr(Config, "MONGO_URI", getattr(Config, "MONGO_URL", None))

        if not self.mongo_url:
            logger.error("❌ CRITICAL ERROR: Config file mein MONGO_URI ya MONGO_URL nahi mila!")
            return

        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.mongo_url)
            self.db = self.client["RajDev_Bot"]
            self.users = self.db["users"]
            self.responses = self.db["ai_responses"]
            logger.info("🗄️ MongoDB Connection Verified!")
        except Exception as e:
            logger.error(f"❌ MongoDB Connection Failed: {e}")

    async def add_user(self, user_id, first_name, username):
        try:
            user = await self.users.find_one({"_id": user_id})
            if not user:
                await self.users.insert_one({
                    "_id": user_id,
                    "first_name": first_name,
                    "username": username,
                    "date": datetime.now()
                })
        except Exception as e:
            logger.error(f"Error adding user: {e}")

    async def get_stats(self):
        """Bot ki report card deta hai"""
        try:
            u_count = await self.users.count_documents({})
            m_count = await self.responses.count_documents({})
            return u_count, m_count
        except:
            return 0, 0

    async def get_all_users(self):
        return await self.users.find({}).to_list(length=None)

    async def get_cached_response(self, query):
        if not query: return None
        try:
            data = await self.responses.find_one({"query": query.lower().strip()})
            return data["response"] if data else None
        except:
            return None

    async def add_response(self, query, response):
        if not query or not response: return
        try:
            query = query.lower().strip()
            # Purana delete karo taaki duplicate na ho
            await self.responses.delete_many({"query": query})
            # Naya save karo
            await self.responses.insert_one({
                "query": query,
                "response": response,
                "date": datetime.now()
            })
        except Exception as e:
            logger.error(f"Error saving memory: {e}")

db = Database()
