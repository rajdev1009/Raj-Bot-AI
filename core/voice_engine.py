import edge_tts
import os
import google.generativeai as genai
from config import Config
from utils.logger import logger

class VoiceEngine:
    
    @staticmethod
    async def text_to_speech(text, output_file="response.mp3"):
        """
        Generates voice from text.
        NOTE: edge-tts 6.1.12 update is required for this to work.
        """
        try:
            # Voice change kiya hai jo zyada stable hai
            voice = "en-US-ChristopherNeural"
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)
            return output_file
        except Exception as e:
            logger.error(f"TTS Generation Error: {e}")
            return None

    @staticmethod
    async def voice_to_text_and_reply(voice_path):
        """Uses Gemini 2.5 Flash to listen and reply."""
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            myfile = genai.upload_file(voice_path)
            
            # System Prompt for Voice
            result = await model.generate_content_async(
                [myfile, "Listen to this audio and reply in friendly Hinglish as 'Dev'."]
            )
            return result.text
        except Exception as e:
            logger.error(f"STT Error: {e}")
            return "Awaz saaf nahi aayi boss."

voice_engine = VoiceEngine()
