import logging

# Logger setup
logger = logging.getLogger("RajBot")

class ImageEngine:
    
    @staticmethod
    async def generate_image_url(prompt):
        """
        Generates an image URL using Pollinations AI.
        This is API-free and works via URL manipulation.
        """
        try:
            if not prompt:
                return None
                
            # Clean prompt for URL
            clean_prompt = prompt.strip().replace(" ", "%20")
            
            # Construct URL
            url = f"https://image.pollinations.ai/prompt/{clean_prompt}"
            
            logger.info(f"Image URL generated for prompt: {prompt}")
            return url
            
        except Exception as e:
            logger.error(f"Image Generation Error: {e}")
            return None

# Singleton instance
image_engine = ImageEngine()
