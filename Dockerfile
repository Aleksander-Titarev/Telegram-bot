FROM python:3.9-slim-buster

WORKDIR /app

ENV BOT_TOKEN=7697618555:AAGB4ZEbgO3c80MdFIyLQzCcDxqZw6gsgx4
ENV API_KEY=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

# Копирование файлов проекта
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Запуск вашего приложения
CMD ["python", "AITelegramBot.py"]

