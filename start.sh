#!/bin/bash

# Запускаем воркер TaskIQ в фоновом режиме
# Используем модуль tasks и объект broker внутри него
taskiq worker tasks:broker --tasks tasks &

# Запускаем основной сервер FastAPI
uvicorn main:app --host 0.0.0.0 --port $PORT
