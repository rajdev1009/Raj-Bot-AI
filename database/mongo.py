import motor.motor_asyncio
from config import Config
from database.models import User, Log  # <--- Imported Models
from utils.logger import logger

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client.RajBotDB
        
        self.users = self.db.users
        self.logs = self.db.logs

    async def add_user(self, user_id, first_name, username):
        user = await self.users.find_one({"_id": user_id})
        if not user:
            # Using the Model here
            new_user = User(user_id, first_name, username)
            await self.users.insert_one(new_user.to_dict())
            logger.info(f"New User Registered: {user_id}")

    async def get_all_users(self):
        return [user async for user in self.users.find({})]

    async def log_event(self, collection_name, data):
        # Generic logger
        await self.db[collection_name].insert_one(data)

db = Database()
