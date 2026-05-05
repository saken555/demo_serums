FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для работы с сетью
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Даем права на выполнение скрипта запуска
RUN chmod +x start.sh

# Render прокидывает порт через переменную окружения PORT
EXPOSE 8000

# Запускаем через наш скрипт
CMD ["./start.sh"]
