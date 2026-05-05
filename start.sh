#!/bin/bash

# Запускаем ОДИН воркер (флаг -w 1)
# --max-async-tasks 1 ограничивает параллелизм внутри воркера для экономии RAM
taskiq worker tasks:broker --tasks tasks -w 1 --max-async-tasks 1 &

# Запускаем FastAPI
uvicorn main:app --host 0.0.0.0 --port $PORT
