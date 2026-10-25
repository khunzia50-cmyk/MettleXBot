import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ดึงค่า Environment Variables
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 10000))

# 1. ระบบ HTTP Server จิ๋วสำหรับรักษาสถานะบน Render (Health Check)
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

# 2. ฟังก์ชันหลักสำหรับรับข้อความจาก Telegram และส่งไปยัง Groq API
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    chat_id = update.message.chat_id

    # ส่งข้อความแจ้งสถานะกำลังประมวลผล
    status_message = await context.bot.send_message(
        chat_id=chat_id, 
        text="⚡ MettleX AI (Groq) กำลังประมวลผล..."
    )

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # ใช้โมเดลมาตรฐานที่รองรับการใช้งานทั่วไปอย่างเสถียร
        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": "คุณคือผู้ช่วยมืออาชีพด้านการเขียนสคริปต์ตัดต่อวิดีโอ ช่วยออกแบบโครงสร้าง บทพูด และคำแนะนำในการตัดต่ออย่างสร้างสรรค์"
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

        # แก้ไขข้อความเดิมเป็นผลลัพธ์จาก AI
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message.message_id,
            text=reply_text
        )

    except Exception as e:
        await context.bot.edit_message_text(
            chat_id=chat_id,
            message_id=status_message.message_id,
            text=f"❌ เกิดข้อผิดพลาดในระบบ: {str(e)}"
        )

# 3. ฟังก์ชันเริ่มต้นรันบอท
def main():
    if not BOT_TOKEN or not GROQ_API_KEY:
        print("❌ Error: กรุณาตั้งค่า TELEGRAM_BOT_TOKEN และ GROQ_API_KEY ใน Environment Variables ให้เรียบร้อย")
        return

    # เริ่มต้นรัน HTTP Server ใน Background Thread เพื่อจองพอร์ตบน Render
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()
    print(f"🌐 HTTP Server started on port {PORT}")

    # สร้างแอปพลิเคชัน Telegram Bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ลงทะเบียนฟังก์ชันรับข้อความทั่วไป
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🚀 Telegram Bot with Groq is running!")
    
    # เริ่มรันระบบ Polling เพื่อรอรับข้อความ
    app.run_polling()

if __name__ == "__main__":
    main()
