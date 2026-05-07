import os
import logging
from fastapi import FastAPI, Request, HTTPException, Query
from redis import Redis
from tasks import process_ai_message

# Инициализация приложения
app = FastAPI()

# Подключение к Redis для контроля лимитов (Rate Limiting)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = Redis.from_url(redis_url)

# Конфигурация безопасности
WEBHOOK_TOKEN = os.getenv("WEBHOOK_TOKEN", "my_secret_token_123")
MAX_CHARS = 1000  # Максимальная длина сообщения
RATE_LIMIT_SECONDS = 3  # Пауза между сообщениями от одного пользователя

@app.get("/")
async def health_check():
    """Проверка того, что сервер 'дышит'."""
    return {"status": "online", "message": "Serums AI Bot is running"}

@app.post("/webhook")
async def handle_webhook(
    request: Request, 
    token: str = Query(None)
):
    """
    Основной эндпоинт для GreenAPI.
    URL для GreenAPI должен быть: https://your-url.onrender.com/webhook?token=your_token
    """
    
    # 1. Проверка безопасности (Secret Token)
    if token != WEBHOOK_TOKEN:
        logging.warning("Unauthorized access attempt with wrong token")
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        data = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}

    # 2. Фильтрация входящих уведомлений
    # Нас интересуют только входящие текстовые сообщения (incomingMessageReceived)
    type_webhook = data.get("typeWebhook")
    if type_webhook != "incomingMessageReceived":
        return {"status": "ignored", "type": type_webhook}

    chat_id = data.get("senderData", {}).get("chatId")
    message_data = data.get("messageData", {})
    
    # Извлекаем текст (поддерживаем обычный текст и расширенный формат)
    text = ""
    if message_data.get("typeMessage") == "textMessage":
        text = message_data.get("textMessageData", {}).get("textMessage", "")
    elif message_data.get("typeMessage") == "extendedTextMessage":
        text = message_data.get("extendedTextMessageData", {}).get("text", "")

    if not chat_id or not text:
        return {"status": "error", "message": "Missing chat_id or text"}

    # 3. Защита: Проверка длины сообщения
    if len(text) > MAX_CHARS:
        logging.info(f"Message from {chat_id} ignored: too long ({len(text)} chars)")
        return {"status": "ignored", "reason": "message_too_long"}

    # 4. Защита: Rate Limiting (один запрос в N секунд)
    lock_key = f"ratelimit:{chat_id}"
    if redis_client.get(lock_key):
        logging.info(f"Rate limit hit for {chat_id}")
        return {"status": "rate_limited", "message": "Please wait between messages"}
    
    # Устанавливаем блокировку на время обработки
    redis_client.setex(lock_key, RATE_LIMIT_SECONDS, "1")

    # 5. Отправка задачи в TaskIQ воркер
    # Мы не ждем ответа здесь, а сразу возвращаем 200 OK GreenAPI
    await process_ai_message.kiq(chat_id, text)

    return {"status": "accepted"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))