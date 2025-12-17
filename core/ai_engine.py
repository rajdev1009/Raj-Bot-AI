import json
import random
import google.generativeai as genai
from config import Config
from utils.rate_limiter import limiter
from utils.logger import logger

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Load JSON
with open('data/responses.json', 'r', encoding='utf-8') as f:
    JSON_RESPONSES = json.load(f)

class AIEngine:
    
    @staticmethod
    async def get_response(user_id, text):
        """
        Agar user question puche aur time limit baki ho -> AI Reply
        Agar limit over ho ya simple chat ho -> Return None (Taaki JSON use ho)
        """
        text_lower = text.lower().strip()
        
        # 1. Rate Limit Check (Silent)
        if not limiter.can_use_ai(user_id):
            return None # Chupchap JSON par shift ho jao
        
        # 2. Try Gemini AI
        try:
            logger.info(f"AI Processing for {user_id}")
            response = await model.generate_content_async(text)
            return response.text
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return None # Error aaya to bhi JSON use karo

    @staticmethod
    def get_json_reply(text):
        """Finds best match from JSON"""
        text = text.lower()
        
        # Exact/Partial Match Search
        for key in JSON_RESPONSES:
            if key in text:
                return random.choice(JSON_RESPONSES[key])
        
        # Agar kuch na mile
        return random.choice(JSON_RESPONSES["default"])

    @staticmethod
    async def analyze_image(image_path):
        try:
            file = genai.upload_file(image_path)
            result = await model.generate_content_async([file, "Describe this image in Hinglish short."])
            return result.text
        except:
            return "Image samajh nahi aa rahi."

ai_engine = AIEngine()
