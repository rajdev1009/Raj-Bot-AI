import time
from config import Config

class RateLimiter:
    def __init__(self):
        self._users = {}

    def can_use_ai(self, user_id):
        """Returns True if user can use AI (once per minute rule)."""
        current_time = time.time()
        last_time = self._users.get(user_id, 0)
        
        if current_time - last_time > Config.AI_COOLDOWN:
            self._users[user_id] = current_time
            return True
        return False

    def get_remaining_time(self, user_id):
        current_time = time.time()
        last_time = self._users.get(user_id, 0)
        diff = current_time - last_time
        return max(0, Config.AI_COOLDOWN - diff)

limiter = RateLimiter()
