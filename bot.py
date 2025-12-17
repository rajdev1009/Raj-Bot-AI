import asyncio
import os
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database.mongo import db
from core.ai_engine import ai_engine
from core.voice_engine import voice_engine
from core.broadcast import broadcast_message
from core.security import Security
from utils.logger import logger

# Initialize Bot
app = Client(
    "RajBot_Session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# 1. START COMMAND
@app.on_message(filters.command("start"))
async def start_handler(client, message: Message):
    user = message.from_user
    await db.add_user(user.id, user.first_name, user.username)
    
    await message.reply_text(
        f"**Hello {user.first_name}! I am Raj.** 🤖\n"
        f"I am a 24/7 AI Bot powered by Gemini & MongoDB.\n\n"
        f"Commands:\n/image <prompt> - Generate/Analyze\n/start - Restart"
    )

# 2. BROADCAST (Admin Only)
@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def broadcast_handler(client, message: Message):
    msg = await message.reply_text("📢 Starting broadcast...")
    sent, failed = await broadcast_message(client, message.reply_to_message)
    await msg.edit_text(f"✅ Broadcast Complete\nSent: {sent}\nFailed: {failed}")

# 3. IMAGE GENERATION (Via Text)
@app.on_message(filters.command("image"))
async def image_gen_handler(client, message: Message):
    if len(message.command) < 2:
        return await message.reply("Usage: /image <prompt>")
    
    prompt = message.text.split(None, 1)[1]
    msg = await message.reply("🎨 Generating...")
    
    # Using Pollinations (Free, No Key) for reliable Image Gen in production bots
    image_url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}"
    
    await message.reply_photo(photo=image_url, caption=f"Generated: {prompt}")
    await msg.delete()
    await db.log_event("image_logs", {"user_id": message.from_user.id, "type": "generation", "prompt": prompt})

# 4. PASSWORD & SECURITY
@app.on_message(filters.text & filters.private)
async def text_handler(client, message: Message):
    user_id = message.from_user.id
    text = message.text

    # Trigger Password Flow
    if text.strip() == "Raj" and not Security.is_waiting(user_id):
        return await message.reply(Security.initiate_auth(user_id))

    # Check Password
    if Security.is_waiting(user_id):
        success, response = await Security.check_password(user_id, text)
        return await message.reply(response)

    # 5. AI CHAT & SMART DELAY
    # Send "typing" action
    await client.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
    
    # 15s Smart Delay (Non-blocking)
    if Config.SMART_DELAY > 0:
        await asyncio.sleep(Config.SMART_DELAY)
    
    # Get Response (AI or JSON)
    reply_text = await ai_engine.get_response(user_id, text)
    await message.reply_text(reply_text)

# 6. VOICE HANDLING
@app.on_message(filters.voice)
async def voice_handler(client, message: Message):
    msg = await message.reply("🎤 Listening...")
    
    # Download
    file_path = await message.download()
    await db.log_event("voice_logs", {"user_id": message.from_user.id, "file_id": message.voice.file_id})
    
    # Process
    text_response = await voice_engine.voice_to_text_and_reply(file_path)
    
    # Send Text
    await msg.edit_text(f"🤖: {text_response}")
    
    # Optional: Send Audio Reply back (TTS)
    audio_path = await voice_engine.text_to_speech(text_response)
    await message.reply_voice(audio_path)
    
    # Cleanup
    if os.path.exists(file_path): os.remove(file_path)
    if os.path.exists(audio_path): os.remove(audio_path)

# 7. IMAGE RECOGNITION
@app.on_message(filters.photo & filters.private)
async def photo_handler(client, message: Message):
    if message.caption and "/image" in message.caption:
        msg = await message.reply("👀 Looking at this...")
        file_path = await message.download()
        
        description = await ai_engine.analyze_image(file_path)
        await msg.edit_text(description)
        
        await db.log_event("image_logs", {"user_id": message.from_user.id, "type": "recognition"})
        os.remove(file_path)

if __name__ == "__main__":
    from pyrogram import enums
    print("🚀 Raj Bot is Starting...")
    app.run()
  
