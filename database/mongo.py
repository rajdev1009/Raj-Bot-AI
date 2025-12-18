import motor.motor_asyncio
from config import Config
from datetime import datetime
from utils.logger import logger

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["RajDev_Bot"]
        self.users = self.db["users"]
        self.responses = self.db["ai_responses"]
        logger.info("🗄️ MongoDB Connection Established!")

    async def add_user(self, user_id, first_name, username):
        """User ko database mein save karta hai agar wo naya hai."""
        user = await self.users.find_one({"_id": user_id})
        if not user:
            return await self.users.insert_one({
                "_id": user_id,
                "first_name": first_name,
                "username": username,
                "date": datetime.now()
            })

    async def get_all_users(self):
        """Broadcast ke liye sare users ki list laata hai."""
        return await self.users.find({}).to_list(length=None)

    async def get_cached_response(self, query):
        """
        Pehle se save kiya hua jawab dhoondta hai.
        Query ko lower aur strip karke match karta hai.
        """
        if not query: return None
        data = await self.responses.find_one({"query": query.lower().strip()})
        if data:
            logger.info(f"🧠 Memory Match Found: {query}")
            return data["response"]
        return None

    async def add_response(self, query, response):
        """
        AI ke naye jawab ko memory mein save karta hai.
        Purane duplicate messages ko delete kar deta hai.
        """
        if not query or not response: return
        query = query.lower().strip()
        try:
            await self.responses.delete_many({"query": query})
            await self.responses.insert_one({
                "query": query,
                "response": response,
                "date": datetime.now()
            })
            logger.info(f"💾 Saved to Memory: {query}")
        except Exception as e:
            logger.error(f"❌ DB Save Error: {e}")

db = Database()
