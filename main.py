import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from groq import Groq

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render จะใส่ URL ให้อัตโนมัติ
PORT = int(os.getenv("PORT", 10000))

groq_client = Groq(api_key=GROQ_API_KEY)

# สร้าง Flask แอปสำหรับรับ Webhook และ Health Check ของ Render
app_flask = Flask(__name__)

# สร้าง Telegram Application (แบบไม่ใช้ run_polling)
telegram_app = Application.builder().token(BOT_TOKEN).build()

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
        chat_completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "คุณคือผู้ช่วยมืออาชีพด้านการเขียนสคริปต์ตัดต่อวิดีโอ ช่วยออกแบบโครงสร้าง บทพูด และคำแนะนำในการตัดต่ออย่างสร้างสรรค์"
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0.7
        )

        reply_text = chat_completion.choices[0].message.content

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

telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

@app_flask.route("/", methods=["GET"])
def health_check():
    return "Bot is active and running!", 200

@app_flask.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    # รับข้อมูลอัปเดตจาก Telegram ส่งเข้ามาตรงๆ
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    telegram_app.update_queue.put_nowait(update)
    return "ok", 200

async def setup_webhook():
    await telegram_app.initialize()
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL}/{BOT_TOKEN}"
        await telegram_app.bot.set_webhook(url=webhook_url)
        print(f"🔗 Webhook set to: {webhook_url}")

if __name__ == "__main__":
    import asyncio
    # ตั้งค่า Webhook อัตโนมัติก่อนรันเซิร์ฟเวอร์
    asyncio.run(setup_webhook())
    
    # รัน Flask บนพอร์ต 10000 เพื่อรองรับ Render Web Service
    app_flask.run(host="0.0.0.0", port=PORT)
