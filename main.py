import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
OPENCODE_API_KEY = os.environ.get("OPENCODE_API_KEY")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id

    await context.bot.send_message(chat_id=chat_id, text="🤖 MettleX AI กำลังประมวลผล...")

    try:
        headers = {
            "Authorization": f"Bearer {OPENCODE_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [{"role": "user", "content": user_text}]
        }

        response = requests.post("https://api.opencode.ai/v1/chat/completions", headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            data = response.json()
            reply_text = data.get("choices", [{}])[0].get("message", {}).get("content", str(data))
        else:
            reply_text = f"❌ API Error ({response.status_code}): {response.text}"

    except Exception as e:
        reply_text = f"❌ เกิดข้อผิดพลาด: {str(e)}"

    await context.bot.send_message(chat_id=chat_id, text=reply_text)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🚀 Telegram Bot is running on Cloud!")
    app.run_polling()
