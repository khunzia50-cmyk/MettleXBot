import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 10000))

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

    def log_message(self, format, *args):
        return

def run_http_server():
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    httpd.serve_forever()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user_message = update.message.text
    chat_id = update.message.chat_id

    status_message = await context.bot.send_message(
        chat_id=chat_id, 
        text="⚡ MettleX AI กำลังประมวลผล..."
    )

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}".strip(),
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional video scriptwriter assistant."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7
        }

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            res_data = response.json()
            reply_text = res_data["choices"][0]["message"]["content"]
        else:
            reply_text = f"❌ API Error ({response.status_code}): {response.text}"

        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message.message_id,
            text=reply_text
        )

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message.message_id,
            text=f"❌ เกิดข้อผิดพลาด: {str(e)}"
        )

def main():
    if not BOT_TOKEN or not GROQ_API_KEY:
        print("❌ Error: Missing Tokens")
        return

    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()
    print(f"🌐 HTTP Server started on port {PORT}")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🚀 Telegram Bot is running!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
