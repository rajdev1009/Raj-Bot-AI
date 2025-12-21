import asyncio
import os
import io
import sys
import contextlib
import fitz  # PyMuPDF
from pyrogram import Client, filters, idle
from pyrogram.enums import ChatAction, ChatType
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- IMPORTING CUSTOM MODULES ---
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

# =========================================================================
# 🎨 STARTUP LOGO (ORIGINAL RAJ DEV SYSTEMS ALIGNMENT)
# =========================================================================
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

# =========================================================================
# 🐍 ADVANCED PYTHON CODE INTERPRETER ENGINE
# =========================================================================
def execute_python_code(code):
    """
    Executes Python code in a controlled environment.
    Captures stdout and returns the output or errors.
    """
    # Security Blacklist for Sandbox
    forbidden_keywords = [
        "os.", "sys.", "shutil.", "subprocess", "open(", 
        "eval(", "exec(", "getattr", "setattr", "delattr"
    ]
    
    for word in forbidden_keywords:
        if word in code.lower():
            return f"❌ SECURITY ALERT: Use of '{word}' is strictly prohibited in Raj Dev Systems."

    output_buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(output_buffer):
            # Executing the user provided code
            exec(code)
        
        execution_result = output_buffer.getvalue()
        if not execution_result:
            return "✅ Execution Successful! (Note: Your code produced no output. Use print() to see results.)"
        return execution_result
        
    except Exception as err:
        return f"❌ PYTHON EXECUTION ERROR:\n---\n{str(err)}"

# =========================================================================
# 🤖 BOT INITIALIZATION
# =========================================================================
app = Client(
    "RajBot_Session",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Global Settings Dictionary
BOT_SETTINGS = {
    "group_auto_reply": False,
    "maintenance_mode": False
}

# =========================================================================
# 🛠️ UTILITY FUNCTIONS (LONG TEXT & LOGGING)
# =========================================================================
async def send_heavy_text(client, chat_id, text, reply_markup=None):
    """Handles Telegram's 4096 character limit by splitting text into chunks."""
    if not text:
        return
    
    if len(text) <= 4000:
        await client.send_message(chat_id, text, reply_markup=reply_markup)
    else:
        # Breaking long content into chunks of 4000 characters
        for i in range(0, len(text), 4000):
            chunk = text[i:i+4000]
            # Add reply_markup only to the last chunk
            current_markup = reply_markup if i + 4000 >= len(text) else None
            await client.send_message(chat_id, chunk, reply_markup=current_markup)
            await asyncio.sleep(0.5) # Prevent flood wait

async def log_to_channel(client, user, input_msg, bot_output):
    """Logs detailed conversation data to the designated log channel."""
    if not Config.LOG_CHANNEL_ID:
        return
    
    log_content = (
        f"🛰 **RAJ DEV SYSTEM LOGS**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **User:** {user.mention} [`{user.id}`]\n"
        f"📥 **Input:** {input_msg}\n"
        f"🤖 **Bot Reply:** {bot_output[:500]}..."
    )
    try:
        await client.send_message(Config.LOG_CHANNEL_ID, log_content)
    except Exception as e:
        logger.error(f"Logging Error: {e}")

# =========================================================================
# 🎮 CORE COMMAND HANDLERS
# =========================================================================

@app.on_message(filters.command(["run", "py"]) & filters.user(Config.ADMIN_ID))
async def python_interpreter_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("**Batao Raj Bhai, kaunsa code run karna hai?**\nExample: `/run print(10+20)`")
    
    code_to_run = message.text.split(None, 1)[1]
    status_msg = await message.reply("⏳ **Processing Python script...**")
    
    result = execute_python_code(code_to_run)
    
    await status_msg.edit(
        f"🐍 **PYTHON INTERPRETER OUTPUT:**\n\n"
        f"```python\n{result}\n```"
    )

@app.on_message(filters.command("stats") & filters.user(Config.ADMIN_ID))
async def bot_stats_handler(client, message):
    total_users, total_memory = await db.get_stats()
    stats_text = (
        f"📊 **RAJ DEV SYSTEMS - LIVE STATS**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Total Users:** {total_users}\n"
        f"🧠 **AI Memory Slots:** {total_memory}\n"
        f"🚀 **Model Version:** Gemini 2.5 Flash\n"
        f"🔋 **Server Status:** Optimal"
    )
    await message.reply_text(stats_text)

@app.on_message(filters.command("cleardb") & filters.user(Config.ADMIN_ID))
async def clear_db_handler(client, message):
    warning_msg = await message.reply("⚠️ **Initiating Database Wipe... Please wait.**")
    try:
        mongo_url = getattr(Config, "MONGO_URI", getattr(Config, "MONGO_URL", None))
        import motor.motor_asyncio
        temp_conn = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        target_db = temp_conn["RajDev_Bot"]
        
        collections = await target_db.list_collection_names()
        for col in collections:
            await target_db[col].drop()
            
        await warning_msg.edit("✅ **DATABASE SUCCESSFULLY WIPED.**\nAll memories and user records have been cleared.")
    except Exception as e:
        await warning_msg.edit(f"❌ **DB WIPE ERROR:** {str(e)}")

@app.on_message(filters.command(["personality", "role"]))
async def change_role_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/personality dev | hacker | friend | teacher | funny` ")
    
    selected_mode = message.command[1].lower()
    update_response = ai_engine.change_mode(selected_mode)
    await message.reply(f"🛠 **System Configuration Updated:**\n{update_response}")

@app.on_message(filters.command("search"))
async def web_search_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("🔍 **Kya search karna hai?**\nExample: `/search latest tech news` ")
    
    user_query = message.text.split(None, 1)[1]
    search_msg = await message.reply(f"🔍 **Searching the web for:** `{user_query}`...")
    
    web_raw_data = await search_web(user_query)
    if not web_raw_data:
        return await search_msg.edit("❌ **Search Engine Error:** No data found for this query.")
    
    # Process web data through AI for a clean summary
    ai_summary = await ai_engine.get_response(
        message.from_user.id, 
        f"Please analyze and summarize this web search result for the user: {web_raw_data}"
    )
    
    await search_msg.edit(f"🌐 **WEB SEARCH RESULTS:**\n\n{ai_summary}")

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    if not message.from_user: return
    # Registering user in MongoDB
    await db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    
    welcome_text = (
        f"**Namaste {message.from_user.first_name}!** 🙏\n\n"
        f"Welcome to **Raj Dev Systems**. I am an Advanced AI Model with Gemini 2.5 Flash architecture.\n\n"
        f"🎨 **Try:** `/img [prompt]` to generate art.\n"
        f"📄 **Try:** Sending me a PDF to analyze.\n"
        f"📸 **Try:** Sending me a photo to talk about it."
    )
    await message.reply_text(welcome_text)

@app.on_message(filters.command(["img", "image"]))
async def image_gen_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("🎨 **Please provide a prompt!**\nExample: `/img a futuristic city` ")
    
    user_prompt = message.text.split(None, 1)[1]
    progress = await message.reply("🎨 **Generating image... this might take a few seconds.**")
    
    image_path = await image_engine.generate_image(user_prompt)
    if image_path:
        await message.reply_photo(image_path, caption=f"🎨 **Prompt:** {user_prompt}")
        if os.path.exists(image_path): os.remove(image_path)
    else:
        await message.reply("❌ **Image Engine Error:** Failed to generate image.")
    await progress.delete()

# =========================================================================
# 📁 FILE & MEDIA ANALYSIS HANDLERS
# =========================================================================

@app.on_message(filters.photo)
async def vision_photo_analysis(client, message):
    """Analyze photos using Gemini Vision API."""
    loading = await message.reply("📸 **Analyzing image pixels...**")
    photo_file = await message.download()
    
    user_caption = message.caption or "Analyze this image and tell me what's inside."
    
    analysis_result = await ai_engine.get_response(
        message.from_user.id, 
        user_caption, 
        photo_path=photo_file
    )
    
    await loading.delete()
    await send_heavy_text(client, message.chat.id, f"🖼 **IMAGE ANALYSIS:**\n\n{analysis_result}")
    
    if os.path.exists(photo_file):
        os.remove(photo_file)

@app.on_message(filters.document)
async def document_analysis_handler(client, message):
    """Analyze PDF documents."""
    if message.document.mime_type == "application/pdf":
        loading_pdf = await message.reply("📄 **Downloading and reading PDF...**")
        pdf_file = await message.download()
        
        try:
            pdf_doc = fitz.open(pdf_file)
            pdf_text = ""
            for page in pdf_doc:
                pdf_text += page.get_text()
            pdf_doc.close()
            
            summary = await ai_engine.get_response(
                message.from_user.id, 
                f"Please provide a detailed summary of this PDF content: {pdf_text[:4000]}"
            )
            
            await loading_pdf.edit(f"📝 **PDF DOCUMENT SUMMARY:**\n\n{summary}")
        except Exception as e:
            await loading_pdf.edit(f"❌ **PDF ERROR:** Could not read document. {e}")
        
        if os.path.exists(pdf_file):
            os.remove(pdf_file)

# =========================================================================
# 🧠 ADVANCED CHAT HANDLER (MEMORY + JSON + AI)
# =========================================================================

@app.on_message(filters.text & ~filters.command(["start", "img", "search", "stats", "personality", "cleardb", "run", "py"]))
async def main_chat_handler(client, message):
    if not message.from_user: return
    
    user_id = message.from_user.id
    input_text = message.text.strip()
    input_lower = input_text.lower()
    is_private_chat = message.chat.type == ChatType.PRIVATE
    
    # Text-to-Speech Button
    tts_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Speak Response", callback_data="speak_msg")]])

    # --- 1. RAJ AUTHENTICATION SYSTEM ---
    if is_private_chat and input_lower == "raj":
        if not Security.is_waiting(user_id):
            return await message.reply(Security.initiate_auth(user_id))
            
    if is_private_chat and Security.is_waiting(user_id):
        is_success, auth_msg, photo_auth = await Security.check_password(user_id, input_text)
        if photo_auth:
            await message.reply_photo(photo_auth, caption=auth_msg)
        else:
            await message.reply(auth_msg)
        return

    # --- 2. CACHED RESPONSE (DATABASE MEMORY) ---
    clean_query = input_lower.replace("dev", "").strip()
    cached_reply = await db.get_cached_response(clean_query)
    if cached_reply:
        return await message.reply(cached_reply, reply_markup=tts_markup)

    # --- 3. AI GENERATION (MAIN ENGINE) ---
    # Trigger AI in private chats OR if 'dev' is mentioned in groups
    if is_private_chat or "dev" in input_lower:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        ai_reply = await ai_engine.get_response(user_id, input_text)
        
        if ai_reply:
            # Saving to Database Cache for future use
            await db.add_response(clean_query, ai_reply)
            
            await send_heavy_text(client, message.chat.id, ai_reply, reply_markup=tts_markup)
            await log_to_channel(client, message.from_user, input_text, ai_reply)
        return

    # --- 4. JSON FALLBACK (LOCAL DATA) ---
    if is_private_chat or BOT_SETTINGS["group_auto_reply"]:
        local_json_res = ai_engine.get_json_reply(input_text)
        if local_json_res:
            await message.reply(local_json_res)

# =========================================================================
# 🔊 VOICE & AUDIO PROCESSING
# =========================================================================

@app.on_callback_query(filters.regex("speak_msg"))
async def tts_callback_handler(client, query):
    """Trigger Text-To-Speech from a button click."""
    text_to_speak = query.message.text or query.message.caption
    if not text_to_speak: return
    
    audio_path = await voice_engine.text_to_speech(text_to_speak[:1000])
    if audio_path:
        await client.send_voice(query.message.chat.id, audio_path)
        if os.path.exists(audio_path): os.remove(audio_path)

@app.on_message(filters.voice)
async def voice_note_handler(client, message):
    """Processes incoming voice notes, converts to text, and replies with AI."""
    processing_voice = await message.reply("🎤 **Analyzing your voice note...**")
    voice_file = await message.download()
    
    transcribed_text = await voice_engine.voice_to_text_and_reply(voice_file)
    
    # Noise Filter
    if not transcribed_text or len(transcribed_text) < 3:
        if os.path.exists(voice_file): os.remove(voice_file)
        return await processing_voice.edit("❌ **AUDIO ERROR:** Could not understand voice. Please speak clearly.")
    
    # Getting AI reply for transcribed text
    ai_voice_reply = await ai_engine.get_response(message.from_user.id, transcribed_text)
    
    await processing_voice.delete()
    tts_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Speak Reply", callback_data="speak_msg")]])
    
    final_voice_res = (
        f"🎤 **TRANSCRIBED:** `{transcribed_text}`\n\n"
        f"🤖 **DEV REPLY:** {ai_voice_reply}"
    )
    
    await send_heavy_text(client, message.chat.id, final_voice_res, reply_markup=tts_btn)
    
    if os.path.exists(voice_file):
        os.remove(voice_file)

# =========================================================================
# 🚀 SYSTEM BOOTSTRAP
# =========================================================================

async def system_boot():
    """Main function to start all services."""
    print(LOGO)
    
    # Starting Flask/Health Check Server
    await start_server()
    
    # Starting Pyrogram Client
    await app.start()
    
    logger.info("🚀 RAJ DEV MEGA BOT IS NOW OPERATIONAL [GEN-2.5]")
    print(">>> SYSTEM IS ONLINE. WAITING FOR MESSAGES...")
    
    # Keeping the bot running
    await idle()
    
    # Stop services on exit
    await app.stop()

if __name__ == "__main__":
    # Standard Python loop to run the async boot function
    try:
        asyncio.get_event_loop().run_until_complete(system_boot())
    except KeyboardInterrupt:
        pass
        
