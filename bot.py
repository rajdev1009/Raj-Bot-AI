import asyncio
import os
import fitz  # PyMuPDF
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction, ChatType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database.mongo import db
from core.ai_engine import ai_engine
from core.voice_engine import voice_engine
from core.image_engine import image_engine
from core.web_search import search_web
from core.broadcast import broadcast_message
from core.security import Security
from utils.logger import logger
from utils.server import start_server

# --- 🎨 STARTUP LOGO (Raj Dev Edition) ---
LOGO = r"""
_________________________________________________________________________
    
    [ R A J   D E V   S Y S T E M S ].               RAJ-BOT-AI 
    
    R A J      ██████╗   ███████╗ ██╗   ██╗
    D E V      ██╔══██╗ ██╔════╝ ██║   ██║
    A S I S T  ██║    ██║█████╗     ██║  ██║
    B O T      ██║   ██║ ██╔══╝    ╚██╗ ██╔╝ 
               ██████╔╝███████╗  ╚████╔╝  
               ╚═════╝  ╚══════╝   ╚═══╝   
    
    >>> AUTHENTICATED BY: RAJ DEV                     running -- R A J
    >>> ALL SYSTEMS ARE RUNNING STABLE
_________________________________________________________________________
"""

# ✅ Naya Session Name taaki connection refresh ho jaye
app = Client(
    "Raj_Master_V3", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

SETTINGS = {"group_auto_reply": False}

# --- 📝 LOGGING SYSTEM ---
async def log_conversation(client, message, bot_reply):
    try:
        if not message.from_user or not Config.LOG_CHANNEL_ID: return
        user = message.from_user
        log_text = (
            f"**#RajLog** 📝\n\n"
            f"👤 **User:** {user.mention} (`{user.id}`)\n"
            f"📥 **Message:** {message.text or '[Media]'}\n"
            f"🤖 **Dev Reply:** {bot_reply}"
        )
        await client.send_message(Config.LOG_CHANNEL_ID, log_text)
    except: pass

# --- 🎮 ADMIN COMMANDS ---

@app.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def stats_handler(c, m):
    u, mem = await db.get_stats()
    await m.reply(f"📊 **Bot Stats**\n👤 Users: {u}\n🧠 Memory: {mem}\n🧹 Cleanup: 7 Days")

@app.on_message(filters.command("personality") & filters.user(Config.ADMIN_ID))
async def personality_handler(c, m):
    if len(m.command) < 2: return await m.reply("Modes: `friend`, `teacher`, `funny`")
    mode = m.command[1].lower()
    ai_engine.personality = mode
    ai_engine.setup_next_key()
    await m.reply(f"✅ Personality: **{mode.upper()}**")

@app.on_message(filters.command("search"))
async def search_handler(c, m):
    if len(m.command) < 2: return await m.reply("Kya search karu?")
    query = m.text.split(None, 1)[1]
    wait = await m.reply("🔍 Searching internet...")
    data = await search_web(query)
    
    if data == "SEARCH_BLOCKED":
        res = await ai_engine.get_response(m.from_user.id, f"DuckDuckGo limited. Knowledge answer: {query}")
        await wait.edit(f"✨ **Internal Knowledge:**\n\n{res}")
    elif data:
        res = await ai_engine.get_response(m.from_user.id, f"Summarize search for: {query}\n\nData: {data}")
        await wait.edit(f"✨ **Web Search Result:**\n\n{res}")
    else: await wait.edit("❌ Kuch nahi mila.")

# --- 📁 MEDIA HANDLERS ---

@app.on_message(filters.photo)
async def vision_handler(c, m):
    wait = await m.reply("📸 Photo dekh raha hu (Gemini 2.5)...")
    path = await m.download()
    res = await ai_engine.get_response(m.from_user.id, m.caption or "Is photo ko samjhao", photo_path=path)
    await wait.edit(res)
    if os.path.exists(path): os.remove(path)

@app.on_message(filters.document)
async def pdf_handler(c, m):
    if m.document.mime_type == "application/pdf":
        wait = await m.reply("📄 PDF summarize kar raha hu...")
        path = await m.download()
        doc = fitz.open(path); text = "".join([p.get_text() for p in doc]); doc.close()
        res = await ai_engine.get_response(m.from_user.id, f"Summarize this PDF: {text[:4000]}")
        await wait.edit(f"📝 **PDF Summary:**\n\n{res}")
        if os.path.exists(path): os.remove(path)

@app.on_message(filters.command(["img", "image"]))
async def img_cmd(c, m):
    if len(m.command) < 2: return await m.reply("Prompt do!")
    prompt = m.text.split(None, 1)[1]
    wait = await m.reply("🎨 Drawing...")
    path = await image_engine.generate_image(prompt)
    if path:
        await m.reply_photo(path, caption=f"✨ **Prompt:** {prompt}")
        os.remove(path)
    await wait.delete()

# --- 🧠 CORE LOGIC (AI + MEMORY) ---

@app.on_message(filters.command("start"))
async def start_cmd(c, m):
    if not m.from_user: return
    await db.add_user(m.from_user.id, m.from_user.first_name, m.from_user.username)
    await m.reply(f"Namaste {m.from_user.first_name}! Main Raj ka Dev hu. Sab kuch makkhan chal raha hai!")

@app.on_message(filters.text & ~filters.command(["start", "img", "image", "search", "stats", "personality"]))
async def chat_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    
    # 1. SECURITY
    if message.chat.type == ChatType.PRIVATE and text_lower == "raj":
        if not Security.is_waiting(user_id): return await message.reply(Security.initiate_auth(user_id))
    if message.chat.type == ChatType.PRIVATE and Security.is_waiting(user_id):
        suc, res, ph = await Security.check_password(user_id, text)
        if ph: await message.reply_photo(ph, caption=res)
        else: await message.reply(res)
        return

    # 🧹 Clean Text for Memory
    clean_text = text_lower.replace("dev", "").strip()

    # 2. DATABASE MEMORY (Zero Quota Use)
    ans = await db.get_cached_response(clean_text)
    if ans: return await message.reply(ans)

    # 3. AI ENGINE (Gemini 2.5 Flash)
    if "dev" in text_lower:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        res = await ai_engine.get_response(user_id, text)
        if res:
            await db.add_response(clean_text, res)
            await message.reply(res)
            await log_conversation(client, message, res)
        return

    # 4. JSON
    if message.chat.type == ChatType.PRIVATE or SETTINGS["group_auto_reply"]:
        j_res = ai_engine.get_json_reply(text)
        if j_res: await message.reply(j_res)

# --- 🚀 STARTUP ---

async def main():
    print(LOGO)
    
    # 🧹 Start Database Indexes (7-day cleanup)
    await db.setup_indexes()
    
    # 🌍 Start Koyeb Health Check Server
    await start_server()
    
    # 🚀 Start Bot with pending updates dropped
    logger.info("🔥 BOT STARTING - CLEANING OLD MESSAGES...")
    await app.start()
    
    # Force drop pending updates (Ise use karne se bot rasta saaf karega)
    # await app.get_updates(offset=-1) # Alternative method
    
    me = await app.get_me()
    logger.info(f"🤖 Connected as: @{me.username}")
    
    if Config.LOG_CHANNEL_ID:
        try: await app.send_message(Config.LOG_CHANNEL_ID, "🚀 **Bot Is Online! Everything is stable.**")
        except: pass

    await idle()
    await app.stop()

if __name__ == "__main__":
    # Python 3.10+ Professional Event Loop
    asyncio.run(main())
    
