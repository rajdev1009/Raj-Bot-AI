import motor.motor_asyncio
from config import Config
from database.models import User
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
        """Adds a new user if they don't exist."""
        try:
            user = await self.users.find_one({"_id": user_id})
            if not user:
                # Using the User Model class for structure
                new_user = User(user_id, first_name, username)
                await self.users.insert_one(new_user.to_dict())
                logger.info(f"New User Registered: {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Database Error (add_user): {e}")

    async def get_all_users(self):
        """Fetches all users for broadcast."""
        return [user async for user in self.users.find({})]

    async def log_event(self, collection_name, data):
        """Generic logger for events."""
        try:
            await self.db[collection_name].insert_one(data)
        except Exception as e:
            logger.error(f"Database Log Error: {e}")

db = Database()
