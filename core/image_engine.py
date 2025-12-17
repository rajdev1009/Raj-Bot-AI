import aiohttp
from utils.logger import logger

class ImageEngine:
    
    @staticmethod
    async def generate_image_url(prompt):
        """Generates an image URL using Pollinations AI (Free & Fast)."""
        try:
            # Formatting prompt for URL
            clean_prompt = prompt.replace(" ", "%20")
            url = f"https://image.pollinations.ai/prompt/{clean_prompt}"
            return url
        except Exception as e:
            logger.error(f"Image Gen Error: {e}")
            return None

image_engine = ImageEngine()
