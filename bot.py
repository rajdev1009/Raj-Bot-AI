import asyncio
import os
import fitz  # PyMuPDF
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction, ChatType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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

# --- 🎨 PRO STARTUP LOGO (RAJ DEV SYSTEMS) ---
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
    >>> ALL SYSTEMS ARE RUNNING STABLE | MODEL: GEMINI 2.5 FLASH
_________________________________________________________________________
"""

app = Client(
    "RajBot_Session", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

SETTINGS = {"group_auto_reply": False}

# --- 📊 ADMIN & STATS HANDLERS ---

@app.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def stats_handler(client, message):
    u_count, m_count = await db.get_stats()
    await message.reply_text(
        f"📊 **RajBot Advanced Stats**\n\n"
        f"👤 **Total Users:** {u_count}\n"
        f"🧠 **AI Memories:** {m_count}\n"
        f"🤖 **Engine:** Gemini 2.5 Flash\n"
        f"🧹 **Cleanup:** 7-Day TTL Active\n"
        f"🛡️ **System Status:** Online"
    )

@app.on_message(filters.command("personality") & filters.user(Config.ADMIN_ID))
async def personality_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/personality friend | teacher | funny` ")
    mode = message.command[1].lower()
    ai_engine.personality = mode
    ai_engine.setup_next_key()
    await message.reply(f"✅ Dev ki personality ab **{mode.upper()}** par set hai!")

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def broadcast_handler(client, message):
    msg = await message.reply_text("📢 Broadcasting message to all users...")
    sent, failed = await broadcast_message(client, message.reply_to_message)
    await msg.edit_text(f"✅ **Broadcast Finished**\n\n🚀 Sent: {sent}\n❌ Failed: {failed}")

# --- 🔍 SEARCH & WEB FEATURES ---

@app.on_message(filters.command("search"))
async def search_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Batao kya search karna hai?")
    query = message.text.split(None, 1)[1]
    wait_msg = await message.reply("🔍 Internet par dhoond raha hu...")
    
    web_data = await search_web(query)
    
    if web_data == "SEARCH_BLOCKED":
        res = await ai_engine.get_response(message.from_user.id, f"DuckDuckGo limited. Knowledge-based answer for: {query}")
        await wait_msg.edit(f"✨ **Note: Live search busy thi, par mere paas ye info hai:**\n\n{res}")
    elif web_data:
        res = await ai_engine.get_response(message.from_user.id, f"Summarize search for: {query}\n\nWeb Data:\n{web_data}")
        await wait_msg.edit(f"✨ **Live Search Result:**\n\n{res}")
    else:
        await wait_msg.edit("❌ Kuch nahi mila.")

# --- 📁 MEDIA & FILE HANDLERS (VISION/PDF) ---

@app.on_message(filters.photo)
async def vision_handler(client, message):
    wait = await message.reply("📸 Photo scan kar raha hu (Vision 2.5)...")
    path = await message.download()
    prompt = message.caption or "Is photo ko samjhao"
    res = await ai_engine.get_response(message.from_user.id, prompt, photo_path=path)
    await wait.edit(res)
    if os.path.exists(path): os.remove(path)

@app.on_message(filters.document)
async def pdf_handler(client, message):
    if message.document.mime_type == "application/pdf":
        wait = await message.reply("📄 PDF file analyze kar raha hu...")
        path = await message.download()
        try:
            doc = fitz.open(path)
            content = "".join([page.get_text() for page in doc])
            doc.close()
            res = await ai_engine.get_response(message.from_user.id, f"Summarize this PDF content for me: {content[:4000]}")
            await wait.edit(f"📝 **PDF Summary:**\n\n{res}")
        except Exception as e:
            await wait.edit(f"Error reading PDF: {e}")
        if os.path.exists(path): os.remove(path)

@app.on_message(filters.command(["img", "image"]))
async def img_cmd(client, message):
    if len(message.command) < 2: return await message.reply("Prompt do!")
    prompt = message.text.split(None, 1)[1]
    wait = await message.reply("🎨 Painting ban rahi hai...")
    path = await image_engine.generate_image(prompt)
    if path:
        await message.reply_photo(path, caption=f"✨ **Prompt:** {prompt}")
        if os.path.exists(path): os.remove(path)
    else: await message.reply("Photo nahi ban payi.")
    await wait.delete()

# --- 🧠 CORE LOGIC LOOP (AI + MEMORY) ---

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    if not message.from_user: return
    await db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await message.reply_text(
        f"**Namaste {message.from_user.first_name}!** 🙏\n"
        f"Main Raj ka Personal AI Assistant hu (Dev).\n\n"
        f"Main **Gemini 2.5 Flash** use karta hu jo ki super fast hai. "
        f"Mera dimaag baaton ko yaad rakhta hai taaki aapka time bache!"
    )

@app.on_message(filters.text & ~filters.command(["start", "img", "image", "search", "stats", "personality", "broadcast"]))
async def chat_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    is_pvt = message.chat.type == ChatType.PRIVATE
    
    # 🛑 1. SECURITY (Auth Check)
    if is_pvt and text_lower == "raj":
        if not Security.is_waiting(user_id): return await message.reply(Security.initiate_auth(user_id))
    if is_pvt and Security.is_waiting(user_id):
        suc, res, ph = await Security.check_password(user_id, text)
        if ph: await message.reply_photo(ph, caption=res)
        else: await message.reply(res)
        return

    # 🧹 Clean Text for Memory Matching
    clean_text = text_lower.replace("dev", "").strip()

    # 🧠 2. DATABASE MEMORY (Zero Quota Use)
    ans = await db.get_cached_response(clean_text)
    if ans:
        return await message.reply(ans)

    # 🤖 3. AI ENGINE (Gemini 2.5 Flash)
    if "dev" in text_lower:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        ai_res = await ai_engine.get_response(user_id, text)
        if ai_res:
            await db.add_response(clean_text, ai_res) # Save for 7 days
            await message.reply(ai_res)
        return

    # 📜 4. JSON FALLBACK
    if is_pvt or SETTINGS["group_auto_reply"]:
        j_res = ai_engine.get_json_reply(text)
        if j_res: await message.reply(j_res)

# --- 🚀 STARTUP SEQUENCE ---

async def main():
    print(LOGO)
    await start_server() # Health Check
    await db.setup_indexes() # Auto-Cleanup Trigger
    
    logger.info("🚀 RAJ DEV MEGA-BOT (STRICT 2.5 FLASH) STARTING...")
    await app.start()
    
    # Flush old messages
    await app.get_updates(offset=-1) 
    
    logger.info("✅ ALL SYSTEMS GREEN! BOT IS RESPONDING.")
    await idle()
    await app.stop()

if __name__ == "__main__":
    # Stable loop for Python 3.10
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
        
