import asyncio
import os
from datetime import datetime
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction
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

app = Client(
    "RajBot_Session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# --- HELPER: LOGGING SYSTEM (SAFE MODE) ---
async def log_conversation(client, message, bot_reply):
    try:
        user = message.from_user
        chat_text = message.text or "[Media/Sticker]"
        time_now = datetime.now().strftime("%d-%m-%Y %I:%M %p")
        
        logger.info(f"📩 User: {user.first_name} | Msg: {chat_text}")
        logger.info(f"📤 Bot: {bot_reply[:50]}...")

        if Config.LOG_CHANNEL_ID:
            log_text = (
                f"**#New_Chat_Log** 📝\n\n"
                f"👤 **User:** {user.mention} (`{user.id}`)\n"
                f"🕒 **Time:** {time_now}\n\n"
                f"📥 **Message:**\n{chat_text}\n\n"
                f"🤖 **Bot Reply:**\n{bot_reply}"
            )
            try:
                await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except Exception as e:
                logger.warning(f"⚠️ Log Channel Error (Ignored): {e}")
                
    except Exception as main_e:
        logger.error(f"Logging System Error: {main_e}")

# --- COMMANDS ---

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    try:
        user = message.from_user
        # Database mein user add karo
        await db.add_user(user.id, user.first_name, user.username)
        
        await message.reply_text(
            f"**Namaste {user.mention}!** 🙏\n"
            f"Main Raj ka Personal Assistant hu (Dev).\n\n"
            f"Agar jawab pata hoga to turant dunga, nahi to **'Dev'** laga kar puchna."
        )
        # Log start command also
        logger.info(f"Start Command used by {user.first_name}")
    except Exception as e:
        logger.error(f"Start Error: {e}")

@app.on_message(filters.command("image"))
async def image_gen_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Likho: /image <kya chahiye>")
    
    prompt = message.text.split(None, 1)[1]
    msg = await message.reply("🎨 Painting bana raha hu...")
    
    try:
        image_url = await image_engine.generate_image_url(prompt)
        if image_url:
            await message.reply_photo(photo=image_url, caption=f"Ye lo: {prompt}")
            await log_conversation(client, message, f"Image: {prompt}")
        else:
            await message.reply("Error aa gaya boss.")
    except Exception as e:
        logger.error(f"Image Handler Error: {e}")
        await message.reply("Kuch gadbad ho gayi.")
    
    await msg.delete()

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def broadcast_handler(client, message):
    msg = await message.reply_text("📢 Broadcast shuru...")
    sent, failed = await broadcast_message(client, message.reply_to_message)
    await msg.edit_text(f"✅ Ho gaya\nSent: {sent}\nFailed: {failed}")

# --- MAIN CHAT LOGIC ---

# ✅ FIX IS HERE: Humne "~filters.command" lagaya hai.
# Iska matlab: "Agar ye koi Command (start/image) hai, to is function ko mat chalao"
@app.on_message(filters.text & filters.private & ~filters.command(["start", "image", "broadcast"]))
async def text_handler(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    
    speaker_btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔊 Suno (Listen)", callback_data="speak_msg")]
    ])

    # 1. SECURITY CHECK (Raj)
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

    # 2. JSON GREETINGS
    json_reply = ai_engine.get_json_reply(text)
    if json_reply:
        await asyncio.sleep(0.5)
        await message.reply_text(json_reply, reply_markup=speaker_btn)
        await log_conversation(client, message, json_reply)
        return

    # 3. DATABASE MEMORY
    cached_ans = await db.get_cached_response(text)
    if cached_ans:
        await message.reply_text(cached_ans, reply_markup=speaker_btn)
        await log_conversation(client, message, cached_ans)
        return

    # 4. AI CHECK (Wake Word: "Dev")
    if "dev" in text_lower:
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        if Config.SMART_DELAY > 0:
            await asyncio.sleep(Config.SMART_DELAY)
            
        ai_response = await ai_engine.get_response(user_id, text)
        
        if ai_response:
            await message.reply_text(ai_response, reply_markup=speaker_btn)
            await log_conversation(client, message, ai_response)
        else:
            await message.reply_text("Abhi busy hu.")
            await log_conversation(client, message, "AI Failed")
    else:
        # Ignore logic for random texts without "Dev"
        pass

# --- SPEAKER CALLBACK ---
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
            if os.path.exists(audio_path):
                os.remove(audio_path)
        else:
            await callback_query.answer("❌ Audio fail ho gaya.", show_alert=True)
            
    except Exception as e:
        logger.error(f"TTS Callback Error: {e}")
        await callback_query.answer("❌ Error aa gaya.", show_alert=True)

@app.on_message(filters.voice)
async def voice_handler(client, message):
    msg = await message.reply("🎤 Sun raha hu...")
    file_path = await message.download()
    text_response = await voice_engine.voice_to_text_and_reply(file_path)
    speaker_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])
    await msg.edit_text(f"🤖: {text_response}", reply_markup=speaker_btn)
    await log_conversation(client, message, f"Voice Reply: {text_response}")
    if os.path.exists(file_path): os.remove(file_path)

# --- STARTUP ---
async def main():
    try:
        await start_server()
    except:
        pass
    logger.info("🚀 Raj Bot (Start Fix) Starting...")
    await app.start()
    
    if Config.LOG_CHANNEL_ID:
        try:
            await app.send_message(Config.LOG_CHANNEL_ID, "✅ **Bot Rebooted & Online**")
        except Exception as e:
            logger.warning(f"Startup Log Error: {e} (Check ID or Permissions)")

    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
