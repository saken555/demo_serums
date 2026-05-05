import httpx
import logging
from config import GEMINI_API_KEY

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def format_model_name(name: str) -> str:
    """Гарантирует, что имя модели начинается с 'models/' без дублей."""
    name = name.strip()
    if name.startswith("models/"):
        return name
    return f"models/{name}"

async def get_embedding(text: str, model_name: str) -> list:
    """Генерация эмбеддинга для RAG-поиска."""
    # Используем отформатированное имя
    full_model_name = format_model_name(model_name)
    url = f"{BASE_URL}/{full_model_name}:embedContent?key={GEMINI_API_KEY}"
    
    payload = {
        "model": full_model_name,
        "content": {"parts": [{"text": text}]},
        "task_type": "retrieval_query"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=10.0)
        if response.status_code != 200:
            logging.error(f"Embedding Error: {response.status_code} - {response.text}")
            # Если 004 не доступна, попробуйте вернуть заглушку или упасть с описанием
            response.raise_for_status()
        return response.json()['embedding']['values']

async def generate_answer(prompt: str, history: list, model: str) -> str:
    """Одиночный запрос к Gemini."""
    full_model_name = format_model_name(model)
    url = f"{BASE_URL}/{full_model_name}:generateContent?key={GEMINI_API_KEY}"
    
    contents = []
    for msg in history:
        role = "user" if msg['role'] == 'user' else "model"
        contents.append({"role": role, "parts": [{"text": msg['content']}]})
    
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    
    payload = {
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": 1000,
            "temperature": 0.7
        }
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=30.0)
        if response.status_code != 200:
            logging.error(f"Gemini Error {full_model_name}: {response.text}")
            return None
        
        data = response.json()
        try:
            return data['candidates'][0]['content']['parts'][0]['text']
        except (KeyError, IndexError):
            return None
