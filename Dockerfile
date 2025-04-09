FROM python:3.13-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем необходимые библиотеки
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения в контейнер
COPY . .

# Указываем команду для запуска приложения. Используем `env` для подстановки переменных окружения (опционально, но полезно для дебага)
CMD ["python", "AITelegramBot.py"]
