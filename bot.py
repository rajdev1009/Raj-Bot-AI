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

app = Client(
    "RajBot_Session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# --- 🎚️ GLOBAL SETTINGS ---
SETTINGS = {
    "group_auto_reply": False
}

# --- 📝 ADVANCED LOGGING ---
async def log_conversation(client, message, bot_reply):
    try:
        if not message.from_user: return
        user = message.from_user
        chat_text = message.text or "[Media/File]"
        chat_type = "Private" if message.chat.type == ChatType.PRIVATE else "Group"
        
        logger.info(f"📩 [{chat_type}] {user.first_name}: {chat_text}")
        
        if Config.LOG_CHANNEL_ID:
            log_text = (
                f"**#RajLog** 📝\n\n"
                f"👤 **User:** {user.mention} (`{user.id}`)\n"
                f"📥 **Message:** {chat_text}\n"
                f"🤖 **Dev Reply:** {bot_reply}"
            )
            try: await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except Exception as e:
                logger.warning(f"Log Channel Error: {e}")
    except: pass

# --- 🎮 ADMIN & FEATURE COMMANDS ---

@app.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def stats_handler(client, message):
    u_count, m_count = await db.get_stats()
    await message.reply_text(
        f"📊 **Bot Statistics**\n\n"
        f"👤 Total Users: {u_count}\n"
        f"🧠 Memory Saved: {m_count}\n"
        f"🤖 Model: Gemini 2.5 Flash\n"
        f"🧹 Auto-Cleanup: 7 Days Active"
    )

@app.on_message(filters.command("personality") & filters.user(Config.ADMIN_ID))
async def personality_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/personality friend | teacher | funny` ")
    mode = message.command[1].lower()
    ai_engine.personality = mode
    ai_engine.setup_next_key()
    await message.reply(f"✅ Dev ki personality ab **{mode.upper()}** ho gayi hai!")

@app.on_message(filters.command("search"))
async def search_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Batao kya search karna hai?")
    query = message.text.split(None, 1)[1]
    wait_msg = await message.reply("🔍 Internet par dhoond raha hu...")
    
    web_data = await search_web(query)
    
    if web_data == "SEARCH_BLOCKED":
        # Fallback logic agar DuckDuckGo block kare
        res = await ai_engine.get_response(message.from_user.id, f"DuckDuckGo is currently limited. Use your internal knowledge to answer: {query}")
        await wait_msg.edit(f"✨ **Note: Live search busy thi, par mere paas ye info hai:**\n\n{res}")
    elif web_data:
        res = await ai_engine.get_response(message.from_user.id, f"Analyze and summarize this web search for the user: {query}\n\nWeb Data:\n{web_data}")
        await wait_msg.edit(f"✨ **Live Web Results:**\n\n{res}")
    else:
        await wait_msg.edit("❌ Kuch nahi mila.")

@app.on_message(filters.command("mode") & filters.user(Config.ADMIN_ID))
async def mode_switch(client, message):
    if len(message.command) < 2:
        status = "ON" if SETTINGS["group_auto_reply"] else "OFF"
        return await message.reply(f"Current Group Mode: {status}")
    action = message.command[1].lower()
    if action == "on": SETTINGS["group_auto_reply"] = True; await message.reply("Group Mode: ON")
    elif action == "off": SETTINGS["group_auto_reply"] = False; await message.reply("Group Mode: OFF")

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    if not message.from_user: return
    await db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await message.reply_text(
        f"**Namaste {message.from_user.first_name}!** 🙏\n"
        f"Main Raj ka Personal AI Assistant hu (Dev).\n\n"
        f"Mera dimaag **Gemini 2.5 Flash** se chalta hai. "
        f"Padhai mein help chahiye toh message mein **'Dev'** lagana!"
    )

@app.on_message(filters.command(["img", "image"]))
async def img_cmd(client, message):
    if len(message.command) < 2: return await message.reply("Prompt likho!")
    prompt = message.text.split(None, 1)[1]
    wait = await message.reply("🎨 Painting ban rahi hai...")
    path = await image_engine.generate_image(prompt)
    if path:
        await message.reply_photo(path, caption=f"✨ **Generated:** {prompt}")
        if os.path.exists(path): os.remove(path)
    else: await message.reply("Nahi ban payi photo.")
    await wait.delete()

@app.on_message(filters.command("broadcast") & filters.user(Config.ADMIN_ID) & filters.reply)
async def broadcast_handler(client, message):
    msg = await message.reply_text("📢 Broadcast shuru...")
    sent, failed = await broadcast_message(client, message.reply_to_message)
    await msg.edit_text(f"✅ **Broadcast Finished**\nSent: {sent}\nFailed: {failed}")

# --- 📁 FILE HANDLERS (Vision & PDF) ---

@app.on_message(filters.photo)
async def vision_handler(client, message):
    wait = await message.reply("📸 Photo dekh raha hu (Gemini 2.5 Vision)...")
    path = await message.download()
    prompt = message.caption or "Is photo ko samjhao"
    res = await ai_engine.get_response(message.from_user.id, prompt, photo_path=path)
    await wait.edit(res)
    if os.path.exists(path): os.remove(path)

@app.on_message(filters.document)
async def pdf_handler(client, message):
    if message.document.mime_type == "application/pdf":
        wait = await message.reply("📄 PDF file padh raha hu...")
        path = await message.download()
        try:
            doc = fitz.open(path)
            content = ""
            for page in doc: content += page.get_text()
            doc.close()
            # PDF Summary using 2.5 Flash
            res = await ai_engine.get_response(message.from_user.id, f"I am a student. Summarize this PDF content for me: {content[:4000]}")
            await wait.edit(f"📝 **PDF Summary:**\n\n{res}")
        except Exception as e:
            logger.error(f"PDF Error: {e}")
            await wait.edit("PDF padhne mein error aaya.")
        if os.path.exists(path): os.remove(path)

# --- 🧠 MAIN LOGIC (THE LOOP) ---

@app.on_message(filters.text & ~filters.command(["start", "img", "image", "search", "stats", "personality", "mode", "broadcast"]))
async def chat_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    is_pvt = message.chat.type == ChatType.PRIVATE
    
    spk_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])

    # 🛑 1. SECURITY (Private Chat Only)
    if is_pvt and text_lower == "raj":
        if not Security.is_waiting(user_id): return await message.reply(Security.initiate_auth(user_id))
    if is_pvt and Security.is_waiting(user_id):
        suc, res, ph = await Security.check_password(user_id, text)
        if ph: await message.reply_photo(ph, caption=res)
        else: await message.reply(res)
        return

    # 🧹 Clean Text for Memory Matching
    clean_text = text_lower.replace("dev", "").strip()

    # 🧠 2. DATABASE MEMORY (Priority 1)
    ans = await db.get_cached_response(clean_text)
    if ans:
        await message.reply(ans, reply_markup=spk_btn)
        return

    # 🤖 3. AI ENGINE (Priority 2 - Strict Gemini 2.5 Flash)
    if "dev" in text_lower:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        ai_res = await ai_engine.get_response(user_id, text)
        
        if ai_res:
            # ✅ Save to memory for 7 days (auto-cleanup in mongo.py)
            await db.add_response(clean_text, ai_res)
            await message.reply(ai_res, reply_markup=spk_btn)
            await log_conversation(client, message, ai_res)
        return

    # 📜 4. JSON FALLBACK (Priority 3)
    if is_pvt or SETTINGS["group_auto_reply"]:
        j_res = ai_engine.get_json_reply(text)
        if j_res:
            await asyncio.sleep(0.5)
            await message.reply(j_res, reply_markup=spk_btn)
            await log_conversation(client, message, j_res)

# --- 🔊 AUDIO HANDLERS ---

@app.on_callback_query(filters.regex("speak_msg"))
async def speak_cb(client, query):
    await query.answer("🔊 Audio generate ho raha hai...")
    t = query.message.text or query.message.caption
    if not t: return
    p = await voice_engine.text_to_speech(t)
    if p:
        await client.send_voice(query.message.chat.id, p)
        if os.path.exists(p): os.remove(p)

@app.on_message(filters.voice)
async def voice_msg(client, message):
    m = await message.reply("🎤 Sun raha hu...")
    p = await message.download()
    t = await voice_engine.voice_to_text_and_reply(p)
    await m.edit(f"🤖: {t}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]]))
    if os.path.exists(p): os.remove(p)

# --- 🚀 STARTUP SEQUENCE ---

async def main():
    print(LOGO)
    await start_server()
    await app.start()
    logger.info("🚀 RAJ DEV MEGA-BOT (STRICT 2.5 FLASH) ONLINE!")
    
    # Notify Admin/Log Channel
    if Config.LOG_CHANNEL_ID:
        try:
            await app.send_message(Config.LOG_CHANNEL_ID, f"✅ **Bot Online!**\n\n```\n{LOGO}\n```")
        except: pass
        
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
 
