from duckduckgo_search import DDGS
from utils.logger import logger

async def search_web(query):
    """Internet se real-time news aur data nikalta hai"""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if not results: return None
            data = "\n\n".join([f"Title: {r['title']}\nInfo: {r['body']}" for r in results])
            return data
    except Exception as e:
        logger.error(f"Search Error: {e}")
        return None
        
