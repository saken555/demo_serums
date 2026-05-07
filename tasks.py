import logging
import httpx
from config import broker, GREEN_API_ID, GREEN_API_TOKEN
from db import get_settings, get_chat_history, save_message, match_serums
from ai import get_embedding, smart_generate
from utils import md_to_whatsapp, set_typing

@broker.task
async def process_ai_message(chat_id: str, user_text: str):
    """Основной воркер для обработки сообщения и отправки ответа."""
    try:
        # 1. Загружаем настройки из БД
        settings = await get_settings()
        if not settings:
            logging.error("Settings not found in DB")
            return

        params = settings.get('params', {})
        
        # Включаем тайпинг перед началом работы
        await set_typing(chat_id, True)

        # 2. Получаем историю чата
        history = await get_chat_history(chat_id, params.get('history_max_msgs', 10))

        # 3. RAG: Векторизация и поиск товаров
        embedding_model = params.get('embedding_model', 'models/text-embedding-004')
        
        search_query = await condense_query(user_text, history)
        user_vector = await get_embedding(search_query, embedding_model)

        products = await match_serums(
            user_vector, 
            params.get('rag_threshold', 0.7), 
            params.get('rag_top_k', 3)
        )

        # 4. Формируем контекст для ИИ
        context_str = "Найденные товары:\n"
        if products:
            for p in products:
                context_str += f"- {p['name']}: {p['descr']} (Цена: {p['price']})\n"
        else:
            context_str = "Товары по запросу не найдены."

        # 5. Сборка промпта и генерация
        full_prompt = (
            f"{settings['ai_prompt']}\n\n"
            f"КОНТЕКСТ ИЗ БАЗЫ ДАННЫХ:\n{context_str}\n\n"
            f"ВОПРОС ПОЛЬЗОВАТЕЛЯ: {user_text}"
        )

        ai_response = await smart_generate(
            full_prompt, 
            history, 
            settings['model1'], 
            settings['model2']
        )

        # Если обе модели упали
        if not ai_response:
            ai_response = "Извините, я сейчас на техническом обслуживании. Пожалуйста, напишите чуть позже."
        
        # 6. Форматирование под WhatsApp
        final_text = await md_to_whatsapp(ai_response)

        # 7. Сохранение в базу (вопрос и ответ)
        await save_message(chat_id, "user", user_text)
        await save_message(chat_id, "assistant", ai_response)

        # 8. Отправка через GreenAPI
        send_url = f"https://api.green-api.com/waInstance{GREEN_API_ID}/sendMessage/{GREEN_API_TOKEN}"
        payload = {"chatId": chat_id, "message": final_text}
        
        async with httpx.AsyncClient() as client:
            await client.post(send_url, json=payload, timeout=10.0)

    except Exception as e:
        logging.error(f"Worker Error: {e}")
    
    finally:
        # Выключаем тайпинг в любом случае
        await set_typing(chat_id, False)
