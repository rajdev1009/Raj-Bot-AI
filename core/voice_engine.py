import edge_tts
import os
from gtts import gTTS
import google.generativeai as genai
from config import Config
from utils.logger import logger

class VoiceEngine:
    
    @staticmethod
    async def text_to_speech(text, output_file="response.mp3"):
        """
        Dual Engine TTS:
        1. Try Edge TTS (High Quality).
        2. If fails, Fallback to Google TTS (Reliable).
        """
        try:
            # PLAN A: Edge TTS
            voice = "en-US-ChristopherNeural"
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file)
            return output_file
            
        except Exception as e:
            logger.error(f"Edge TTS Failed: {e}. Switching to Google TTS...")
            
            try:
                # PLAN B: Google TTS (Backup)
                tts = gTTS(text=text, lang='hi') # Hindi accent for natural feel
                tts.save(output_file)
                return output_file
            except Exception as e2:
                logger.error(f"Google TTS also failed: {e2}")
                return None

    @staticmethod
    async def voice_to_text_and_reply(voice_path):
        """Uses Gemini 2.5 Flash to listen and reply."""
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            myfile = genai.upload_file(voice_path)
            
            result = await model.generate_content_async(
                [myfile, "Listen to this audio and reply in friendly Hinglish as 'Dev'."]
            )
            return result.text
        except Exception as e:
            logger.error(f"STT Error: {e}")
            return "Awaz saaf nahi aayi boss."

voice_engine = VoiceEngine()
