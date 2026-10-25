import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# 1. เว็บเซิร์ฟเวอร์จิ๋วสำหรับ Render Port Binding (ป้องกัน Render ขึ้น No open ports)
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
    
    # ส่งข้อความแจ้งผู้ใช้ว่ากำลังประมวลผล
    await context.bot.send_message(chat_id=chat_id, text="⚡ MettleX AI (Groq) กำลังประมวลผล...")
    
    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # ตั้งค่า Prompt และใช้โมเดล Llama 3.3 70B ตัวท็อปของ Groq
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
        
        # ยิง API ไปที่ Endpoint
