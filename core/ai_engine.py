import google.generativeai as genai
from config import Config
from utils.logger import logger
from PIL import Image

class AIEngine:
    def __init__(self):
        self.keys = Config.GEMINI_API_KEYS
        self.current_key_index = 0
        self.personality = "friend"
        self.setup_next_key()

    def setup_next_key(self):
        if not self.keys: return
        active_key = self.keys[self.current_key_index % len(self.keys)]
        genai.configure(api_key=active_key)
        self.model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction="You are Dev, Raj Dev's best friend. Speak in Hinglish."
        )
        self.current_key_index += 1

    async def get_response(self, user_id, text, photo_path=None):
        for _ in range(len(self.keys)):
            try:
                if photo_path:
                    img = Image.open(photo_path)
                    res = await self.model.generate_content_async([text or "Explain photo", img])
                else:
                    res = await self.model.generate_content_async(text)
                return res.text.strip()
            except Exception as e:
                if "429" in str(e): self.setup_next_key(); continue
                return f"Error: {e}"
        return "Quota Full!"

ai_engine = AIEngine()
