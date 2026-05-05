import httpx
import logging
from config import GEMINI_API_KEY

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

async def get_embedding(text: str, model_name: str) -> list:
    """Генерация эмбеддинга для RAG-поиска."""
    url = f"{BASE_URL}/{model_name}:embedContent?key={GEMINI_API_KEY}"
    payload = {
        "model": model_name,
        "content": {"parts": [{"text": text}]},
        "task_type": "retrieval_query"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()['embedding']['values']

async def generate_answer(prompt: str, history: list, model: str) -> str:
    """Одиночный запрос к Gemini."""
    url = f"{BASE_URL}/models/{model}:generateContent?key={GEMINI_API_KEY}"
    
    # Формируем структуру сообщений
    contents = []
    for msg in history:
        role = "user" if msg['role'] == 'user' else "model"
        contents.append({"role": role, "parts": [{"text": msg['content']}]})
    
    # Добавляем текущий промпт (инструкция + контекст + вопрос) в конец
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 1000, # Можно брать из БД
            "temperature": 0.7
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=30.0)
        if response.status_code != 200:
            logging.error(f"Gemini Error {model}: {response.text}")
            return None
        
        data = response.json()
        try:
            return data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, Index_Error):
            return None

async def smart_generate(full_prompt: str, history: list, m1: str, m2: str) -> str:
    """Логика Fallback: сначала m1, если ошибка — m2."""
    # Попытка 1
    result = await generate_answer(full_prompt, history, m1)
    if result:
        return result
    
    # Попытка 2 (Fallback)
    logging.warning(f"Switching to fallback model: {m2}")
    result = await generate_answer(full_prompt, history, m2)
    return result
