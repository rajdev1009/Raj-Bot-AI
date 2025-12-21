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

# --- 🐍 PYTHON INTERPRETER LOGIC ---
import sys
import io
import contextlib

def execute_python_code(code):
    """Python code sandbox execution"""
    # Security: In keywords ko block kiya hai taaki bot safe rahe
    forbidden = ["os.", "sys.", "shutil.", "subprocess", "open(", "eval(", "exec("]
    if any(x in code.lower() for x in forbidden):
        return "❌ Ghalat harkat mat kar! Ye keywords allow nahi hain."
    
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code)
        result = output.getvalue()
        return result if result else "✅ Success (No Output)."
    except Exception as e:
        return f"❌ Error: {str(e)}"

# --- 🎨 STARTUP LOGO ---
LOGO = r"""
_________________________________________________________________________
    
    [ R A J   D E V   S Y S T E M S ]                 RAJ- -LLM - MODEL 
    
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

SETTINGS = {"group_auto_reply": False}

# --- 🛠️ HELPERS ---
async def send_split_text(client, chat_id, text, reply_markup=None):
    if len(text) < 4000:
        await client.send_message(chat_id, text, reply_markup=reply_markup)
    else:
        chunk_size = 4000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        for i, chunk in enumerate(chunks):
            markup = reply_markup if i == len(chunks) - 1 else None
            await client.send_message(chat_id, chunk, reply_markup=markup)

async def log_conversation(client, message, bot_reply):
    try:
        if not message.from_user or not Config.LOG_CHANNEL_ID: return
        log_text = (f"**#RajLog** 📝\n\n👤 **User:** {message.from_user.mention}\n📥 **Message:** {message.text or '[Media]'}\n🤖 **Dev Reply:** {bot_reply}")
        await client.send_message(Config.LOG_CHANNEL_ID, log_text)
    except: pass

# --- 🎮 COMMANDS ---

@app.on_message(filters.command(["run", "py"]) & filters.user(Config.ADMIN_ID))
async def python_run(client, message):
    if len(message.command) < 2: return await message.reply("Code likho bsdk!")
    code = message.text.split(None, 1)[1]
    wait = await message.reply("⚙️ Executing...")
    res = execute_python_code(code)
    await wait.edit(f"🐍 **Python Output:**\n\n```python\n{res}\n```")

@app.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def stats_handler(client, message):
    u_count, m_count = await db.get_stats()
    await message.reply_text(f"📊 **Stats**\n👤 Users: {u_count}\n🧠 Memory: {m_count}")

@app.on_message(filters.command("cleardb") & filters.user(Config.ADMIN_ID))
async def clear_database(client, message):
    msg = await message.reply("⚠️ Clearing DB...")
    try:
        mongo_conn_url = getattr(Config, "MONGO_URI", getattr(Config, "MONGO_URL", None))
        import motor.motor_asyncio
        temp_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_conn_url)
        temp_db = temp_client["RajDev_Bot"]
        collections = await temp_db.list_collection_names()
        for col in collections: await temp_db[col].drop()
        await msg.edit("✅ Database Cleared!")
    except Exception as e: await msg.edit(f"❌ Error: {e}")

@app.on_message(filters.command(["personality", "role"]))
async def personality_handler(client, message):
    if len(message.command) < 2: return await message.reply("Usage: `/personality dev | hacker` ")
    mode = message.command[1].lower()
    msg = ai_engine.change_mode(mode)
    await message.reply(f"⚙️ {msg}")

@app.on_message(filters.command("search"))
async def search_handler(client, message):
    if len(message.command) < 2: return await message.reply("Batao kya search karna hai?")
    query = message.text.split(None, 1)[1]
    wait = await message.reply("🔍 Searching...")
    web_data = await search_web(query)
    res = await ai_engine.get_response(message.from_user.id, f"Summarize: {query}\n\nData:\n{web_data}")
    await wait.edit(f"✨ {res}")

@app.on_message(filters.command("mode") & filters.user(Config.ADMIN_ID))
async def mode_switch(client, message):
    action = message.command[1].lower() if len(message.command) > 1 else ""
    if action == "on": SETTINGS["group_auto_reply"] = True; await message.reply("✅ Group Mode ON")
    elif action == "off": SETTINGS["group_auto_reply"] = False; await message.reply("❌ Group Mode OFF")
    else: await message.reply(f"Mode: {'ON' if SETTINGS['group_auto_reply'] else 'OFF'}")

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await message.reply_text(f"**Namaste {message.from_user.first_name}!** 🙏 Main Dev hu.")

@app.on_message(filters.command(["img", "image"]))
async def img_cmd(client, message):
    if len(message.command) < 2: return await message.reply("Prompt likho!")
    prompt = message.text.split(None, 1)[1]
    wait = await message.reply("🎨 Painting...")
    path = await image_engine.generate_image(prompt)
    if path:
        await message.reply_photo(path, caption=f"Prompt: {prompt}")
        os.remove(path)
    else: await message.reply("Error!")
    await wait.delete()

# --- 📁 FILES ---

@app.on_message(filters.photo)
async def vision_handler(client, message):
    wait = await message.reply("📸 Checking...")
    path = await message.download()
    res = await ai_engine.get_response(message.from_user.id, message.caption or "Analyze", photo_path=path)
    await wait.delete()
    await send_split_text(client, message.chat.id, res)
    os.remove(path)

@app.on_message(filters.document)
async def pdf_handler(client, message):
    if message.document.mime_type == "application/pdf":
        wait = await message.reply("📄 Reading PDF...")
        path = await message.download()
        doc = fitz.open(path); content = "".join([page.get_text() for page in doc]); doc.close()
        res = await ai_engine.get_response(message.from_user.id, f"Summarize: {content[:4000]}")
        await wait.edit(f"📝 {res}"); os.remove(path)

# --- 🧠 CHAT ---

@app.on_message(filters.text & ~filters.command(["start", "img", "search", "stats", "personality", "mode", "cleardb", "run", "py"]))
async def chat_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id; text = message.text.strip(); text_lower = text.lower()
    is_pvt = message.chat.type == ChatType.PRIVATE
    spk_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])

    if is_pvt and text_lower == "raj":
        if not Security.is_waiting(user_id): return await message.reply(Security.initiate_auth(user_id))
    if is_pvt and Security.is_waiting(user_id):
        suc, res, ph = await Security.check_password(user_id, text)
        if ph: await message.reply_photo(ph, caption=res)
        else: await message.reply(res)
        return

    clean_text = text_lower.replace("dev", "").strip()
    ans = await db.get_cached_response(clean_text)
    if ans: return await message.reply(ans, reply_markup=spk_btn)

    if "dev" in text_lower or is_pvt:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        ai_res = await ai_engine.get_response(user_id, text)
        if ai_res:
            await db.add_response(clean_text, ai_res)
            await send_split_text(client, message.chat.id, ai_res, reply_markup=spk_btn)
            await log_conversation(client, message, ai_res)
        return

    if is_pvt or SETTINGS["group_auto_reply"]:
        j_res = ai_engine.get_json_reply(text)
        if j_res: await message.reply(j_res)

# --- 🔊 AUDIO ---

@app.on_callback_query(filters.regex("speak_msg"))
async def speak_cb(client, query):
    t = query.message.text or query.message.caption
    p = await voice_engine.text_to_speech(t[:1000])
    if p: await client.send_voice(query.message.chat.id, p); os.remove(p)

@app.on_message(filters.voice)
async def voice_msg(client, message):
    m = await message.reply("🎤 Listening..."); p = await message.download()
    t = await voice_engine.voice_to_text_and_reply(p)
    if not t or len(t) < 3: return await m.edit("Noise detected!")
    ai_res = await ai_engine.get_response(message.from_user.id, t)
    await m.delete()
    await send_split_text(client, message.chat.id, f"🎤 {t}\n\n🤖 {ai_res}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]]))
    os.remove(p)

async def main():
    print(LOGO); await start_server(); await app.start()
    logger.info("🚀 ONLINE!"); await idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop(); loop.run_until_complete(main())
    
