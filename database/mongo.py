import motor.motor_asyncio
from config import Config
from datetime import datetime

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client["RajDev_Bot"]
        self.users = self.db["users"]
        self.responses = self.db["ai_responses"]

    async def add_user(self, user_id, first_name, username):
        user = await self.users.find_one({"_id": user_id})
        if not user:
            return await self.users.insert_one({
                "_id": user_id,
                "first_name": first_name,
                "username": username,
                "date": datetime.now()
            })

    async def get_all_users(self):
        users_list = []
        async for user in self.users.find({}):
            users_list.append(user)
        return users_list

    # --- 🧠 SMART MEMORY FUNCTIONS ---

    async def get_cached_response(self, query):
        """Database se purana jawab dhoondta hai"""
        data = await self.responses.find_one({"query": query.lower().strip()})
        return data["response"] if data else None

    async def add_response(self, query, response):
        """AI ka naya jawab save karta hai"""
        query = query.lower().strip()
        # Purana data delete karo agar same sawal hai
        await self.responses.delete_many({"query": query})
        # Naya data insert karo
        await self.responses.insert_one({
            "query": query,
            "response": response,
            "date": datetime.now()
        })

db = Database()
