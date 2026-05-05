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
# Берем URL из переменных (для Upstash это rediss://...), если нет — локальный redis
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

# ВАЖНО: 
# 1. Для Backend библиотека просит аргумент redis_url
# 2. Для Broker библиотека просит аргумент url
result_backend = RedisAsyncResultBackend(redis_url=redis_url)
broker = ListQueueBroker(url=redis_url).with_result_backend(result_backend)
