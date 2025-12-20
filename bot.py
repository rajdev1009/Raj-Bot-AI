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
from core.security import Security
from utils.logger import logger
from utils.server import start_server

# --- 🎨 LOGO ---
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

# --- 🎚️ SETTINGS ---
SETTINGS = {
    "group_auto_reply": False
}

# --- 🛠️ HELPER: Long Message Splitter ---
async def send_split_text(client, chat_id, text, reply_markup=None):
    """Agar message 4096 chars se bada hai to tukdon me bhejo"""
    if len(text) < 4000:
        await client.send_message(chat_id, text, reply_markup=reply_markup)
    else:
        # Split logic
        chunk_size = 4000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        for i, chunk in enumerate(chunks):
            # Sirf last chunk pe button lagao
            markup = reply_markup if i == len(chunks) - 1 else None
            await client.send_message(chat_id, chunk, reply_markup=markup)

# --- 🎮 COMMANDS ---

@app.on_message(filters.command(["personality", "role"]))
async def personality_handler(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: `/personality hacker` | `dev` | `friend`")
    
    mode = message.command[1].lower()
    try:
        msg = ai_engine.change_mode(mode)
        await message.reply(f"⚙️ **System Update:**\n{msg}")
    except:
        await message.reply("❌ Error changing mode.")

@app.on_message(filters.command("mode"))
async def group_mode_switch(client, message):
    """Group me auto-reply ON/OFF karne ke liye"""
    if len(message.command) < 2:
        status = "ON" if SETTINGS["group_auto_reply"] else "OFF"
        return await message.reply(f"📢 Current Group Mode: **{status}**")
    
    action = message.command[1].lower()
    if action in ["on", "enable"]:
        SETTINGS["group_auto_reply"] = True
        await message.reply("✅ Group Mode: **ON** (Ab main group me sabse baat karunga)")
    elif action in ["off", "disable", "of"]: # 'of' typo fix
        SETTINGS["group_auto_reply"] = False
        await message.reply("❌ Group Mode: **OFF** (Ab sirf 'Dev' bolne par reply karunga)")

@app.on_message(filters.command(["img", "image"]))
async def img_cmd(client, message):
    if len(message.command) < 2: return await message.reply("Likho kaisa image chahiye. Ex: `/img Iron Man`")
    prompt = message.text.split(None, 1)[1]
    wait = await message.reply("🎨 Painting bana raha hu... (Wait)")
    try:
        path = await image_engine.generate_image(prompt)
        if path:
            await message.reply_photo(path, caption=f"Prompt: {prompt}")
            if os.path.exists(path): os.remove(path)
        else:
            await message.reply("❌ Server busy hai, image nahi ban payi.")
    except Exception as e:
        await message.reply(f"Error: {e}")
    await wait.delete()

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await db.add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    await message.reply_text(f"👋 Namaste **{message.from_user.first_name}**!\n\nMain **Raj Dev** ka AI Assistant hu.\n\nCommands:\n`/img [text]` - Photo banao\n`/personality hacker` - Mode badlo\n`/mode on` - Group reply on")

# --- 📁 FILES & VISION ---

@app.on_message(filters.photo & filters.private)
async def vision_handler(client, message):
    wait = await message.reply("👀 Dekh raha hu...")
    path = await message.download()
    prompt = message.caption or "Is photo me kya hai?"
    res = await ai_engine.get_response(message.from_user.id, prompt, photo_path=path)
    await wait.delete()
    await send_split_text(client, message.chat.id, res)
    if os.path.exists(path): os.remove(path)

# --- 🧠 MAIN CHAT LOGIC (JSON + AI Mixed) ---

@app.on_message(filters.text & ~filters.command(["start", "img", "search", "mode", "personality"]))
async def chat_handler(client, message):
    if not message.from_user: return
    user_id = message.from_user.id
    text = message.text.strip()
    text_lower = text.lower()
    is_pvt = message.chat.type == ChatType.PRIVATE
    
    # Button for audio
    spk_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])

    # 1. SECURITY CHECK (Private only)
    if is_pvt and text_lower == "raj":
        if not Security.is_waiting(user_id): return await message.reply(Security.initiate_auth(user_id))
    if is_pvt and Security.is_waiting(user_id):
        suc, res, ph = await Security.check_password(user_id, text)
        if ph: await message.reply_photo(ph, caption=res)
        else: await message.reply(res)
        return

    # 🧹 'Dev' keyword hatao processing ke liye
    clean_text = text_lower.replace("dev", "").strip()

    # 2. JSON REPLY (Sabse Pehle Check Hoga!) ⚡
    # Agar simple hello/hi hai to AI use mat karo, JSON se reply do (Fast)
    json_reply = ai_engine.get_json_reply(text)
    
    # Logic: Agar JSON reply mila AND (user ne specific sawal nahi pucha)
    if json_reply and len(text.split()) < 5: 
        await message.reply(json_reply)
        return # Yahin ruk jao, AI ko mat bulao

    # 3. AI ENGINE (Agar JSON me jawab nahi mila ya sentence bada hai)
    # Trigger: Private chat hai YA message me "dev" likha hai YA Group Mode ON hai
    should_reply = is_pvt or ("dev" in text_lower) or (SETTINGS["group_auto_reply"] and not message.service)
    
    if should_reply:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        
        # Memory Check
        cached_res = await db.get_cached_response(clean_text)
        if cached_res:
            await send_split_text(client, message.chat.id, cached_res, reply_markup=spk_btn)
            return

        # Fetch from Gemini
        ai_res = await ai_engine.get_response(user_id, text)
        
        if ai_res:
            await db.add_response(clean_text, ai_res) # Save logic
            # 👇 Yahan SPLIT function use kiya hai taaki lamba message error na de
            await send_split_text(client, message.chat.id, ai_res, reply_markup=spk_btn)
            
            # Logger
            chat_type = "Private" if is_pvt else "Group"
            logger.info(f"🤖 AI Reply to {message.from_user.first_name} ({chat_type})")

# --- 🔊 AUDIO HANDLERS ---

@app.on_callback_query(filters.regex("speak_msg"))
async def speak_cb(client, query):
    await query.answer("🔊 Processing audio...")
    # Message ka text uthao
    text_to_speak = query.message.text or query.message.caption
    if not text_to_speak: return
    
    # Sirf pehle 200 words bolo (Taki bot hang na ho)
    short_text = text_to_speak[:1000] 
    
    audio_path = await voice_engine.text_to_speech(short_text)
    if audio_path:
        await client.send_voice(query.message.chat.id, audio_path)
        os.remove(audio_path)
    else:
        await query.message.reply("❌ Audio generation failed.")

@app.on_message(filters.voice)
async def voice_msg_handler(client, message):
    wait = await message.reply("🎤 Sun raha hu...")
    voice_path = await message.download()
    
    # 1. Voice to Text
    text = await voice_engine.voice_to_text_and_reply(voice_path)
    if not text:
        await wait.edit("❌ Samajh nahi aaya.")
        return

    # 2. Get AI Response
    ai_res = await ai_engine.get_response(message.from_user.id, text)
    
    # 3. Reply (Text + Button)
    spk_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔊 Suno", callback_data="speak_msg")]])
    await wait.delete()
    await send_split_text(client, message.chat.id, f"🎤 **Tumne kaha:** {text}\n\n🤖 **Jawab:**\n{ai_res}", reply_markup=spk_btn)
    
    if os.path.exists(voice_path): os.remove(voice_path)

# --- SERVER START ---
async def main():
    print(LOGO)
    await start_server()
    await app.start()
    logger.info("🚀 RAJ DEV MEGA BOT (ALL SYSTEMS FIXED) ONLINE!")
    await idle()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    
