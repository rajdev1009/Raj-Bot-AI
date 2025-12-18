import google.generativeai as genai
from config import Config
from utils.logger import logger
import json
import random

if Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)

class AIEngine:
    def __init__(self):
        self.responses = {}
        try:
            with open("data/responses.json", "r", encoding="utf-8") as f:
                self.responses = json.load(f)
        except Exception as e:
            logger.error(f"📂 JSON Load Error: {e}")

        self.instruction = (
            "You are Dev, Raj Dev's personal assistant from Lumding, Assam. "
            "Speak in natural Hinglish. Be friendly, smart, and loyal. "
            "Never mention you are an AI. You are a real person named Dev."
        )
        self.model = self.setup_model()

    def setup_model(self):
        try:
            return genai.GenerativeModel("gemini-2.5-flash", system_instruction=self.instruction)
        except:
            return genai.GenerativeModel("gemini-1.5-flash", system_instruction=self.instruction)

    async def get_response(self, user_id, text):
        try:
            response = await self.model.generate_content_async(text)
            return response.text.strip()
        except Exception as e:
            logger.error(f"🤖 AI Error: {e}")
            return None

    def get_json_reply(self, text):
        """Sirf chote messages (Greetings) par react karega."""
        text = text.lower().strip()
        # 🔒 Agar 4 shabd se bada sentence hai to JSON skip karo (AI handles it)
        if len(text.split()) > 4: return None

        for key, val in self.responses.items():
            if key in text:
                return random.choice(val)
        return None

ai_engine = AIEngine()
