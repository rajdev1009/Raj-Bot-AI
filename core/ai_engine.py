import google.generativeai as genai
from config import Config
from utils.logger import logger
import json
import os

# API Key Setup
if Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)
else:
    logger.error("❌ GEMINI_API_KEY missing in .env file!")

class AIEngine:
    def __init__(self):
        # 1. Load JSON Data (Responses)
        self.responses = {}
        try:
            with open("data/responses.json", "r", encoding="utf-8") as f:
                self.responses = json.load(f)
        except Exception as e:
            logger.error(f"JSON Load Error: {e}")

        # 2. System Instruction (Character: Dev)
        self.system_prompt = (
            "You are Dev, a helpful and friendly AI assistant of Raj Dev. "
            "You speak in Hinglish (Hindi + English mix). "
            "You are smart, funny, and loyal to Raj. "
            "Keep answers short and natural like a human chatting on Telegram."
        )

        # 3. Model Setup (Trying Gemini 2.5 Flash)
        self.model = self.initialize_model()

    def initialize_model(self):
        """
        Professional Logic: Pehle 2.5 Flash try karega.
        Agar wo API par available nahi hai, to Crash nahi hoga, 1.5 par switch hoga.
        """
        try:
            logger.info("🤖 Trying to connect with Gemini 2.5 Flash...")
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=self.system_prompt
            )
            logger.info("✅ Gemini 2.5 Flash Connected Successfully!")
            return model
        except Exception as e:
            logger.warning(f"⚠️ Gemini 2.5 Flash Error: {e}")
            logger.info("🔄 Switching to Backup Model (Gemini 1.5 Flash)...")
            return genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=self.system_prompt
            )

    async def get_response(self, user_id, text):
        """
        Gemini AI se response leta hai.
        """
        try:
            if not Config.GEMINI_API_KEY:
                return "❌ API Key nahi mili boss. .env check karo."

            # AI se pucho
            response = await self.model.generate_content_async(text)
            
            # Response text nikalo
            reply = response.text.strip()
            
            # Agar AI ne kuch kharnak/block content diya to
            if not reply:
                return "Hmm, iska jawab mere paas nahi hai."
                
            return reply

        except Exception as e:
            logger.error(f"🔴 AI ERROR: {e}")
            return "Network issue hai ya API Key check karo."

    def get_json_reply(self, text):
        """
        JSON file se fast reply dhoondta hai.
        """
        text = text.lower().strip()
        # Direct Match
        if text in self.responses:
            import random
            return random.choice(self.responses[text])
            
        # Partial Match (Agar sentence mein keyword ho)
        for key, replies in self.responses.items():
            if key in text:
                import random
                return random.choice(replies)
        return None

ai_engine = AIEngine()
