import random
import aiohttp
import os
from utils.logger import logger

class ImageEngine:
    def __init__(self):
        self.api_url = "https://image.pollinations.ai/prompt/"

    async def generate_image(self, prompt):
        """
        Pollinations AI se image generate karke download karta hai.
        Returns: Local file path
        """
        try:
            if not prompt: return None
            
            seed = random.randint(1, 999999)
            # Prompt ko URL safe banao
            clean_prompt = prompt.strip().replace(" ", "%20")
            final_url = f"{self.api_url}{clean_prompt}?seed={seed}&nologo=true&width=1024&height=1024"
            
            image_name = f"raj_ai_{seed}.jpg"

            logger.info(f"🎨 Generating Image for: {prompt}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(final_url, timeout=30) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        with open(image_name, "wb") as f:
                            f.write(content)
                        return image_name
                    else:
                        logger.error(f"❌ Image API Error Status: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"❌ Image Engine Crash: {e}")
            return None

image_engine = ImageEngine()
