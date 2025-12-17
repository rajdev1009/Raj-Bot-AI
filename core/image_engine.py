import random
from utils.logger import logger

class ImageEngine:
    
    @staticmethod
    async def generate_image_url(prompt):
        """
        Generates an image URL using Pollinations AI with Random Seed.
        """
        try:
            if not prompt:
                return None
                
            # Random seed add karo taaki image har baar nayi ho
            seed = random.randint(1, 10000)
            clean_prompt = prompt.strip().replace(" ", "%20")
            
            # URL Construction
            url = f"https://image.pollinations.ai/prompt/{clean_prompt}?seed={seed}&nologo=true"
            
            logger.info(f"Image Generated: {prompt}")
            return url
            
        except Exception as e:
            logger.error(f"Image Generation Error: {e}")
            return None

image_engine = ImageEngine()
