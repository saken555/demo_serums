from fastapi import FastAPI, Request, BackgroundTasks
from config import broker
from tasks import process_ai_message
import uvicorn

app = FastAPI()

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Прием уведомлений от GreenAPI."""
    data = await request.json()
    
    # Проверяем, что это входящее текстовое сообщение
    # Структура GreenAPI: typeWebhook == "incomingMessageReceived"
    if data.get("typeWebhook") == "incomingMessageReceived":
        msg_data = data.get("messageData", {})
        
        if msg_data.get("typeMessage") == "textMessage":
            chat_id = data["senderData"]["chatId"]
            text = msg_data["textMessageData"]["textMessage"]
            
            # Отправляем задачу в воркер TaskIQ
            await process_ai_message.kiq(chat_id, text)
            
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
