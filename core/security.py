from database.mongo import db
import random
import time

user_sessions = {}

class Security:
    PASSWORD = "Rajdev9101"
    SESSION_DURATION = 3600  # 1 hour

    IMAGES = [
        "https://i.ibb.co/qFyMDRk8/IMG-20251130-WA0108-2.jpg",
        "https://i.ibb.co/wNm5kJn4/1765831046347-2.jpg",
        "https://i.ibb.co/nqXdCMsG/1762672948749-2.jpg"
    ]

    CHANNEL_NAME = "Raj HD Movies"
    CHANNEL_LINK = "https://t.me/+u4cmm3JmIrFlNzZl"

    INSTAGRAM_NAME = "@raj_dev_official"
    INSTAGRAM_LINK = "https://www.instagram.com/itz_dminem_official43"

    FACEBOOK_NAME = "Raj Dev"
    FACEBOOK_LINK = "https://www.facebook.com/share/1C794RUagn/"

    MY_INFO = (
        f"📞 **Phone:** +91 9395744401\n"
        f"📸 **Instagram:** [{INSTAGRAM_NAME}]({INSTAGRAM_LINK})\n"
        f"📘 **Facebook:** [{FACEBOOK_NAME}]({FACEBOOK_LINK})\n"
        f"📍 **Location:** Lumding, Assam"
    )

    @staticmethod
    async def check_password(user_id, text):
        if text == Security.PASSWORD:
            user_sessions[user_id] = {
                "status": "authenticated",
                "time": time.time()
            }

            caption = (
                "✅ **Access Granted! Welcome Boss.**\n\n"
                f"📺 **Channel:** [{Security.CHANNEL_NAME}]({Security.CHANNEL_LINK})\n\n"
                f"👤 **Owner Details:**\n{Security.MY_INFO}"
            )

            return True, caption, random.choice(Security.IMAGES)

        else:
            await db.log_event(
                "security_logs",
                {"user_id": user_id, "status": "failed_attempt"}
            )
            user_sessions.pop(user_id, None)
            return False, "❌ **Galat Password!**\nAccess Denied.", None

    @staticmethod
    def is_waiting(user_id):
        session = user_sessions.get(user_id)

        if not session:
            return False

        if session.get("status") == "authenticated":
            if time.time() - session["time"] < Security.SESSION_DURATION:
                return False
            else:
                user_sessions.pop(user_id, None)
                return True

        return session.get("status") == "awaiting_password"

    @staticmethod
    def initiate_auth(user_id):
        user_sessions[user_id] = {"status": "awaiting_password"}
        return (
            "🔒 **Security Check**\n\n"
            "Hidden content dekhne ke liye Password enter karein:"
        )
        
