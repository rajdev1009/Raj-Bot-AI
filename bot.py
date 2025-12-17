import asyncio
import os
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction
from config import Config
from database.mongo import db
from core.ai_engine import ai_engine
from core.voice_engine import voice_engine
from core.image_engine import image_engine  # Added Import
from core.broadcast import broadcast_message
from core.security import Security
from utils.logger import logger
from utils.server import start_server

# Initialize Bot
app = Client(
    "RajBot_Session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# --- [HANDLERS START] ---

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    user = message.from_user
    await db.add_user(user.id, user.first_name, user.username)
    await message.reply_text(
        f"**Hello {user.first_name}! I am Raj.** 🤖\n"
        f"System: Online 🟢\nLocation: Lumding, Assam\n"
        f"Try: /image or just talk to me."
    )

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def broadcast_handler(client, message):
    msg = await message.reply_text("📢 Starting broadcast...")
    sent, failed = await broadcast_message(client, message.reply_to_message)
    await msg.edit_text(f"✅ Broadcast Complete\nSent: {sent}\nFailed: {failed}")

@app.on_message(filters.command("image"))
async def image_gen_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /image <prompt>")
    
    prompt = message.text.split(None, 1)[1]
    msg = await message.reply("🎨 Generating...")
    
    # Using the new Image Engine
    image_url = await image_engine.generate_image_url(prompt)
    
    if image_url:
        await message.reply_photo(photo=image_url, caption=f"Generated: {prompt}")
        await db.log_event("image_logs", {"user_id": message.from_user.id, "prompt": prompt})
    else:
        await message.reply("❌ Error creating image. Try again.")
    
    await msg.delete()

@app.on_message(filters.text & filters.private)
async def text_handler(client, message):
    user_id = message.from_user.id
    text = message.text

    # 1. Security Check (Password: Rajdev9101)
    if text.strip() == "Raj" and not Security.is_waiting(user_id):
        return await message.reply(Security.initiate_auth(user_id))
    
    if Security.is_waiting(user_id):
        success, response = await Security.check_password(user_id, text)
        return await message.reply(response)

    # 2. AI Response
    await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    if Config.SMART_DELAY > 0:
        await asyncio.sleep(Config.SMART_DELAY) # Human-like delay
        
    reply_text = await ai_engine.get_response(user_id, text)
    await message.reply_text(reply_text)

@app.on_message(filters.voice)
async def voice_handler(client, message):
    msg = await message.reply("🎤 Processing Voice...")
    file_path = await message.download()
    
    # Process Voice
    text_response = await voice_engine.voice_to_text_and_reply(file_path)
    await msg.edit_text(f"🤖: {text_response}")
    
    # Cleanup
    if os.path.exists(file_path): os.remove(file_path)

# --- [HANDLERS END] ---

async def main():
    # 1. Start Web Server (For 24/7 Keep Alive)
    try:
        await start_server()
    except Exception as e:
        logger.warning(f"Server Error (Ignorable locally): {e}")
    
    # 2. Start Bot Client
    logger.info("🚀 Starting Telegram Client...")
    await app.start()
    
    # 3. Notify Admin
    try:
        if Config.ADMIN_ID:
            await app.send_message(Config.ADMIN_ID, "✅ **Raj Bot is Online**")
    except:
        pass

    # 4. Idle (Keep running)
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
