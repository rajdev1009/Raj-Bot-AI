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

SETTINGS = {"group_auto_reply": False}

# --- LOGGING ---
async def log_conversation(client, message, bot_reply):
    try:
        user = message.from_user
        chat_text = message.text or "[Media]"
        chat_type = "Private" if message.chat.type == ChatType.PRIVATE else "Group"
        logger.info(f"📩 [{chat_type}] {user.first_name}: {chat_text}")
        if Config.LOG_CHANNEL_ID:
            log_text = f"**#Log**\n👤 {user.mention}\n📥 {chat_text}\n🤖 {bot_reply}"
            try: await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except: pass
    except: pass

# --- COMMANDS ---
@app.on_message(filters.command("mode") & filters.user(Config.ADMIN_ID))
async def mode_switch(c, m):
    if len(m.command) < 2: return await m.reply(f"Status: {SETTINGS['group_auto_reply']}")
    action = m.command[1].lower()
    if action == "on": SETTINGS["group_auto_reply"] = True; await m.reply("Mode: ON")
    elif action == "off": SETTINGS["group_auto_reply"] = False; await m.reply("Mode: OFF")

@app.on_message(filters.command("start"))
async def start(c, m):
    await db.add_user(m.from_user.id, m.from_user.first_name, m.from_user.username)
    await m.reply("Namaste! Main Raj ka Assistant hu (Dev).")

@app.on_message(filters.command(["image", "img"]))
async def img_gen(c, m):
    try:
        if len(m.command) < 2: return await m.reply("Likho: /img cat")
        prompt = m.text.split(None, 1)[1]
        msg = await m.reply("🎨 Painting...")
        url = await image_engine.generate_image_url(prompt)
        if url: await m.reply_photo(url, caption=f"Img: {prompt}")
        else: await m.reply("Busy.")
        await msg.delete()
    except: pass

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def bcast(c, m):
    s, f = await broadcast_message(c, m.reply_to_message)
    await m.reply(f"Sent: {s}, Failed: {f}")

# --- MAIN LOGIC ---
@app.on_message(filters.text & ~filters.command(["start", "image", "img", "broadcast", "mode"]))
async def main_chat(c, m):
    user_id = m.from_user.id
    text = m.text.strip()
    text_lower = text.lower()
    is_pvt = m.chat.type == ChatType.PRIVATE
    spk_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])

    # 1. SECURITY
    if is_pvt:
        if text_lower == "raj":
            if not Security.is_waiting(user_id): return await m.reply(Security.initiate_auth(user_id))
        if Security.is_waiting(user_id):
            suc, res, ph = await Security.check_password(user_id, text)
            if ph: await m.reply_photo(ph, caption=res)
            else: await m.reply(res)
            return

    # 2. DATABASE (Priority 1)
    # Pehle pura text check karo, fir bina 'dev' ke check karo
    cached = await db.get_cached_response(text)
    if not cached:
        clean = text_lower.replace("dev", "").strip()
        if clean: cached = await db.get_cached_response(clean)
    
    if cached:
        await m.reply(cached, reply_markup=spk_btn)
        await log_conversation(c, m, cached)
        return

    # 3. AI (Priority 2 - Only if "Dev" is present)
    if "dev" in text_lower:
        await c.send_chat_action(m.chat.id, ChatAction.TYPING)
        ai_res = await ai_engine.get_response(user_id, text)
        if ai_res:
            await m.reply(ai_res, reply_markup=spk_btn)
            await log_conversation(c, m, ai_res)
        return

    # 4. JSON (Priority 3 - Only if NO "Dev" & Settings allow)
    if is_pvt or SETTINGS["group_auto_reply"]:
        json_res = ai_engine.get_json_reply(text)
        if json_res:
            await m.reply(json_res, reply_markup=spk_btn)
            await log_conversation(c, m, json_res)

# --- CALLBACKS ---
@app.on_callback_query(filters.regex("speak_msg"))
async def spk(c, q):
    try:
        path = await voice_engine.text_to_speech(q.message.text or q.message.caption)
        if path: await c.send_voice(q.message.chat.id, path); os.remove(path)
    except: await q.answer("Error", show_alert=True)

@app.on_message(filters.voice)
async def vc(c, m):
    p = await m.download()
    res = await voice_engine.voice_to_text_and_reply(p)
    await m.reply(f"🤖: {res}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]]))
    os.remove(p)

async def main():
    print(LOGO)
    try: await start_server()
    except: pass
    logger.info("🚀 Raj Bot Starting...")
    await app.start()
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
 
