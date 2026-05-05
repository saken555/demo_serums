import os
from dotenv import load_dotenv
from taskiq_redis import RedisAsyncResultBackend, ListQueueBroker

load_dotenv()

# Настройки GreenAPI
GREEN_API_ID = os.getenv("GREEN_API_ID")
GREEN_API_TOKEN = os.getenv("GREEN_API_TOKEN")

# Настройки Supabase
SUPABASE_URL = "https://iahghirynznazxyuuqya.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlhaGdoaXJ5bnpuYXp4eXV1cXlhIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3Njk1NjAzNSwiZXhwIjoyMDkyNTMyMDM1fQ.d2KEGCvtZ4S1wGA6qN9lVPVsz94QnN40h4teoynfNyk"
GEMINI_API_KEY = "AIzaSyDgc3OrC0tJV0BEMEDwe2WwKgbyQpENXkw" 

# Инициализация TaskIQ (Redis)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
result_backend = RedisAsyncResultBackend(redis_url=redis_url)
broker = ListQueueBroker(redis_url=redis_url).with_result_backend(result_backend)

