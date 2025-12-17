import motor.motor_asyncio
from config import Config
from datetime import datetime
from utils.logger import logger

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db = self.client.RajBotDB
        
        # Collections
        self.users = self.db.users
        self.chats = self.db.chats
        self.voice_logs = self.db.voice_logs
        self.image_logs = self.db.image_logs
        self.broadcast_logs = self.db.broadcast_logs
        self.security_logs = self.db.security_logs

    async def add_user(self, user_id, first_name, username):
        user = await self.users.find_one({"_id": user_id})
        if not user:
            await self.users.insert_one({
                "_id": user_id,
                "first_name": first_name,
                "username": username,
                "joined_at": datetime.now()
            })
            logger.info(f"New User Registered: {user_id}")

    async def get_all_users(self):
        return [user async for user in self.users.find({})]

    async def log_event(self, collection_name, data):
        collection = getattr(self, collection_name)
        data['timestamp'] = datetime.now()
        await collection.insert_one(data)

db = Database()
