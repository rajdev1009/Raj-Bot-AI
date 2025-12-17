from datetime import datetime

class User:
    """Structure for User Data in MongoDB"""
    def __init__(self, user_id, first_name, username):
        self.id = user_id
        self.first_name = first_name or "Unknown"
        self.username = username or "No Username"
        self.joined_at = datetime.now()
        self.is_banned = False
        self.role = "user"  # options: user, admin, vip

    def to_dict(self):
        """Converts object to dictionary for MongoDB storage"""
        return {
            "_id": self.id,
            "first_name": self.first_name,
            "username": self.username,
            "joined_at": self.joined_at,
            "is_banned": self.is_banned,
            "role": self.role
        }

class Log:
    """Structure for Activity Logs"""
    @staticmethod
    def create(user_id, action, details):
        return {
            "user_id": user_id,
            "action": action,
            "details": details,
            "timestamp": datetime.now()
        }
        
