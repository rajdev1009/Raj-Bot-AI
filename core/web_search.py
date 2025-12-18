from duckduckgo_search import DDGS
from utils.logger import logger
import asyncio

async def search_web(query):
    """Advanced Search with Error Handling"""
    try:
        # Hum naya instance bana rahe hain taaki session fresh rahe
        with DDGS() as ddgs:
            # Region aur Time limit lagane se block hone ke chances kam hote hain
            results = [r for r in ddgs.text(query, region='wt-wt', safesearch='moderate', timelimit='y', max_results=3)]
            
            if not results:
                return None
                
            summary = ""
            for i, r in enumerate(results, 1):
                summary += f"🌐 Result {i}: {r['title']}\n📝 {r['body'][:200]}...\n\n"
            return summary
            
    except Exception as e:
        if "202" in str(e) or "Ratelimit" in str(e):
            logger.error("⚠️ Search Blocked by DuckDuckGo (Ratelimit).")
            return "SEARCH_BLOCKED"
        logger.error(f"Search Error: {e}")
        return None
        
