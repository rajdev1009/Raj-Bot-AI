from database.mongo import db

user_sessions = {}

class Security:
    PASSWORD = "Rajdev9101"
    
    # Aapki Details
    MY_IMAGE = "https://i.ibb.co/qFyMDRk8/IMG-20251130-WA0108-2.jpg"
    MY_CHANNEL = "https://t.me/+u4cmm3JmIrFlNzZl"
    
    # Personal Info (Yahan edit kar sakte ho)
    MY_INFO = (
        "📞 **Phone:** +91 9101xxxxxx\n"
        "📸 **Instagram:** @raj_dev_official\n"
        "📘 **Facebook:** Raj Dev\n"
        "📍 **Location:** Lumding, Assam"
    )
    
    @staticmethod
    async def check_password(user_id, text):
        if text == Security.PASSWORD:
            user_sessions.pop(user_id, None)
            
            caption = (
                f"✅ **Access Granted! Welcome Boss.**\n\n"
                f"🎬 **Movie Channel:** [Join Here]({Security.MY_CHANNEL})\n\n"
                f"👤 **Owner Details:**\n{Security.MY_INFO}"
            )
            return True, caption, Security.MY_IMAGE
        else:
            await db.log_event("security_logs", {"user_id": user_id, "status": "failed_attempt"})
            user_sessions.pop(user_id, None)
            return False, "❌ **Galat Password!**\nDobara koshish mat karna varna Ban ho jaoge.", None

    @staticmethod
    def is_waiting(user_id):
        return user_sessions.get(user_id) == "awaiting_password"

    @staticmethod
    def initiate_auth(user_id):
        user_sessions[user_id] = "awaiting_password"
        return "🔒 **Security Check**\n\nHidden content dekhne ke liye Password enter karein:"
        
