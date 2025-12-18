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

# --- 🎨 AAPKA LOGO ---
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

# Stable session name
app = Client("RajBot_Session", api_id=Config.API_ID, api_hash=Config.API_HASH, bot_token=Config.BOT_TOKEN)
SETTINGS = {"group_auto_reply": False}

# --- 🎮 COMMANDS ---

@app.on_message(filters.command("start"))
async def start_cmd(c, m):
    if not m.from_user: return
    await db.add_user(m.from_user.id, m.from_user.first_name, m.from_user.username)
    await m.reply(f"Namaste {m.from_user.first_name}! Main Raj ka Dev hu. Pucho kya puchna hai (Gemini 2.5 Flash).")

@app.on_message(filters.command("search"))
async def search_handler(c, m):
    if len(m.command) < 2: return await m.reply("Kya search karu?")
    query = m.text.split(None, 1)[1]
    wait = await m.reply("🔍 Searching...")
    data = await search_web(query)
    
    # ⚡ Search Error Fix (Fallback Logic)
    if data == "SEARCH_BLOCKED":
        res = await ai_engine.get_response(m.from_user.id, f"DuckDuckGo limited. Answer using your knowledge: {query}")
        await wait.edit(f"✨ **Internal Knowledge:**\n\n{res}")
    elif data:
        res = await ai_engine.get_response(m.from_user.id, f"Summarize search for: {query}\n\nData: {data}")
        await wait.edit(res)
    else: await wait.edit("❌ Kuch nahi mila.")

@app.on_message(filters.command(["img", "image"]))
async def img_cmd(c, m):
    if len(m.command) < 2: return await m.reply("Prompt do!")
    prompt = m.text.split(None, 1)[1]
    wait = await m.reply("🎨 Drawing...")
    path = await image_engine.generate_image(prompt)
    if path:
        await m.reply_photo(path, caption=f"✨ {prompt}")
        os.remove(path)
    await wait.delete()

# --- 📁 FILES & VISION ---

@app.on_message(filters.photo)
async def vision_handler(c, m):
    wait = await m.reply("📸 Scannig photo...")
    path = await m.download()
    res = await ai_engine.get_response(m.from_user.id, m.caption or "Is photo ko samjhao", photo_path=path)
    await wait.edit(res)
    if os.path.exists(path): os.remove(path)

# --- 🧠 MAIN CHAT LOGIC ---

@app.on_message(filters.text & ~filters.command(["start", "img", "image", "search", "stats", "personality"]))
async def chat_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    
    # 1. Memory Match (Priority)
    clean_text = text_lower.replace("dev", "").strip()
    ans = await db.get_cached_response(clean_text)
    if ans: return await message.reply(ans)

    # 2. AI (Dev)
    if "dev" in text_lower:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        res = await ai_engine.get_response(user_id, text)
        if res:
            await db.add_response(clean_text, res)
            await message.reply(res)
        return

# --- 🚀 STARTUP ---

async def main():
    print(LOGO)
    
    # Start Services
    await start_server()
    await db.setup_indexes() # Cleanup trigger
    
    logger.info("🚀 STARTING BOT...")
    await app.start()
    
    # Clear any pending updates to avoid "Old Message Flood"
    await app.get_updates(offset=-1) 
    
    logger.info("✅ RAJ DEV BOT IS NOW RESPONDING!")
    await idle()
    await app.stop()

if __name__ == "__main__":
    # Purana loop jo aapke liye work kar raha tha
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
