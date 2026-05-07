import httpx
import logging
from config import GEMINI_API_KEY

# ВНИМАНИЕ: Для модели gemini-embedding-2 обязательна версия v1beta
BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

def format_model_name(name: str) -> str:
    """Гарантирует, что имя модели начинается с 'models/' без дублей."""
    name = name.strip()
    if name.startswith("models/"):
        return name
    return f"models/{name}"

async def condense_query(user_text: str, history: list, model: str ) -> str:
    """Превращает уточняющий вопрос в полноценный поисковый запрос на основе истории."""
    if not history:
        return user_text
        
    history_str = ""
    for msg in history[-3:]: # Берем только последние 3 сообщения для экономии
        role = "Юзер" if msg['role'] == 'user' else "Бот"
        history_str += f"{role}: {msg['content']}\n"
        
    prompt = (
        f"Дан диалог между пользователем и ИИ-консультантом по косметике.\n"
        f"История:\n{history_str}\n"
        f"Новый вопрос: {user_text}\n\n"
        f"Твоя задача: переформулируй новый вопрос в короткий поисковый запрос (2-5 слов), "
        f"который можно использовать для поиска в базе данных. "
        f"Если вопрос понятен без контекста, верни его без изменений. "
        f"Ответь ТОЛЬКО текстом запроса."
    )
    
    # Используем generate_answer или прямой запрос к Flash
    condensed = await generate_answer(prompt, [], model)
    
    return condensed if condensed else user_text


async def get_embedding(text: str, model_name: str) -> list:
    """Генерация эмбеддинга с обрезкой до 768 (Matryoshka)."""
    full_model_name = format_model_name(model_name)
    url = f"{BASE_URL}/{full_model_name}:embedContent?key={GEMINI_API_KEY}"
    
    # Для поискового запроса используем более точный префикс
    query_text = f"task: search query | query: {text}"
    
    payload = {
        "model": full_model_name,
        "content": {"parts": [{"text": query_text}]},
        # КРИТИЧЕСКИЙ ПАРАМЕТР: заставляем API вернуть 768 измерений
        "output_dimensionality": 768 
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, timeout=10.0)
        if response.status_code != 200:
            logging.error(f"Embedding Error: {response.status_code} - {response.text}")
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
