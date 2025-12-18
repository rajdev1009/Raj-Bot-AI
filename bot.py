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

# --- 🎨 STARTUP LOGO (Advanced Alignment) ---
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

app = Client("RajBot_Session", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)
SETTINGS = {"group_auto_reply": False}

# --- 📝 ADVANCED LOGGING ---
async def log_conversation(client, message, bot_reply):
    try:
        if not message.from_user: return
        user = message.from_user
        chat_text = message.text or "[Media/Voice]"
        chat_type = "Private" if message.chat.type == ChatType.PRIVATE else "Group"
        
        logger.info(f"📩 [{chat_type}] {user.first_name}: {chat_text}")
        
        if Config.LOG_CHANNEL_ID:
            log_text = (
                f"**#RajLog** 📝\n\n"
                f"👤 **User:** {user.mention}\n"
                f"📥 **Message:** {chat_text}\n"
                f"🤖 **Dev Reply:** {bot_reply}"
            )
            try: await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except Exception as e: logger.warning(f"Log Channel Warning: {e}")
    except: pass

# --- 🎮 COMMANDS ---

@app.on_message(filters.command("mode") & filters.user(Config.ADMIN_ID))
async def mode_switch(client, message):
    if len(message.command) < 2:
        curr = "✅ ON" if SETTINGS["group_auto_reply"] else "❌ OFF"
        return await message.reply(f"Current Group Mode: {curr}")
    
    action = message.command[1].lower()
    if action == "on": SETTINGS["group_auto_reply"] = True; await message.reply("Group Auto-Reply: ON")
    elif action == "off": SETTINGS["group_auto_reply"] = False; await message.reply("Group Auto-Reply: OFF")

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    if not message.from_user: return
    await db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await message.reply_text(f"Namaste {message.from_user.first_name}! Main Raj ka Assistant Dev hu. Padhai mein help chahiye to 'Dev' lagakar puchna!")

@app.on_message(filters.command(["img", "image"]))
async def img_cmd(client, message):
    if len(message.command) < 2: return await message.reply("Likho: /img <prompt>")
    prompt = message.text.split(None, 1)[1]
    wait_msg = await message.reply("🎨 Painting bana raha hu...")
    
    try:
        path = await image_engine.generate_image(prompt)
        if path and os.path.exists(path):
            await message.reply_photo(path, caption=f"Ye lo: {prompt}")
            os.remove(path)
        else: await message.reply("Nahi ban payi photo, fir se try karo.")
    except: await message.reply("Technical Error!")
    finally: await wait_msg.delete()

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def bcast_cmd(client, message):
    msg = await message.reply("📢 Broadcasting...")
    sent, fail = await broadcast_message(client, message.reply_to_message)
    await msg.edit(f"✅ Sent: {sent} | Failed: {fail}")

# --- 🧠 MAIN LOGIC (THE BRAIN) ---

@app.on_message(filters.text & ~filters.command(["start", "image", "img", "broadcast", "mode"]))
async def chat_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    is_pvt = message.chat.type == ChatType.PRIVATE
    spk_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])

    # 1. SECURITY
    if is_pvt and text_lower == "raj":
        if not Security.is_waiting(user_id): return await message.reply(Security.initiate_auth(user_id))
    if is_pvt and Security.is_waiting(user_id):
        suc, res, ph = await Security.check_password(user_id, text)
        if ph: await message.reply_photo(ph, caption=res)
        else: await message.reply(res)
        return

    # 🧹 Clean Text for DB
    clean_text = text_lower.replace("dev", "").strip()

    # 🧠 2. DATABASE MEMORY (PRIORITY 1)
    # Check if we already answered this
    ans = await db.get_cached_response(clean_text)
    if ans:
        await message.reply(ans, reply_markup=spk_btn)
        await log_conversation(client, message, f"[Memory] {ans}")
        return

    # 🤖 3. AI ENGINE (PRIORITY 2 - Triggered by 'Dev')
    if "dev" in text_lower:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        ai_res = await ai_engine.get_response(user_id, text)
        if ai_res:
            # ✅ SAVE TO DATABASE: Agli baar ke liye yaad rakho
            await db.add_response(clean_text, ai_res)
            await message.reply(ai_res, reply_markup=spk_btn)
            await log_conversation(client, message, ai_res)
        return

    # 📜 4. JSON FALLBACK (PRIORITY 3)
    if is_pvt or SETTINGS["group_auto_reply"]:
        j_res = ai_engine.get_json_reply(text)
        if j_res:
            await message.reply(j_res, reply_markup=spk_btn)
            await log_conversation(client, message, j_res)

# --- 🔊 CALLBACKS & VOICE ---

@app.on_callback_query(filters.regex("speak_msg"))
async def voice_callback(client, query):
    t = query.message.text or query.message.caption
    if not t: return
    p = await voice_engine.text_to_speech(t)
    if p: await client.send_voice(query.message.chat.id, p); os.remove(p)

@app.on_message(filters.voice)
async def voice_msg_handler(client, message):
    m = await message.reply("🎤 Sun raha hu...")
    p = await message.download()
    t = await voice_engine.voice_to_text_and_reply(p)
    await m.edit(f"🤖: {t}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]]))
    if os.path.exists(p): os.remove(p)

async def main():
    print(LOGO)
    try: await start_server()
    except: pass
    logger.info("🚀 Raj Dev Advanced Bot Starting...")
    await app.start()
    if Config.LOG_CHANNEL_ID:
        try: await app.send_message(Config.LOG_CHANNEL_ID, f"✅ **Core Online!**\n\n```\n{LOGO}\n```")
        except: pass
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
 
