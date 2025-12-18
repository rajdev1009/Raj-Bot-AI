import google.generativeai as genai
from config import Config
from utils.logger import logger
import json
import random

class AIEngine:
    def __init__(self):
        self.keys = Config.GEMINI_API_KEYS
        self.current_key_index = 0
        self.responses = {}
        
        try:
            with open("data/responses.json", "r", encoding="utf-8") as f:
                self.responses = json.load(f)
        except:
            logger.error("📂 JSON Response file missing!")

        self.instruction = (
            "You are Dev, Raj Dev's personal assistant from Lumding, Assam. "
            "Speak in natural Hinglish. You are smart and help with studies. "
            "Character: Friendly, loyal, and 100% human-like."
        )
        
        # Pehli key se model setup karo
        self.setup_next_key()

    def setup_next_key(self):
        """Keys ko rotate karta hai agar quota khatam ho jaye."""
        if not self.keys or self.current_key_index >= len(self.keys):
            self.current_key_index = 0 # Reset to first key

        active_key = self.keys[self.current_key_index]
        genai.configure(api_key=active_key)
        
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=self.instruction
        )
        logger.info(f"🔑 Switched to API Key Index: {self.current_key_index}")
        self.current_key_index += 1

    async def get_response(self, user_id, text):
        # 3 baar try karega alag alag keys ke saath
        for attempt in range(len(self.keys)):
            try:
                response = await self.model.generate_content_async(text)
                return response.text.strip()
            except Exception as e:
                if "429" in str(e):
                    logger.warning(f"⚠️ Quota Full for key {self.current_key_index-1}. Rotating...")
                    self.setup_next_key()
                    continue # Agli key se try karo
                else:
                    logger.error(f"🤖 AI Error: {e}")
                    return None
        return "Boss, saari API keys ka quota khatam ho gaya hai. Kal try karte hain!"

    def get_json_reply(self, text):
        text = text.lower().strip()
        if len(text.split()) > 4: return None
        for key, val in self.responses.items():
            if key in text:
                return random.choice(val)
        return None

ai_engine = AIEngine()
