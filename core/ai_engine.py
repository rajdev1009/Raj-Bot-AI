import json
import random
import google.generativeai as genai
from config import Config
from utils.rate_limiter import limiter
from utils.logger import logger

# API Setup
genai.configure(api_key=Config.GEMINI_API_KEY)

# ✅ UPDATED: Ab hum Gemini 2.5 Flash use kar rahe hain
# 1.5 ab purana ho gaya hai.
model = genai.GenerativeModel('gemini-2.5-flash')

# JSON Responses Load Karna
try:
    with open('data/responses.json', 'r', encoding='utf-8') as f:
        JSON_RESPONSES = json.load(f)
except Exception as e:
    logger.error(f"JSON Error: {e}")
    JSON_RESPONSES = {}

class AIEngine:
    
    @staticmethod
    async def get_response(user_id, text):
        """
        Gemini 2.5 Flash se reply laata hai.
        """
        # 1. Rate Limit Check
        if not limiter.can_use_ai(user_id):
            return None 
        
        # 2. Try Gemini AI
        try:
            logger.info(f"AI 2.5 Request for {user_id}")
            
            # Direct generation
            response = await model.generate_content_async(text)
            
            if response and response.text:
                return response.text
            else:
                return None

        except Exception as e:
            logger.error(f"Gemini 2.5 Error: {e}")
            return "Server update ho raha hai, thodi der baad try karein."

    @staticmethod
    def get_json_reply(text):
        """JSON se fast reply dhoondta hai"""
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
        except Exception as e:
            logger.error(f"Image Error: {e}")
            return "Image samajh nahi aa rahi."

ai_engine = AIEngine()
