import edge_tts
import os
import google.generativeai as genai
from config import Config
from utils.logger import logger

class VoiceEngine:
    
    @staticmethod
    async def text_to_speech(text, output_file="response.mp3"):
        """Generates voice from text."""
        communicate = edge_tts.Communicate(text, "en-US-ChristopherNeural")
        await communicate.save(output_file)
        return output_file

    @staticmethod
    async def voice_to_text_and_reply(voice_path):
        """Uses Gemini Multimodal to listen to audio and reply."""
        try:
            # Upload to Gemini
            myfile = genai.upload_file(voice_path)
            
            # Prompt Gemini to listen and reply
            model = genai.GenerativeModel('gemini-1.5-flash')
            result = await model.generate_content_async(
                [myfile, "Listen to this audio, understand it, and reply in text."]
            )
            return result.text
        except Exception as e:
            logger.error(f"Voice Error: {e}")
            return "Sorry, I couldn't hear that clearly."

voice_engine = VoiceEngine()
