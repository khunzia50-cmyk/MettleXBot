import os
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 10000))

# 1. HTTP Server สำหรับ Health Check บน Render
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

# 2. ฟังก์ชันจัดการข้อความ
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    user_message = update.message.text
    chat_id = update.message.chat_id

    status_message = await context.bot.send_message(
        chat_id=chat_id, 
        text="⚡ MettleX AI (DeepSeek R1) กำลังประมวลผลเชิงลึก..."
    )

    try:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # ใช้โมเดล DeepSeek R1 Distill Llama 70B ตามที่เลือก
        payload = {
            "model": "deepseek-r1-distill-llama-70b",
            "messages": [
                {
                    "role": "system",
                    "content": "คุณคือผู้ช่วยมืออาชีพด้านการเขียนสคริปต์ตัดต่อวิดีโอ ช่วยออกแบบโครงสร้าง บทพูด และคำแนะนำในการตัดต่ออย่างสร้างสรรค์และมีเหตุมีผล"
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
            timeout=45
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
        print("❌ Error: Missing tokens")
        return

    # รัน HTTP Server ใน Background
    server_thread = threading.Thread(target=run_http_server, daemon=True)
    server_thread.start()
    print(f"🌐 HTTP Server started on port {PORT}")

    # สร้าง Bot Application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🚀 Telegram Bot with DeepSeek R1 is running!")
    
    # เริ่มรัน Polling พร้อมเคลียร์เควสต์ค้าง
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
