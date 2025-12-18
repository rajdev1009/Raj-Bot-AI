from duckduckgo_search import DDGS
from utils.logger import logger

async def search_web(query):
    try:
        with DDGS() as ddgs:
            # Using basic text search
            results = [r for r in ddgs.text(query, max_results=3)]
            if not results: return None
            summary = "\n\n".join([f"Title: {r['title']}\nInfo: {r['body']}" for r in results])
            return summary
    except Exception as e:
        if "202" in str(e) or "Ratelimit" in str(e):
            return "SEARCH_BLOCKED" # Bot.py handles this
        logger.error(f"Search Error: {e}")
        return None
        
