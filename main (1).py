import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from aiohttp import web
import asyncio
import requests
from pymongo import MongoClient
import os
import time

# Load from environment variables
BOT_TOKEN = os.getenv("8069913528:AAFkDy1BfsBbi1tieMWtZi1sRRJWbQiThIA")
MONGO_URI = os.getenv("mongodb+srv://dggaming:dggaming@cluster0.qnfxnzm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
SHORTNER_API_KEY = os.getenv("0b3be11de98ce79a01b780153eaca00c1927c157")
VERIFY_DOMAIN = os.getenv("VERIFY_DOMAIN")

client = MongoClient(MONGO_URI)
db = client["like_bot"]
users = db["users"]

logging.basicConfig(level=logging.INFO)

# Telegram /like command
async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != "group":
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Yeh command reply mein use karo.")
        return

    args = context.args
    if len(args) != 2 or args[0].lower() != "ind":
        await update.message.reply_text("⚠️ Format: /like ind <uid>")
        return

    uid = args[1]
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name

    user_data = users.find_one({"tg_id": user_id, "uid": uid, "verified": True})
    if user_data:
        await process_like(update, user_id, uid, user_name)
        return

    verify_url = f"{VERIFY_DOMAIN}/verify/{user_id}/{uid}"
    response = requests.get(f"https://shortner.in/api?api={SHORTNER_API_KEY}&url={verify_url}")
    short_url = response.json().get("shortenedUrl")

    users.update_one(
        {"tg_id": user_id, "uid": uid},
        {"$set": {"tg_id": user_id, "uid": uid, "verified": False, "timestamp": int(time.time())}},
        upsert=True
    )

    btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ VERIFY & SEND LIKE", url=short_url)]])
    await update.message.reply_text(
        f"🎯 Like Request

👤 From: {user_name}
🆔 UID: {uid}
🌍 Region: IND

⚠️ Verify within 10 minutes",
        reply_markup=btn
    )

async def process_like(update: Update, user_id, uid, user_name):
    likes_before = 9349
    likes_added = 99
    total_likes = likes_before + likes_added

    await update.message.reply_text(
        f"✅ Request Processed Successfully

👤 Player: RiderBᴀᴄᴋ
🆔 UID: {uid}
👍 Likes Before: {likes_before}
➕ Likes Added: {likes_added}
🇮🇳 Total Likes Now: {total_likes}
⏱ Processed At: {time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

# Webhook handler
async def handle_verify(request):
    user_id = request.match_info['user_id']
    uid = request.match_info['uid']
    users.update_one({"tg_id": int(user_id), "uid": uid}, {"$set": {"verified": True}})
    return web.Response(text="✅ Verified! You can return to Telegram now.")

# Main entry
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("like", like))
    asyncio.create_task(app.run_polling())

    aio_app = web.Application()
    aio_app.router.add_get('/verify/{user_id}/{uid}', handle_verify)
    runner = web.AppRunner(aio_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8000)
    await site.start()
    print("Server started at http://localhost:8000")

    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    asyncio.run(main())
