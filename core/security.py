from database.mongo import db

# In-memory session state for password flow
# {user_id: "awaiting_password"}
user_sessions = {}

class Security:
    PASSWORD = "Rajdev9101"
    
    @staticmethod
    async def check_password(user_id, text):
        if text == Security.PASSWORD:
            user_sessions.pop(user_id, None)
            return True, "✅ **Access Granted**\n\nMovies: @Raj_HD_movies\nServer: Lumding HQ"
        else:
            await db.log_event("security_logs", {"user_id": user_id, "status": "failed_attempt"})
            user_sessions.pop(user_id, None)
            return False, "❌ **Access Denied**\nAttempt logged."

    @staticmethod
    def is_waiting(user_id):
        return user_sessions.get(user_id) == "awaiting_password"

    @staticmethod
    def initiate_auth(user_id):
        user_sessions[user_id] = "awaiting_password"
        return "🔒 **Security Check**\n\nEnter the password to access hidden content:"
      
