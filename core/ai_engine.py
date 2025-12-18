import google.generativeai as genai
from config import Config
from utils.logger import logger
import json, random
from PIL import Image

class AIEngine:
    def __init__(self):
        # 🔑 Multiple API Keys ki list
        self.keys = Config.GEMINI_API_KEYS
        self.current_key_index = 0
        self.personality = "friend" # Default mood
        self.responses = {}
        
        # 📂 Local JSON responses load karna
        try:
            with open("data/responses.json", "r", encoding="utf-8") as f:
                self.responses = json.load(f)
        except Exception as e:
            logger.error(f"📂 JSON file missing or error: {e}")

        # 🚀 Pehli key ke saath 2.5 Flash setup karo
        self.setup_next_key()

    def get_instruction(self):
        """Dev ki alag-alag personalities ke liye instructions"""
        modes = {
            "friend": "You are Dev, Raj Dev's best friend from Lumding, Assam. Speak in casual Hinglish with emojis. Be very friendly.",
            "teacher": "You are Dev, a helpful and smart teacher. Explain concepts clearly for a student. Use Hinglish.",
            "funny": "You are Dev, a roasting master. Be sarcastic, funny, and use cool Hinglish slangs."
        }
        return modes.get(self.personality, modes["friend"])

    def setup_next_key(self):
        """Agar ek key ka quota khatam ho jaye toh doosri key par switch karta hai"""
        if not self.keys:
            logger.error("❌ No Gemini API Keys found in Config!")
            return

        # Next key select karo
        active_key = self.keys[self.current_key_index % len(self.keys)]
        genai.configure(api_key=active_key)
        
        # --- ⚡ 2025 LATEST MODEL: GEMINI 2.5 FLASH ---
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash", 
            system_instruction=self.get_instruction()
        )
        
        logger.info(f"🔑 Switched to Gemini 2.5 Flash using Key Index: {self.current_key_index % len(self.keys)}")
        self.current_key_index += 1

    async def get_response(self, user_id, text, photo_path=None):
        """AI se reply lene ka main function"""
        # Saari keys try karega agar 429 error aata hai
        for _ in range(len(self.keys)):
            try:
                if photo_path:
                    # 📸 VISION LOGIC: Photo + Text dono 2.5 Flash handle karega
                    img = Image.open(photo_path)
                    content = [text or "Is photo ko dekho aur samjhao", img]
                    response = await self.model.generate_content_async(content)
                else:
                    # 💬 CHAT LOGIC
                    response = await self.model.generate_content_async(text)
                
                return response.text.strip()

            except Exception as e:
                # 🛑 Agar Quota (429) khatam ho gaya toh key badlo
                if "429" in str(e) or "quota" in str(e).lower():
                    logger.warning("⚠️ Quota exhausted for current key. Rotating...")
                    self.setup_next_key()
                    continue 
                
                logger.error(f"🤖 AI Error: {e}")
                return f"Sorry bhai, ek technical error aaya hai: {e}"
        
        return "❌ Boss, saari API keys ka daily quota khatam ho chuka hai!"

    def get_json_reply(self, text):
        """Chote-mote greetings ke liye fast JSON reply"""
        text = text.lower().strip()
        # Agar bada sentence hai toh JSON skip karo, AI ko handle karne do
        if len(text.split()) > 4: 
            return None
            
        for key, val in self.responses.items():
            if key in text:
                return random.choice(val)
        return None

ai_engine = AIEngine()
