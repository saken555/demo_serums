import logging
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def get_settings():
    """Получает актуальные настройки и параметры ИИ."""
    try:
        response = supabase.table("settings").select("*").limit(1).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        logging.error(f"Error fetching settings: {e}")
        return None

async def get_chat_history(chat_id: str, limit: int):
    """Извлекает историю сообщений для контекста."""
    try:
        response = supabase.table("chat_history") \
            .select("role", "content") \
            .eq("chatId", chat_id) \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        # Возвращаем в хронологическом порядке
        return response.data[::-1]
    except Exception as e:
        logging.error(f"Error fetching history: {e}")
        return []

async def save_message(chat_id: str, role: str, content: str):
    """Сохраняет сообщение (пользователя или ИИ) в базу."""
    try:
        supabase.table("chat_history").insert({
            "chatId": chat_id,
            "role": role,
            "content": content
        }).execute()
    except Exception as e:
        logging.error(f"Error saving message: {e}")

async def match_serums(embedding: list, threshold: float, count: int):
    """Вызов RPC функции в Supabase для векторного поиска."""
    try:
        rpc_params = {
            "query_embedding": embedding,
            "match_threshold": threshold,
            "match_count": count
        }
        response = supabase.rpc("match_serums", rpc_params).execute()
        return response.data
    except Exception as e:
        logging.error(f"Error in RAG search: {e}")
        return []
