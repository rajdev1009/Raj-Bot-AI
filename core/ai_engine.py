import json
import random
import google.generativeai as genai
from config import Config
from utils.rate_limiter import limiter
from utils.logger import logger

# Configure Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Load JSON responses
with open('data/responses.json', 'r', encoding='utf-8') as f:
    JSON_RESPONSES = json.load(f)

class AIEngine:
    
    @staticmethod
    async def get_response(user_id, text):
        """Decides between Gemini and JSON based on Rate Limit."""
        text_lower = text.lower().strip()
        
        # 1. Try JSON Fallback (Fastest & Free) if Rate Limited or Simple Match
        if not limiter.can_use_ai(user_id):
            logger.info(f"User {user_id} rate limited. Switching to JSON.")
            return AIEngine.get_json_reply(text_lower)
        
        # 2. If Allowed, use Gemini
        try:
            logger.info(f"Using Gemini AI for {user_id}")
            response = await model.generate_content_async(text)
            return response.text
        except Exception as e:
            logger.error(f"Gemini Error: {e}")
            return AIEngine.get_json_reply(text_lower)

    @staticmethod
    def get_json_reply(text):
        """Fuzzy logic for JSON matching."""
        best_match = None
        
        for key in JSON_RESPONSES:
            if key in text:
                best_match = key
                break
        
        if best_match:
            return random.choice(JSON_RESPONSES[best_match])
        else:
            return "I am resting right now (Rate Limit). Ask me in 1 minute or say 'Hi'."

    @staticmethod
    async def analyze_image(image_path, prompt="Describe this image"):
        try:
            file = genai.upload_file(image_path)
            result = await model.generate_content_async([file, prompt])
            return result.text
        except Exception as e:
            logger.error(f"Image Analysis Error: {e}")
            return "Could not analyze image."

ai_engine = AIEngine()
