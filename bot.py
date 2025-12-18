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

# --- 🎨 STARTUP LOGO ---
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

app = Client(
    "RajBot_Session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# --- 🎚️ SETTINGS ---
SETTINGS = {
    "group_auto_reply": False
}

# --- HELPER: LOGGING ---
async def log_conversation(client, message, bot_reply):
    try:
        user = message.from_user
        chat_text = message.text or "[Media/Sticker]"
        chat_type = "Private" if message.chat.type == ChatType.PRIVATE else "Group"
        
        logger.info(f"📩 [{chat_type}] {user.first_name}: {chat_text}")
        
        if Config.LOG_CHANNEL_ID:
            log_text = (
                f"**#New_Chat_Log** 📝\n"
                f"SOURCE: {chat_type}\n"
                f"👤 **User:** {user.mention} (`{user.id}`)\n"
                f"📥 **Message:**\n{chat_text}\n"
                f"🤖 **Bot Reply:**\n{bot_reply}"
            )
            try: await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except: pass
    except: pass

# --- COMMANDS ---

@app.on_message(filters.command("mode") & filters.user(Config.ADMIN_ID))
async def mode_switch_handler(client, message):
    try:
        if len(message.command) < 2:
            status = "✅ ON" if SETTINGS["group_auto_reply"] else "❌ OFF"
            return await message.reply_text(f"🎚️ **Group Auto-Reply:** {status}")
        
        action = message.command[1].lower()
        if action == "on":
            SETTINGS["group_auto_reply"] = True
            await message.reply_text("🔔 **Group Mode: ON** (Sabse baat karunga).")
        elif action == "off":
            SETTINGS["group_auto_reply"] = False
            await message.reply_text("🔕 **Group Mode: OFF** (Sirf 'Dev' sununga).")
    except: pass

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    try:
        user = message.from_user
        await db.add_user(user.id, user.first_name, user.username)
        if message.chat.type != ChatType.PRIVATE:
            return await message.reply_text("Namaste! Main Raj ka AI Assistant hu.")
        await message.reply_text(f"**Namaste {user.mention}!** 🙏\nMain Raj ka AI Assistant hu (Dev).")
    except: pass

@app.on_message(filters.command(["image", "img"]))
async def image_gen_handler(client, message):
    try:
        if len(message.command) < 2: return await message.reply("Likho: /img <kya chahiye>")
        prompt = message.text.split(None, 1)[1]
        msg = await message.reply("🎨 Painting...")
        image_url = await image_engine.generate_image_url(prompt)
        if image_url:
            await message.reply_photo(photo=image_url, caption=f"Ye lo: {prompt}")
            await log_conversation(client, message, f"Image: {prompt}")
        else: await message.reply("Server busy.")
        await msg.delete()
    except: pass

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def broadcast_handler(client, message):
    msg = await message.reply_text("📢 Sending...")
    sent, failed = await broadcast_message(client, message.reply_to_message)
    await msg.edit_text(f"✅ Sent: {sent} | Failed: {failed}")

# --- MAIN CHAT LOGIC (PRIORITY FIXED) ---

@app.on_message(filters.text & ~filters.command(["start", "image", "img", "broadcast", "mode"]))
async def text_handler(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    is_private = message.chat.type == ChatType.PRIVATE
    
    speaker_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])

    # 🛑 1. SECURITY (Sabse Pehle)
    if is_private:
        if text_lower == "raj":
            if not Security.is_waiting(user_id):
                return await message.reply(Security.initiate_auth(user_id))
        
        if Security.is_waiting(user_id):
            success, response, photo_url = await Security.check_password(user_id, text)
            if photo_url: await message.reply_photo(photo=photo_url, caption=response)
            else: await message.reply(response)
            await log_conversation(client, message, f"Security: {success}")
            return

    # 🧠 2. DATABASE MEMORY (User requested Priority: DB First)
    # Pehle bina "Dev" hataye check karo
    cached_ans = await db.get_cached_response(text)
    
    # Agar nahi mila, to "Dev" hata kar check karo (Smart Search)
    if not cached_ans:
        clean_text = text_lower.replace("dev", "").strip()
        if clean_text:
            cached_ans = await db.get_cached_response(clean_text)
    
    if cached_ans:
        # Agar DB mein hai, to yahin se reply kardo aur RETURN kardo.
        await message.reply_text(cached_ans, reply_markup=speaker_btn)
        await log_conversation(client, message, cached_ans)
        return

    # 🤖 3. AI CHECK (Sirf tab jab "Dev" ho)
    if "dev" in text_lower:
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        if Config.SMART_DELAY > 0: await asyncio.sleep(Config.SMART_DELAY)
            
        ai_response = await ai_engine.get_response(user_id, text)
        
        if ai_response:
            await message.reply_text(ai_response, reply_markup=speaker_btn)
            await log_conversation(client, message, ai_response)
        else:
            if is_private: await message.reply_text("Abhi busy hu (AI Error).")
        
        # ⚠️ IMPORTANT: Agar "Dev" bola hai, to JSON check MAT karo. Yahi ruk jao.
        return

    # 📜 4. JSON GREETINGS (Last Option - Only if NO "Dev")
    should_reply_json = is_private or SETTINGS["group_auto_reply"]
    
    if should_reply_json:
        json_reply = ai_engine.get_json_reply(text)
        if json_reply:
            await asyncio.sleep(0.5)
            await message.reply_text(json_reply, reply_markup=speaker_btn)
            await log_conversation(client, message, json_reply)
            return

# --- SPEAKER CALLBACK ---
@app.on_callback_query(filters.regex("speak_msg"))
async def speak_callback_handler(client, callback_query: CallbackQuery):
    await callback_query.answer("🔊 Audio...", show_alert=False)
    text_to_speak = callback_query.message.text or callback_query.message.caption
    if not text_to_speak: return
    try:
        audio_path = await voice_engine.text_to_speech(text_to_speak)
        if audio_path:
            await client.send_voice(chat_id=callback_query.message.chat.id, voice=audio_path)
            if os.path.exists(audio_path): os.remove(audio_path)
    except: await callback_query.answer("❌ Error.", show_alert=True)

@app.on_message(filters.voice)
async def voice_handler(client, message):
    msg = await message.reply("🎤 Sun raha hu...")
    file_path = await message.download()
    text_resp = await voice_engine.voice_to_text_and_reply(file_path)
    speaker_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])
    await msg.edit_text(f"🤖: {text_resp}", reply_markup=speaker_btn)
    await log_conversation(client, message, f"Voice: {text_resp}")
    if os.path.exists(file_path): os.remove(file_path)

# --- STARTUP ---
async def main():
    print(LOGO)
    try: await start_server()
    except: pass
    logger.info("🚀 Raj Bot (Priority Fixed) Starting...")
    await app.start()
    if Config.LOG_CHANNEL_ID:
        try: await app.send_message(Config.LOG_CHANNEL_ID, f"✅ **Bot Online!**\n\n```\n{LOGO}\n```")
        except: pass
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
