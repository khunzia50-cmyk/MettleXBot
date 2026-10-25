import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 1. เว็บเซิร์ฟเวอร์จิ๋วสำหรับ Render Port Binding
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"MettleX Groq Bot is running!")

def run_http_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# รันเซิร์ฟเวอร์แยกเป็น Thread เบื้องหลัง
threading.Thread(target=run_http_server, daemon=True).start()

# 2. อ่านค่า API Key และ Token จาก Environment Variables ของ Render
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    await context.bot.send_message(chat_id=chat_id, text="⚡ MettleX AI (Groq) กำลังประมวลผล...")
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system", 
                    "content": "คุณคือผู้เชี่ยวชาญด้านการเขียนสคริปต์ Python, MoviePy, FFmpeg, ระบบการตัดต่อวิดีโออัตโนมัติ และการออกแบบวิดีโอสั้นแบบรวดเร็ว"
                },
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.5
        }
        
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
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
    print("🚀 Telegram Bot with Groq is running!")
    app.run_polling()
