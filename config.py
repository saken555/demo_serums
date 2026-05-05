import os
from dotenv import load_dotenv
from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker

load_dotenv()

# Настройки GreenAPI
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")

# Настройки Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") 

# Инициализация TaskIQ (Redis)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
result_backend = RedisAsyncResultBackend(redis_url=redis_url)
# Для брокера используем url=, для backend оставляем redis_url= (так требует библиотека)
broker = ListQueueBroker(url=redis_url).with_result_backend(result_backend)

redis_url = os.getenv("REDIS_URL")

# Для Upstash обязательно проверяем наличие SSL в URL
result_backend = RedisAsyncResultBackend(url=redis_url)
broker = ListQueueBroker(redis_url=redis_url).with_result_backend(result_backend)

