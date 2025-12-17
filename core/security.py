from database.mongo import db

user_sessions = {}

class Security:
    PASSWORD = "Rajdev9101"
    
    # ✅ CONFIG: Yahan apni details set karein
    MY_IMAGE = "https://i.ibb.co/qFyMDRk8/IMG-20251130-WA0108-2.jpg"
    CHANNEL_NAME = "Raj HD Movies"  # <--- Ye ab dikhega
    CHANNEL_LINK = "https://t.me/+u4cmm3JmIrFlNzZl"
    
    # Personal Info
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
            
            # ✅ UPDATED: Message Format with Channel Name
            caption = (
                f"✅ **Access Granted! Welcome Boss.**\n\n"
                f"📺 **Channel:** {Security.CHANNEL_NAME}\n"
                f"🔗 **Link:** [Join Here]({Security.CHANNEL_LINK})\n\n"
                f"👤 **Owner Details:**\n{Security.MY_INFO}"
            )
            return True, caption, Security.MY_IMAGE
        else:
            await db.log_event("security_logs", {"user_id": user_id, "status": "failed_attempt"})
            user_sessions.pop(user_id, None)
            return False, "❌ **Galat Password!**\nAccess Denied.", None

    @staticmethod
    def is_waiting(user_id):
        return user_sessions.get(user_id) == "awaiting_password"

    @staticmethod
    def initiate_auth(user_id):
        user_sessions[user_id] = "awaiting_password"
        return "🔒 **Security Check**\n\nHidden content dekhne ke liye Password enter karein:"
        
