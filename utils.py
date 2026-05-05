import re
import httpx
import logging
from config import GREEN_API_ID, GREEN_API_TOKEN

async def md_to_whatsapp(text: str) -> str:
    """Конвертирует Markdown в упрощенный формат WhatsApp."""
    # Заменяем жирный текст: **text** -> *text*
    text = re.sub(r'\*\*(.*?)\*\*', r'*\1*', text)
    # Заменяем курсив: __text__ или *text* -> _text_ (но аккуратно с * для жирного)
    # Для MVP достаточно просто заменить двойные звездочки на одинарные.
    
    # Убираем заголовки: ### Текст -> *Текст*
    text = re.sub(r'#+\s*(.*)', r'*\1*', text)
    
    # Заменяем списки: - или * в начале строки на пулю •
    text = re.sub(r'^\s*[-*]\s+', '• ', text, flags=re.MULTILINE)
    
    return text.strip()

async def set_typing(chat_id: str, is_typing: bool):
    """Управляет статусом 'печтает...' в WhatsApp через GreenAPI."""
    status = "typing" if is_typing else "stopTyping"
    url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/setTypingStatus/{GREEN_API_TOKEN}"
    payload = {"chatId": chat_id, "status": status}
    
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload, timeout=5.0)
        except Exception as e:
            logging.error(f"GreenAPI Typing Error: {e}")

def count_tokens_approx(text: str) -> int:
    """Примерный подсчет токенов (1 токен ≈ 4 символа для кириллицы)."""
    return len(text) // 4
