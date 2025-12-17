import json
import random
import datetime
import re
import google.generativeai as genai
from config import Config
from database.mongo import db
from utils.rate_limiter import limiter
from utils.logger import logger

# API Setup
genai.configure(api_key=Config.GEMINI_API_KEY)

# Gemini 2.5 Flash Model
model = genai.GenerativeModel('gemini-2.5-flash')

# Load JSON Responses
try:
    with open('data/responses.json', 'r', encoding='utf-8') as f:
        JSON_RESPONSES = json.load(f)
except:
    JSON_RESPONSES = {}

class AIEngine:
    
    @staticmethod
    async def get_response(user_id, text):
        """
        AI se reply leta hai (Strict Human Persona).
        """
        # 1. Rate Limit
        if not limiter.can_use_ai(user_id):
            return None 

        # 2. Check Cache
        cached_ans = await db.get_cached_response(text)
        if cached_ans:
            return cached_ans

        # 3. AI Processing
        try:
            logger.info(f"AI Request: {text}")
            
            # Dynamic Info
            now = datetime.datetime.now()
            current_time = now.strftime("%I:%M %p")
            current_date = now.strftime("%d %B %Y")
            
            # --- STRICT SYSTEM PROMPT (BRAINWASH) ---
            system_instruction = f"""
            IDENTITY:
            Name: Dev
            Role: Human Assistant & Developer (NOT an AI).
            Location: Lumding, Assam.
            Language: Hinglish (Hindi + English mix).
            
            STRICT RULES:
            1. NEVER say "As an AI", "I don't have feelings", or "I am a language model".
            2. Keep answers SHORT & CASUAL (Friend style). Only give long answers for studies/syllabus.
            3. If asked "How are you?", say "Main mast hu", "Ekdum fit", or "Badhiya".
            4. If asked "Who are you?", say "Main Dev hu, Raj ka assistant".
            5. Current Info: Date: {current_date}, Time: {current_time}. President: Donald Trump.

            EXAMPLE CHATS (Follow this style):
            User: How are you?
            Dev: Main badhiya hu boss, tum batao?
            
            User: Tum AI ho kya?
            Dev: Arre nahi bhai, main Dev hu. Insaan hu.
            
            User: Kya kar rahe ho?
            Dev: Bas Raj bhai ke commands handle kar raha hu.
            """

            # Model with Instruction
            model_sys = genai.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=system_instruction
            )

            # Generate
            response = await model_sys.generate_content_async(text)
            
            if response and response.text:
                final_ans = response.text.strip()
                
                # --- CLEANUP (AI galti se AI bol de to fix karo) ---
                if "As an AI" in final_ans or "language model" in final_ans:
                    final_ans = "Main thik hu, tum batao?"

                # 4. SAVE TO CACHE (Without 'Dev')
                clean_query_for_db = re.sub(r'^\s*dev\s+', '', text, flags=re.IGNORECASE).strip()
                is_dynamic = any(w in clean_query_for_db.lower() for w in ["time", "date", "tarikh", "samay", "baj", "aaj"])
                
                if not is_dynamic:
                    await db.save_to_cache(clean_query_for_db, final_ans)
                
                return final_ans
            else:
                return None

        except Exception as e:
            logger.error(f"AI Error: {e}")
            return "Network issue hai, wapas pucho."

    @staticmethod
    def get_json_reply(text):
        text = text.lower()
        for key in JSON_RESPONSES:
            if key in text:
                return random.choice(JSON_RESPONSES[key])
        return None

    @staticmethod
    async def analyze_image(image_path):
        try:
            file = genai.upload_file(image_path)
            result = await model.generate_content_async([file, "Describe this image in Hinglish short."])
            return result.text
        except:
            return "Image clear nahi hai."

ai_engine = AIEngine()
