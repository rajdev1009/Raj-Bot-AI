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

# --- 🎚️ GLOBAL SETTINGS ---
SETTINGS = {
    "group_auto_reply": False
}

# --- 🛠️ HELPER: Long Message Splitter ---
async def send_split_text(client, chat_id, text, reply_markup=None):
    if len(text) < 4000:
        await client.send_message(chat_id, text, reply_markup=reply_markup)
    else:
        chunk_size = 4000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        for i, chunk in enumerate(chunks):
            markup = reply_markup if i == len(chunks) - 1 else None
            await client.send_message(chat_id, chunk, reply_markup=markup)

# --- 📝 LOGGING SYSTEM ---
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
                f"👤 **User:** {user.mention}\n"
                f"📥 **Message:** {chat_text}\n"
                f"🤖 **Dev Reply:** {bot_reply}"
            )
            try: await client.send_message(Config.LOG_CHANNEL_ID, log_text)
            except: pass
    except: pass

# --- 🎮 COMMAND HANDLERS ---

@app.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def stats_handler(client, message):
    u_count, m_count = await db.get_stats()
    await message.reply_text(f"📊 **Bot Statistics**\n\n👤 Total Users: {u_count}\n🧠 Saved Memories: {m_count}\n🤖 Raj LLM MODEL.")

# --- 🗑️ DELETE DATABASE COMMAND (FIXED: DB NAME SPECIFIED) ---
@app.on_message(filters.command("cleardb") & filters.user(Config.ADMIN_ID))
async def clear_database(client, message):
    msg = await message.reply("⚠️ **WARNING:** Main poora database uda raha hu (Users + Memory)...\n\nProcessing... ⏳")
    
    try:
        # 1. Config Check
        mongo_conn_url = getattr(Config, "MONGO_URI", getattr(Config, "MONGO_URL", None))
        
        if not mongo_conn_url:
            await msg.edit("❌ Error: `config.py` mein `MONGO_URI` nahi mila!")
            return

        # 2. Direct Connection
        import motor.motor_asyncio
        temp_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_conn_url)
        
        # 👇 FIX: "RajDev_Bot" naam hardcode kiya hai taaki 'No default database' error na aaye
        temp_db = temp_client["RajDev_Bot"]
        
        # 3. List and Delete
        collections = await temp_db.list_collection_names()
        
        if not collections:
            await msg.edit("✅ Database pehle se hi khali hai bhai!")
            return

        deleted_names = []
        for col_name in collections:
            await temp_db[col_name].drop()
            deleted_names.append(col_name)
        
        # 4. Success
        await msg.edit(f"✅ **Mission Successful!**\n\n🗑️ Ye collections delete ho gaye:\n`{', '.join(deleted_names)}`\n\nAb bot ekdum naya ho gaya hai.")
        
    except Exception as e:
        await msg.edit(f"❌ Error aaya: {e}")

@app.on_message(filters.command(["personality", "role"]))
async def personality_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/personality dev | hacker | friend | teacher`")
    
    mode = message.command[1].lower()
    
    try:
        msg = ai_engine.change_mode(mode)
        await message.reply(f"⚙️ **System Update:**\n{msg}")
    except:
        ai_engine.personality = mode
        ai_engine.setup_next_key()
        await message.reply(f"✅ Dev ki personality manually set hui: **{mode.upper()}**")

@app.on_message(filters.command("search"))
async def search_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Batao kya search karna hai?")
    query = message.text.split(None, 1)[1]
    wait_msg = await message.reply("🔍 Internet par dhoond raha hu...")
    
    web_data = await search_web(query)
    if web_data:
        res = await ai_engine.get_response(message.from_user.id, f"Summarize this web search for the user: {query}\n\nWeb Data:\n{web_data}")
        await wait_msg.edit(f"✨ **Web Results:**\n\n{res}")
    else:
        await wait_msg.edit("❌ Kuch nahi mila.")

@app.on_message(filters.command("mode") & filters.user(Config.ADMIN_ID))
async def mode_switch(client, message):
    if len(message.command) < 2:
        status = "ON" if SETTINGS["group_auto_reply"] else "OFF"
        return await message.reply(f"Current Group Mode: {status}")
    action = message.command[1].lower()
    if action == "on": SETTINGS["group_auto_reply"] = True; await message.reply("✅ Group Mode: ON")
    elif action == "off": SETTINGS["group_auto_reply"] = False; await message.reply("❌ Group Mode: OFF")

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    if not message.from_user: return
    await db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await message.reply_text(f"**Namaste {message.from_user.first_name}!** 🙏\nMain Raj ka Assistant hu (Dev). Main **RAJ-LLM-MODEL** use karta hu. Padhai mein help chahiye toh puchna!")

@app.on_message(filters.command(["img", "image"]))
async def img_cmd(client, message):
    if len(message.command) < 2: return await message.reply("Prompt likho!")
    prompt = message.text.split(None, 1)[1]
    wait = await message.reply("🎨 Painting ban rahi hai...")
    path = await image_engine.generate_image(prompt)
    if path:
        await message.reply_photo(path, caption=f"Prompt: {prompt}")
        if os.path.exists(path): os.remove(path)
    else: await message.reply("Nahi ban payi.")
    await wait.delete()

# --- 📁 FILE HANDLERS (Vision & PDF) ---

@app.on_message(filters.photo)
async def vision_handler(client, message):
    wait = await message.reply("📸 Photo dekh raha hu ...")
    path = await message.download()
    prompt = message.caption or "Is photo ko samjhao"
    res = await ai_engine.get_response(message.from_user.id, prompt, photo_path=path)
    await wait.delete()
    await send_split_text(client, message.chat.id, res)
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
            res = await ai_engine.get_response(message.from_user.id, f"Summarize this PDF content for a student: {content[:4000]}")
            await wait.edit(f"📝 **PDF Summary:**\n\n{res}")
        except: await wait.edit("PDF padhne mein error aaya.")
        if os.path.exists(path): os.remove(path)

# --- 🧠 MAIN CHAT LOGIC ---

@app.on_message(filters.text & ~filters.command(["start", "img", "search", "stats", "personality", "mode", "cleardb"]))
async def chat_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    is_pvt = message.chat.type == ChatType.PRIVATE
    
    spk_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])

    # 1. SECURITY (Private)
    if is_pvt and text_lower == "raj":
        if not Security.is_waiting(user_id): return await message.reply(Security.initiate_auth(user_id))
    if is_pvt and Security.is_waiting(user_id):
        suc, res, ph = await Security.check_password(user_id, text)
        if ph: await message.reply_photo(ph, caption=res)
        else: await message.reply(res)
        return

    # 🧹 Clean Text
    clean_text = text_lower.replace("dev", "").strip()

    # 2. DATABASE MEMORY (Priority 1)
    ans = await db.get_cached_response(clean_text)
    if ans:
        await message.reply(ans, reply_markup=spk_btn)
        return

    # 3. AI ENGINE (Priority 2)
    if "dev" in text_lower:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        ai_res = await ai_engine.get_response(user_id, text)
        if ai_res:
            await db.add_response(clean_text, ai_res) 
            await send_split_text(client, message.chat.id, ai_res, reply_markup=spk_btn)
            await log_conversation(client, message, ai_res)
        return

    # 4. JSON
    if is_pvt or SETTINGS["group_auto_reply"]:
        j_res = ai_engine.get_json_reply(text)
        if j_res: await message.reply(j_res)

# --- 🔊 OTHER HANDLERS ---

@app.on_callback_query(filters.regex("speak_msg"))
async def speak_cb(client, query):
    t = query.message.text or query.message.caption
    if not t: return
    p = await voice_engine.text_to_speech(t[:1000])
    if p: await client.send_voice(query.message.chat.id, p); os.remove(p)

@app.on_message(filters.voice)
async def voice_msg(client, message):
    m = await message.reply("🎤 Sun raha hu...")
    p = await message.download()
    t = await voice_engine.voice_to_text_and_reply(p)
    ai_res = await ai_engine.get_response(message.from_user.id, t)
    await m.delete()
    spk_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])
    await send_split_text(client, message.chat.id, f"🎤 **Tumne kaha:** {t}\n\n🤖 **Jawab:**\n{ai_res}", reply_markup=spk_btn)
    if os.path.exists(p): os.remove(p)

async def main():
    print(LOGO)
    await start_server()
    await app.start()
    logger.info("🚀 RAJ DEV MEGA BOT (STRICT 2.5 FLASH) ONLINE!")
    await idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
