import asyncio
import os
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction
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

# --- COMMANDS ---

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    user = message.from_user
    await db.add_user(user.id, user.first_name, user.username)
    await message.reply_text(
        f"**Namaste {user.mention}!** 🙏\n"
        f"Main Raj ka Personal AI Assistant hu (Gemini 2.5 Powered).\n\n"
        f"🤖 **Mujhse baat kaise karein?**\n"
        f"Agar kuch puchna hai to **'Dev'** laga kar pucho.\n"
        f"Example: _'Dev India ka PM kaun hai?'_"
    )

@app.on_message(filters.command("image"))
async def image_gen_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Likho: /image <kya chahiye>")
    
    prompt = message.text.split(None, 1)[1]
    msg = await message.reply("🎨 Painting bana raha hu...")
    
    image_url = await image_engine.generate_image_url(prompt)
    if image_url:
        await message.reply_photo(photo=image_url, caption=f"Ye lo {message.from_user.mention}: {prompt}")
    else:
        await message.reply("Error aa gaya boss.")
    await msg.delete()

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def broadcast_handler(client, message):
    msg = await message.reply_text("📢 Broadcast shuru...")
    sent, failed = await broadcast_message(client, message.reply_to_message)
    await msg.edit_text(f"✅ Ho gaya\nSent: {sent}\nFailed: {failed}")

# --- MAIN CHAT LOGIC ---

@app.on_message(filters.text & filters.private)
async def text_handler(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower() # Chota bada letter handle karne ke liye
    user_mention = message.from_user.mention

    # 1. SECURITY CHECK (✅ NO SLASH REQUIRED)
    # Sirf "raj" likhne par trigger hoga (bina / ke)
    if text_lower == "raj" and not Security.is_waiting(user_id):
        return await message.reply(Security.initiate_auth(user_id))
    
    # Password Validation
    if Security.is_waiting(user_id):
        success, response, photo_url = await Security.check_password(user_id, text)
        if photo_url:
            return await message.reply_photo(photo=photo_url, caption=response)
        else:
            return await message.reply(response)

    # 2. JSON CHECK (Fast Greetings)
    # Bina "Dev" ke bhi jawab dega agar Hi/Hello hai
    json_reply = ai_engine.get_json_reply(text)
    
    if json_reply:
        await asyncio.sleep(1) # Natural pause
        await message.reply_text(f"{json_reply} {user_mention}")
        return

    # 3. AI CHECK (Wake Word: "Dev")
    # "Dev" hoga tabhi Gemini 2.5 Flash chalega
    if "dev" in text_lower:
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        if Config.SMART_DELAY > 0:
            await asyncio.sleep(Config.SMART_DELAY)
            
        ai_response = await ai_engine.get_response(user_id, text)
        
        if ai_response:
            await message.reply_text(f"{ai_response}\n\n~ {user_mention}")
        else:
            # Agar error aaya (jo ab nahi aana chahiye 2.5 ke saath)
            await message.reply_text(f"Server busy hai boss, thodi der baad aana. {user_mention}")
    
    # 4. IGNORE EVERYTHING ELSE
    # Agar na Raj bola, na Hi bola, na Dev bola -> Bot kuch nahi karega.

@app.on_message(filters.voice)
async def voice_handler(client, message):
    msg = await message.reply("🎤 Sun raha hu...")
    file_path = await message.download()
    text_response = await voice_engine.voice_to_text_and_reply(file_path)
    await msg.edit_text(f"🤖: {text_response}\n~ {message.from_user.mention}")
    if os.path.exists(file_path): os.remove(file_path)

# --- STARTUP ---

async def main():
    try:
        await start_server()
    except:
        pass
    
    logger.info("🚀 Raj Bot (Gemini 2.5) Start Ho Raha Hai...")
    await app.start()
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
