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

# --- 🎨 STARTUP LOGO (Raj Dev Special) ---
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
# Default: Group mein Auto-Reply OFF (Spam rokne ke liye)
SETTINGS = {
    "group_auto_reply": False
}

# --- 📝 HELPER FUNCTION: LOGGING ---
async def log_conversation(client, message, bot_reply):
    """
    Ye function chat ko Console aur Telegram Channel dono jagah log karta hai.
    """
    try:
        user = message.from_user
        chat_text = message.text or "[Media/Sticker]"
        chat_type = "Private" if message.chat.type == ChatType.PRIVATE else "Group"
        
        # 1. Console Log (Koyeb Dashboard)
        logger.info(f"📩 [{chat_type}] {user.first_name}: {chat_text}")
        
        # 2. Telegram Log Channel
        if Config.LOG_CHANNEL_ID:
            log_text = (
                f"**#New_Chat_Log** 📝\n"
                f"SOURCE: {chat_type}\n"
                f"👤 **User:** {user.mention} (`{user.id}`)\n"
                f"📥 **Message:**\n{chat_text}\n"
                f"🤖 **Bot Reply:**\n{bot_reply}"
            )
            try:
                await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except Exception as e:
                # Agar bot channel me nahi hai to crash nahi hoga
                pass
    except Exception as e:
        logger.error(f"Logging Error: {e}")

# --- 🎮 COMMAND HANDLERS ---

@app.on_message(filters.command("mode") & filters.user(Config.ADMIN_ID))
async def mode_switch_handler(client, message):
    """
    Admin Command: Group Auto-Reply ON/OFF karne ke liye.
    """
    try:
        if len(message.command) < 2:
            status = "✅ ON" if SETTINGS["group_auto_reply"] else "❌ OFF"
            return await message.reply_text(
                f"🎚️ **Current Group Mode:** {status}\n\n"
                f"Likho: `/mode on` (Sabse baat karega)\n"
                f"Likho: `/mode off` (Sirf 'Dev' bolne par bolega)"
            )
        
        action = message.command[1].lower()
        
        if action == "on":
            SETTINGS["group_auto_reply"] = True
            await message.reply_text("🔔 **Group Mode: ON**\nAb main Groups mein 'Hi/Hello' ka bhi jawab dunga.")
        elif action == "off":
            SETTINGS["group_auto_reply"] = False
            await message.reply_text("🔕 **Group Mode: OFF**\nAb main Groups mein shant rahunga (Sirf 'Dev' sununga).")
        else:
            await message.reply_text("Galat command. Likho `/mode on` ya `/mode off`")
            
    except Exception as e:
        logger.error(f"Mode Error: {e}")

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    try:
        user = message.from_user
        # User ko Database mein add karo
        await db.add_user(user.id, user.first_name, user.username)
        
        # Group aur Private ke liye alag welcome message
        if message.chat.type != ChatType.PRIVATE:
            await message.reply_text("Namaste! Main Raj ka AI Assistant hu. 'Dev' bolkar kuch bhi pucho.")
            return

        await message.reply_text(
            f"**Namaste {user.mention}!** 🙏\n"
            f"Main Raj ka Personal Assistant hu (Dev).\n\n"
            f"Agar jawab pata hoga to turant dunga, nahi to **'Dev'** laga kar puchna."
        )
    except Exception as e:
        logger.error(f"Start Error: {e}")

@app.on_message(filters.command(["image", "img"]))
async def image_gen_handler(client, message):
    try:
        if len(message.command) < 2:
            return await message.reply("Likho: /img <kya chahiye>")
        
        prompt = message.text.split(None, 1)[1]
        msg = await message.reply("🎨 Painting bana raha hu...")
        
        image_url = await image_engine.generate_image_url(prompt)
        
        if image_url:
            await message.reply_photo(photo=image_url, caption=f"Ye lo: {prompt}")
            await log_conversation(client, message, f"Image Created: {prompt}")
        else:
            await message.reply("Server busy hai, image nahi bani.")
        
        await msg.delete()
    except Exception as e:
        logger.error(f"Image Error: {e}")
        await message.reply("Error aa gaya.")

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def broadcast_handler(client, message):
    msg = await message.reply_text("📢 Broadcast shuru...")
    sent, failed = await broadcast_message(client, message.reply_to_message)
    await msg.edit_text(f"✅ Ho gaya\nSent: {sent}\nFailed: {failed}")

# --- 🧠 MAIN CHAT LOGIC (THE BRAIN) ---

@app.on_message(filters.text & ~filters.command(["start", "image", "img", "broadcast", "mode"]))
async def text_handler(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    is_private = message.chat.type == ChatType.PRIVATE
    
    speaker_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])

    # 🛑 1. SECURITY CHECK (Sirf Private Chat mein)
    if is_private:
        if text_lower == "raj":
            if not Security.is_waiting(user_id):
                return await message.reply(Security.initiate_auth(user_id))
        
        if Security.is_waiting(user_id):
            success, response, photo_url = await Security.check_password(user_id, text)
            if photo_url:
                await message.reply_photo(photo=photo_url, caption=response)
            else:
                await message.reply(response)
            await log_conversation(client, message, f"Security Attempt: {success}")
            return

    # 🧹 SMART TEXT CLEANING
    # "Dev" hata kar clean text banate hain taaki database mein search kar sakein
    clean_text = text_lower.replace("dev", "").strip()
    
    # 💾 2. DATABASE MEMORY CHECK (Priority #1)
    # Pehle check karo kya ye sawal pehle pucha gaya hai?
    cached_ans = await db.get_cached_response(clean_text)
    
    if cached_ans:
        # Agar DB mein mil gaya, to wahi se jawab do aur ruk jao.
        await message.reply_text(cached_ans, reply_markup=speaker_btn)
        # Optional: DB response ko log karna hai to uncomment karo
        # await log_conversation(client, message, f"[DB Memory] {cached_ans}")
        return

    # 🤖 3. AI CHECK (Priority #2 - Only if "Dev" is present)
    if "dev" in text_lower:
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        if Config.SMART_DELAY > 0:
            await asyncio.sleep(Config.SMART_DELAY)
            
        ai_response = await ai_engine.get_response(user_id, text)
        
        if ai_response:
            # ✅ MEMORY SAVE: AI ke jawab ko Database mein save karo
            # Taaki agli baar bina "Dev" ke bhi jawab mil jaye
            if clean_text:
                await db.add_response(clean_text, ai_response)
                
            await message.reply_text(ai_response, reply_markup=speaker_btn)
            await log_conversation(client, message, ai_response)
        else:
            if is_private:
                await message.reply_text("Abhi busy hu, baad mein puchna.")
        
        # Agar "Dev" bola tha, to yahi ruk jao. JSON check mat karo.
        return

    # 📜 4. JSON GREETINGS (Priority #3 - Low Priority)
    # Ye tabhi chalega jab:
    # 1. Message Private ho, YA
    # 2. Group mein Mode ON ho.
    should_reply_json = is_private or SETTINGS["group_auto_reply"]
    
    if should_reply_json:
        # AI Engine ke andar logic hai jo lambe sentences ko ignore karega
        json_reply = ai_engine.get_json_reply(text)
        if json_reply:
            await asyncio.sleep(0.5)
            await message.reply_text(json_reply, reply_markup=speaker_btn)
            await log_conversation(client, message, json_reply)
            return

# --- 🔊 SPEAKER CALLBACK HANDLER ---

@app.on_callback_query(filters.regex("speak_msg"))
async def speak_callback_handler(client, callback_query: CallbackQuery):
    await callback_query.answer("🔊 Audio generate ho raha hai...", show_alert=False)
    
    text_to_speak = callback_query.message.text or callback_query.message.caption
    
    if not text_to_speak:
        await callback_query.answer("❌ Bolne ke liye kuch nahi mila.", show_alert=True)
        return

    try:
        audio_path = await voice_engine.text_to_speech(text_to_speak)
        
        if audio_path:
            await client.send_voice(
                chat_id=callback_query.message.chat.id,
                voice=audio_path,
                caption="🤖 **Audio Reply**"
            )
            # File bhejne ke baad delete kar do server se
            if os.path.exists(audio_path):
                os.remove(audio_path)
        else:
            await callback_query.answer("❌ Audio fail ho gaya.", show_alert=True)
            
    except Exception as e:
        logger.error(f"TTS Callback Error: {e}")
        await callback_query.answer("❌ Error aa gaya.", show_alert=True)

# --- 🎤 VOICE MESSAGE HANDLER ---

@app.on_message(filters.voice)
async def voice_handler(client, message):
    msg = await message.reply("🎤 Sun raha hu...")
    try:
        file_path = await message.download()
        text_response = await voice_engine.voice_to_text_and_reply(file_path)
        
        speaker_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])
        
        await msg.edit_text(f"🤖: {text_response}", reply_markup=speaker_btn)
        await log_conversation(client, message, f"Voice Reply: {text_response}")
        
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Voice Handler Error: {e}")
        await msg.edit_text("❌ Awaz samajh nahi aayi.")

# --- 🚀 STARTUP SEQUENCE ---

async def main():
    # 1. Print Logo in Console
    print(LOGO)
    
    # 2. Start Web Server (For Koyeb Health Check)
    try:
        await start_server()
    except Exception as e:
        logger.warning(f"Server Error (Ignored): {e}")
    
    logger.info("🚀 Raj Bot is Starting...")
    
    # 3. Start Bot Client
    await app.start()
    
    # 4. Send Online Notification to Log Channel
    if Config.LOG_CHANNEL_ID:
        try:
            # Code block ``` use kiya taaki logo format na bigde
            await app.send_message(
                Config.LOG_CHANNEL_ID,
                f"✅ **Bot Online! All Systems Normal.**\n\n```\n{LOGO}\n```"
            )
        except Exception as e:
            logger.warning(f"Startup Log Failed: {e}")
    
    # 5. Keep Bot Running
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
 
