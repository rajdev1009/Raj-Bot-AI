from database.mongo import db

user_sessions = {}

class Security:
    PASSWORD = "Rajdev9101"

    # CONFIG
    MY_IMAGE = "https://i.ibb.co/qFyMDRk8/IMG-20251130-WA0108-2.jpg"

    CHANNEL_NAME = "Raj HD Movies"
    CHANNEL_LINK = "https://t.me/+u4cmm3JmIrFlNzZl"

    INSTAGRAM_NAME = "@raj_dev_official"
    INSTAGRAM_LINK = "https://www.instagram.com/itz_dminem_official43"

    FACEBOOK_NAME = "Raj Dev"
    FACEBOOK_LINK = "https://www.facebook.com/share/1C794RUagn/"

    MY_INFO = (
        f"📞 **Phone:** +91 9395744401"
        f"📸 **Instagram:** [{INSTAGRAM_NAME}]({INSTAGRAM_LINK})\n"
        f"📘 **Facebook:** [{FACEBOOK_NAME}]({FACEBOOK_LINK})\n"
        f"📍 **Location:** Lumding, Assam"
    )

    @staticmethod
    async def check_password(user_id, text):
        if text == Security.PASSWORD:
            user_sessions.pop(user_id, None)

            caption = (
                "✅ **Access Granted! Welcome Boss.**\n\n"
                f"📺 **Channel:** [{Security.CHANNEL_NAME}]({Security.CHANNEL_LINK})\n\n"
                f"👤 **Owner Details:**\n{Security.MY_INFO}"
            )

            return True, caption, Security.MY_IMAGE

        else:
            await db.log_event(
                "security_logs",
                {"user_id": user_id, "status": "failed_attempt"}
            )
            user_sessions.pop(user_id, None)
            return False, "❌ **Galat Password!**\nAccess Denied.", None

    @staticmethod
    def is_waiting(user_id):
        return user_sessions.get(user_id) == "awaiting_password"

    @staticmethod
    def initiate_auth(user_id):
        user_sessions[user_id] = "awaiting_password"
        return (
            "🔒 **Security Check**\n\n"
            "Hidden content dekhne ke liye Password enter karein:"
        )
        
