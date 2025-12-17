from aiohttp import web
from config import Config
from utils.logger import logger

async def web_handler(request):
    """Returns a simple status to satisfy Health Checks."""
    return web.Response(text="Raj Bot is Running 24/7 🚀", status=200)

async def start_server():
    """Starts the Async Web Server on Port 8080."""
    app = web.Application()
    app.router.add_get("/", web_handler)
    app.router.add_get("/health", web_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Binds to 0.0.0.0:8080
    site = web.TCPSite(runner, "0.0.0.0", Config.PORT)
    await site.start()
    logger.info(f"🌍 Web Server running on Port {Config.PORT}")
  
