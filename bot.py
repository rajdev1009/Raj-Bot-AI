import asyncio
import os
from datetime import datetime
from pyrogram import Client, filters, idle, enums
from pyrogram.enums import ChatAction, ChatType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import Config
from database.mongo import db
from core.ai_engine import ai_engine
from core.voice_engine import voice_engine
from core.image_engine import image_engine
from core.broadcast import broadcast_message
from core.security import Security
from utils.logger import logger
from utils.server import start_server

# --- 🎨 STARTUP LOGO (RAJ DEV SPECIAL) ---
LOGO = r"""
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
 ▓                                                                          ▓
▓   ██████╗   █████╗     ██████╗ ███████╗ ██╗    ██╗  ▓
 ▓  ██╔══██╗██╔══██╗     ██╔═██╗██╔═══╝  ██║   ██║   ▓
▓   ██████╔╝███████║     ██║  ██║█████╗   ██║   ██║   ▓
 ▓  ██╔══██╗██╔══██║     ██║  ██║██╔══╝  ╚██╗ ██╔    ▓
▓   ██║    ██║██║  ██║   ██████╔╝███████╗ ╚████╔╝    ▓
 ▓                                                                           ▓
▓   CORE ACTIVATED | DEVELOPED BY RAJ DEV | 2025                             ▓
▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓
"""

# --- 🤖 BOT INITIALIZATION ---
app = Client(
    "RajBot_Session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# --- 🎚️ GLOBAL SETTINGS ---
SETTINGS = {
    "group_auto_reply": False  # Admin can toggle this via /mode
}

# --- 📝 ADVANCED LOGGING SYSTEM ---
async def log_conversation(client, message, bot_reply):
    """Logs conversation to Console and Telegram Log Channel with error protection."""
    try:
        user = message.from_user
        if not user: return
        
        chat_text = message.text or "[Media/Voice]"
        chat_type = "Private" if message.chat.type == ChatType.PRIVATE else f"Group ({message.chat.title})"
        
        # 1. Console Log
        logger.info(f"📩 [{chat_type}] {user.first_name}: {chat_text}")
        
        # 2. Telegram Log Channel
        if Config.LOG_CHANNEL_ID:
            log_text = (
                f"**#New_Chat_Log** 📝\n\n"
                f"👤 **User:** {user.mention} (`{user.id}`)\n"
                f"📍 **Source:** {chat_type}\n"
                f"📥 **Message:**\n{chat_text}\n\n"
                f"🤖 **Bot Reply:**\n{bot_reply}"
            )
            try:
                await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except Exception as e:
                logger.warning(f"Log Channel Error: {e}")
    except Exception as e:
        logger.error(f"Main Logging Error: {e}")

# --- 🎮 COMMAND HANDLERS ---

@app.on_message(filters.command("mode") & filters.user(Config.ADMIN_ID))
async def mode_switch_handler(client, message):
    try:
        if len(message.command) < 2:
            status = "✅ ON" if SETTINGS["group_auto_reply"] else "❌ OFF"
            return await message.reply_text(f"🎚️ **Group Mode:** {status}\nUse: `/mode on` or `/mode off`")
        
        action = message.command[1].lower()
        if action == "on":
            SETTINGS["group_auto_reply"] = True
            await message.reply_text("🔔 **Group Mode: ON**\nMain groups mein sabse baat karunga.")
        elif action == "off":
            SETTINGS["group_auto_reply"] = False
            await message.reply_text("🔕 **Group Mode: OFF**\nMain groups mein sirf 'Dev' sununga.")
    except Exception as e:
        logger.error(f"Mode Command Error: {e}")

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    if not message.from_user: return
    try:
        user = message.from_user
        await db.add_user(user.id, user.first_name, user.username)
        
        welcome_text = (
            f"**Namaste {user.mention}!** 🙏\n"
            f"Main Raj Dev ka AI Assistant hu (Dev).\n\n"
            f"Mera dimaag Gemini 2.5 Flash se chalta hai. "
            f"Kuch bhi puchna ho to message mein **'Dev'** zaroor lagana."
        )
        await message.reply_text(welcome_text)
    except Exception as e:
        logger.error(f"Start Handler Error: {e}")

@app.on_message(filters.command(["image", "img"]))
async def image_gen_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Likho: /img <kya chahiye>")
    
    prompt = message.text.split(None, 1)[1]
    msg = await message.reply("🎨 Painting bana raha hu, thoda ruko...")
    
    try:
        image_url = await image_engine.generate_image_url(prompt)
        if image_url:
            await message.reply_photo(photo=image_url, caption=f"**Prompt:** {prompt}\n**By:** Raj AI")
            await log_conversation(client, message, f"Generated Image: {prompt}")
        else:
            await message.reply("❌ Error: Image nahi ban payi.")
    except Exception as e:
        logger.error(f"Image Logic Error: {e}")
        await message.reply("Technical issue aa gaya.")
    finally:
        await msg.delete()

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def broadcast_handler(client, message):
    msg = await message.reply_text("📢 Broadcast shuru ho raha hai...")
    sent, failed = await broadcast_message(client, message.reply_to_message)
    await msg.edit_text(f"✅ **Broadcast Finished**\n\nSent: {sent}\nFailed: {failed}")

# --- 🧠 MAIN CHAT LOGIC (PRIORITY BASED) ---

@app.on_message(filters.text & ~filters.command(["start", "image", "img", "broadcast", "mode"]))
async def text_handler(client, message):
    if not message.from_user: return
    
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    is_pvt = message.chat.type == ChatType.PRIVATE
    
    # Speaker Button UI
    speaker_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])

    # 1. SECURITY SYSTEM (Only in Private)
    if is_pvt:
        if text_lower == "raj":
            if not Security.is_waiting(user_id):
                return await message.reply(Security.initiate_auth(user_id))
        
        if Security.is_waiting(user_id):
            success, response, photo_url = await Security.check_password(user_id, text)
            if photo_url: await message.reply_photo(photo=photo_url, caption=response)
            else: await message.reply(response)
            await log_conversation(client, message, f"Security Attempt: {success}")
            return

    # 🧹 Clean Text for DB Match
    clean_text = text_lower.replace("dev", "").strip()

    # 2. DATABASE MEMORY (Priority #1)
    # Sabse pehle check karo ki kya ye pehle pucha gaya hai?
    cached_ans = await db.get_cached_response(clean_text)
    if cached_ans:
        await message.reply_text(cached_ans, reply_markup=speaker_btn)
        return

    # 3. AI ENGINE (Priority #2 - Triggered by 'Dev')
    if "dev" in text_lower:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        # AI se jawab mangao
        ai_response = await ai_engine.get_response(user_id, text)
        
        if ai_response:
            # ✅ SAVE TO MEMORY: Agli baar ke liye yaad rakho
            try:
                await db.add_response(clean_text, ai_response)
            except Exception as db_e:
                logger.error(f"Memory Save Error: {db_e}")
                
            await message.reply_text(ai_response, reply_markup=speaker_btn)
            await log_conversation(client, message, ai_response)
        else:
            if is_pvt: await message.reply_text("Network issue hai, wapas pucho.")
        return

    # 4. JSON RESPONSES (Priority #3 - Fallback for Greetings)
    if is_pvt or SETTINGS["group_auto_reply"]:
        # Chote messages (Hi, Hello) ke liye fast JSON reply
        json_reply = ai_engine.get_json_reply(text)
        if json_reply:
            await asyncio.sleep(0.5)
            await message.reply_text(json_reply, reply_markup=speaker_btn)
            await log_conversation(client, message, json_reply)
            return

# --- 🔊 CALLBACK: TEXT TO SPEECH ---

@app.on_callback_query(filters.regex("speak_msg"))
async def speak_callback_handler(client, callback_query: CallbackQuery):
    await callback_query.answer("🔊 Generating Audio...", show_alert=False)
    text_to_speak = callback_query.message.text or callback_query.message.caption
    
    if not text_to_speak: return
    
    try:
        audio_path = await voice_engine.text_to_speech(text_to_speak)
        if audio_path:
            await client.send_voice(chat_id=callback_query.message.chat.id, voice=audio_path)
            if os.path.exists(audio_path): os.remove(audio_path)
    except Exception as e:
        logger.error(f"TTS Button Error: {e}")
        await callback_query.answer("❌ Audio Error.", show_alert=True)

# --- 🎤 VOICE MESSAGE HANDLER ---

@app.on_message(filters.voice)
async def voice_message_handler(client, message):
    msg = await message.reply("🎤 Sun raha hu, thoda sabr karo...")
    try:
        file_path = await message.download()
        text_response = await voice_engine.voice_to_text_and_reply(file_path)
        
        await msg.edit_text(
            f"🤖 **Dev Says:**\n{text_response}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])
        )
        await log_conversation(client, message, f"Voice Reply: {text_response}")
        if os.path.exists(file_path): os.remove(file_path)
    except Exception as e:
        logger.error(f"Voice Processor Error: {e}")
        await msg.edit_text("❌ Awaz samajh nahi aayi.")

# --- 🚀 STARTUP SEQUENCE ---

async def main():
    # 1. Print Logo in Console
    print(LOGO)
    
    # 2. Start Koyeb Health Check Server
    try:
        await start_server()
    except Exception as e:
        logger.warning(f"Server Startup Warning: {e}")
    
    logger.info("🚀 Raj Bot (Advanced Version) is starting...")
    
    # 3. Start Bot Client
    await app.start()
    
    # 4. Notify Log Channel
    if Config.LOG_CHANNEL_ID:
        try:
            await app.send_message(
                Config.LOG_CHANNEL_ID,
                f"✅ **Core Activated | Version 2.0**\n\n```\n{LOGO}\n```"
            )
        except Exception as e:
            logger.warning(f"Initial Log Channel Notification Failed: {e}")
    
    # 5. Keep running
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
 
