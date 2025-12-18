import google.generativeai as genai
from config import Config
from utils.logger import logger
import json
import os

# API Key Check
if Config.GEMINI_API_KEY:
    genai.configure(api_key=Config.GEMINI_API_KEY)

class AIEngine:
    def __init__(self):
        self.responses = {}
        try:
            with open("data/responses.json", "r", encoding="utf-8") as f:
                self.responses = json.load(f)
        except Exception as e:
            logger.error(f"JSON Load Error: {e}")

        self.system_prompt = (
            "You are Dev, a helpful and friendly AI assistant of Raj Dev. "
            "You speak in Hinglish. Keep answers short and natural."
        )
        self.model = self.initialize_model()

    def initialize_model(self):
        try:
            return genai.GenerativeModel(model_name="gemini-2.5-flash", system_instruction=self.system_prompt)
        except:
            return genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=self.system_prompt)

    async def get_response(self, user_id, text):
        try:
            if not Config.GEMINI_API_KEY: return "API Key Missing."
            response = await self.model.generate_content_async(text)
            return response.text.strip()
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return None

    def get_json_reply(self, text):
        """
        Smart JSON Reply:
        Sirf tab jawab dega jab message chota ho (Greeting type).
        Lambe questions ko ignore karega taaki DB/AI jawab de sake.
        """
        text = text.lower().strip()
        
        # 🔒 LOCK: Agar message 4 words se bada hai, to JSON check mat karo.
        # Example: "Hi" (OK), "Dev help me please" (Ignored by JSON)
        if len(text.split()) > 4:
            return None

        # Direct Match
        if text in self.responses:
            import random
            return random.choice(self.responses[text])
            
        # Keyword Match
        for key, replies in self.responses.items():
            if key in text:
                import random
                return random.choice(replies)
        return None

ai_engine = AIEngine()
