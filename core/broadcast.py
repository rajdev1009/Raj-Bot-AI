import asyncio
from pyrogram import Client
from database.mongo import db
from utils.logger import logger

async def broadcast_message(app: Client, message):
    users = await db.get_all_users()
    sent_count = 0
    failed_count = 0
    
    for user in users:
        try:
            # Forward or Copy message
            await message.copy(chat_id=user['_id'])
            sent_count += 1
            await asyncio.sleep(0.1) # FloodWait prevention
        except Exception as e:
            failed_count += 1
            
    await db.log_event("broadcast_logs", {
        "sent": sent_count, 
        "failed": failed_count, 
        "admin_id": message.from_user.id
    })
    
    return sent_count, failed_count
  
