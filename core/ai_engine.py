import google.generativeai as genai
from config import Config
from utils.logger import logger
import json, random
from PIL import Image

class AIEngine:
    def __init__(self):
        self.keys = Config.GEMINI_API_KEYS
        self.current_key_index = 0
        self.personality = "friend" # Default: friend
        self.responses = {}
        
        try:
            with open("data/responses.json", "r", encoding="utf-8") as f:
                self.responses = json.load(f)
        except: logger.error("Responses JSON file missing!")

        self.setup_next_key()

    def get_instruction(self):
        modes = {
            "friend": "You are Dev, Raj Dev's best friend. Speak in casual Hinglish with emojis.",
            "teacher": "You are Dev, a helpful teacher. Explain concepts simply and detail-oriented.",
            "funny": "You are Dev, very sarcastic and funny. Roast gently and use heavy Hinglish."
        }
        return modes.get(self.personality, modes["friend"])

    def setup_next_key(self):
        if not self.keys: return
        active_key = self.keys[self.current_key_index % len(self.keys)]
        genai.configure(api_key=active_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", # Vision ke liye stable hai
            system_instruction=self.get_instruction()
        )
        self.current_key_index += 1

    async def get_response(self, user_id, text, photo_path=None):
        for _ in range(len(self.keys)):
            try:
                if photo_path:
                    img = Image.open(photo_path)
                    content = [text or "Is photo ko samjhao", img]
                    response = await self.model.generate_content_async(content)
                else:
                    response = await self.model.generate_content_async(text)
                return response.text.strip()
            except Exception as e:
                if "429" in str(e): 
                    self.setup_next_key()
                    continue
                return f"Error: {e}"
        return "Saari Keys ka Quota khatam!"

    def get_json_reply(self, text):
        text = text.lower().strip()
        if len(text.split()) > 4: return None
        for key, val in self.responses.items():
            if key in text: return random.choice(val)
        return None

ai_engine = AIEngine()
