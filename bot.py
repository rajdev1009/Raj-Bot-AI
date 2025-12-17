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
        f"Main Raj ka Personal Assistant hu (Dev).\n\n"
        f"🧠 **Smart Feature:**\n"
        f"Agar mujhe jawab pata hai, to main turant bata dunga.\n"
        f"Agar nahi pata, to **'Dev'** laga kar pucho taaki main seekh lu."
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

# --- MAIN LOGIC (THE BRAIN) ---

@app.on_message(filters.text & filters.private)
async def text_handler(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    user_mention = message.from_user.mention

    # 1. SECURITY CHECK (Password: Raj)
    if text_lower == "raj" and not Security.is_waiting(user_id):
        return await message.reply(Security.initiate_auth(user_id))
    
    if Security.is_waiting(user_id):
        success, response, photo_url = await Security.check_password(user_id, text)
        if photo_url:
            return await message.reply_photo(photo=photo_url, caption=response)
        else:
            return await message.reply(response)

    # 2. JSON GREETINGS (Hi/Hello - Fast Reply)
    json_reply = ai_engine.get_json_reply(text)
    if json_reply:
        await asyncio.sleep(0.5)
        await message.reply_text(f"{json_reply} {user_mention}")
        return

    # 3. DATABASE MEMORY CHECK (No "Dev" Needed)
    # Agar sawal pehle pucha gaya hai, to turant jawab do
    cached_ans = await db.get_cached_response(text)
    
    if cached_ans:
        # User ko feel karane ke liye ki humne yaad rakha hai
        await message.reply_text(f"{cached_ans}\n\n(Saved Memory 🧠)")
        return

    # 4. AI CHECK (Wake Word: "Dev" Needed)
    # Agar database mein nahi mila, to tabhi jawab do jab "Dev" bola ho
    if "dev" in text_lower:
        await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
        
        # Thoda delay taaki real lage
        if Config.SMART_DELAY > 0:
            await asyncio.sleep(Config.SMART_DELAY)
            
        ai_response = await ai_engine.get_response(user_id, text)
        
        if ai_response:
            await message.reply_text(f"{ai_response}\n\n~ {user_mention}")
        else:
            await message.reply_text(f"Abhi busy hu. {user_mention}")
    
    # 5. IGNORE (Agar na DB mein hai, na Dev bola)
    else:
        pass

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
    
    logger.info("🚀 Raj Bot (Smart Memory) Start Ho Raha Hai...")
    await app.start()
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
