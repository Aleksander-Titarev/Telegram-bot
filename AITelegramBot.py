import logging  # Импортируем модуль logging для записи информации о работе программы в лог
import re  # Импортируем модуль re для работы с регулярными выражениями
import os  # Импортируем модуль os для работы с переменными окружения
from telegram import Update  # Импортируем класс Update из библиотеки telegram для обработки входящих обновлений от Telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext  # Импортируем необходимые классы из telegram.ext для создания Telegram бота
from openai import OpenAI  # Импортируем класс OpenAI из библиотеки openai для взаимодействия с OpenAI API
import telegram  # Импортируем модуль telegram для работы с Telegram API
from dotenv import load_dotenv  # Импортируем функцию load_dotenv из библиотеки python-dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Конфигурация
BOT_TOKEN = os.environ.get("BOT_TOKEN")  # Токен Telegram бота, полученный от BotFather. Получаем из переменной окружения
API_KEY = os.environ.get("API_KEY")  # API ключ для доступа к OpenAI API. Получаем из переменной окружения

# Проверка токенов
if not BOT_TOKEN:  # Проверяем, установлен ли BOT_TOKEN
    print("Error: BOT_TOKEN не установлен.")  # Выводим сообщение об ошибке в консоль
    exit(1)  # Завершаем программу с кодом ошибки 1

if not API_KEY:  # Проверяем, установлен ли API_KEY
    print("Error: API_KEY не установлен.")  # Выводим сообщение об ошибке в консоль
    exit(1)  # Завершаем программу с кодом ошибки 1

# Инициализация клиентов
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=API_KEY)  # Создаем экземпляр класса OpenAI для взаимодействия с API OpenRouter.ai (позволяет использовать разные модели OpenAI)
conversation_history = {}  # Создаем словарь для хранения истории переписки с каждым пользователем. Ключ - user_id, значение - список сообщений

async def start(update: Update, context: CallbackContext):
    """
    Обработчик команды /start. Отправляет приветственное сообщение пользователю.
    """
    user_id = update.message.from_user.id  # Получаем ID пользователя, отправившего сообщение
    if user_id not in conversation_history:  # Проверяем, есть ли история переписки с этим пользователем
        conversation_history[user_id] = []  # Если нет, создаем пустой список для хранения истории

    await update.message.reply_text(  # Отправляем приветственное сообщение пользователю
        "Привет, товарищ\! Нет желания думать самому\? Задавай свой вопрос\.\n"  # Текст сообщения
        "Используйте /help для получения справки\.",  # Дополнительный текст сообщения
        parse_mode=telegram.constants.ParseMode.MARKDOWN_V2  # Указываем, что текст отформатирован в стиле MarkdownV2
    )

async def help_command(update: Update, context: CallbackContext):
    """
    Обработчик команды /help. Отправляет справочное сообщение пользователю со списком команд.
    """
    help_text = (  # Текст справочного сообщения
        "*Список команд:*\n"
        "/start \- Начать диалог\n"
        "/help \- Помощь и контакт \(\@SenatorGennady\)\n"
        "/reset \- Сбросить историю\n"
    )
    await update.message.reply_text(help_text, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)  # Отправляем справочное сообщение, отформатированное в стиле MarkdownV2

async def handle_message(update: Update, context: CallbackContext):
    """
    Обработчик всех текстовых сообщений, не являющихся командами.
    Отправляет сообщение пользователя в OpenAI API и возвращает ответ.
    """
    user_id = update.message.from_user.id  # Получаем ID пользователя, отправившего сообщение
    user_message = update.message.text  # Получаем текст сообщения пользователя
    logging.info(f"Сообщение от {user_id}: {user_message}")  # Записываем информацию о сообщении в лог

    if user_id not in conversation_history:  # Проверяем, есть ли история переписки с этим пользователем
        conversation_history[user_id] = []  # Если нет, создаем пустой список

    conversation_history[user_id].append({"role": "user", "content": user_message})  # Добавляем сообщение пользователя в историю переписки

    try:
        completion = client.chat.completions.create(  # Отправляем запрос в OpenAI API
            model="deepseek/deepseek-chat-v3-0324:free",  # Указываем используемую модель
            messages=conversation_history[user_id],  # Отправляем историю переписки в качестве контекста
            timeout=30 # Задаем таймаут для запроса в секундах
        )

        if completion.choices and completion.choices[0].message.content:  # Проверяем, получен ли ответ от API и содержит ли он контент
            content = completion.choices[0].message.content.strip()  # Получаем контент ответа и удаляем пробелы в начале и конце

            # Экранирование символов для MarkdownV2
            def escape_markdown_v2(text):
                """Экранирует специальные символы в тексте для корректного отображения в MarkdownV2."""
                escape_chars = r"_*[]()~`>#+-=|{}.!"  # Символы, которые нужно экранировать
                return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)  # Заменяем каждый специальный символ на его экранированную версию

            escaped_content = escape_markdown_v2(content)  # Экранируем контент ответа
            cleaned_content = re.sub(r'<.*?>', '', escaped_content).strip() # Удаляем HTML-теги, если они есть и удаляем пробелы

            if cleaned_content:
                max_length = 4096  # Максимальная длина сообщения Telegram
                chunks = [cleaned_content[i:i+max_length] for i in range(0, len(cleaned_content), max_length)]  # Разбиваем сообщение на части, если оно слишком длинное

                for i, chunk in enumerate(chunks):  # Отправляем каждую часть сообщения пользователю
                    response = f"*Ответ:*\n{chunk}" if i == 0 else chunk  # Форматируем первую часть сообщения, добавляя заголовок "Ответ:"
                    try:
                        await update.message.reply_text(response, parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)  # Отправляем часть сообщения, отформатированную в стиле MarkdownV2
                    except telegram.error.BadRequest as e:
                         logging.error(f"BadRequest error: {e}")
                         await update.message.reply_text(f"Ответ:\n{chunk}", parse_mode=None)  # fallback - отправляем без форматирования в случае ошибки

                conversation_history[user_id].append({"role": "assistant", "content": content})  # Добавляем ответ ассистента в историю переписки (оригинальный контент)
            else:
                await update.message.reply_text("*Пустой ответ*", parse_mode=telegram.constants.ParseMode.MARKDOWN_V2) # Обрабатываем случай, когда OpenAI API вернул пустой ответ
        else:
            await update.message.reply_text("*Ошибка обработки: нет ответа от API*", parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)  # Сообщаем пользователю об ошибке, если API не вернул ответ

    except Exception as e:  # Обрабатываем возможные исключения
        logging.error(f"Ошибка: {str(e)}")  # Записываем информацию об ошибке в лог
        await update.message.reply_text(f"*Ошибка:* {str(e)}", parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)  # Отправляем сообщение об ошибке пользователю

async def reset_command(update: Update, context: CallbackContext):
    """
    Обработчик команды /reset. Сбрасывает историю переписки с пользователем.
    """
    user_id = update.message.from_user.id  # Получаем ID пользователя, отправившего сообщение
    if user_id in conversation_history:  # Проверяем, есть ли история переписки с этим пользователем
        del conversation_history[user_id]  # Если есть, удаляем ее
        await update.message.reply_text("История сброшена\.", parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)  # Отправляем сообщение об успешном сбросе истории
    else:
        await update.message.reply_text("Истории нет\.", parse_mode=telegram.constants.ParseMode.MARKDOWN_V2)  # Отправляем сообщение о том, что истории нет

async def error_handler(update: Update, context: CallbackContext):
    """
    Обработчик ошибок. Записывает информацию об ошибке в лог и отправляет сообщение пользователю.
    """
    logging.error(f"Ошибка: {context.error}")  # Записываем информацию об ошибке в лог
    if update:
        await update.message.reply_text("⚠️ Ошибка обработки. Попробуйте позже.")  # Отправляем сообщение об ошибке пользователю

def main():
    """
    Основная функция, запускающая Telegram бота.
    """
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)  # Настраиваем логирование

    app = Application.builder().token(BOT_TOKEN).build()  # Создаем экземпляр класса Application

    app.add_handler(CommandHandler("start", start))  # Регистрируем обработчик команды /start
    app.add_handler(CommandHandler("help", help_command))  # Регистрируем обработчик команды /help
    app.add_handler(CommandHandler("reset", reset_command))  # Регистрируем обработчик команды /reset
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Регистрируем обработчик текстовых сообщений
    app.add_error_handler(error_handler)  # Регистрируем обработчик ошибок

    app.run_polling()  # Запускаем бота в режиме polling

if __name__ == '__main__':
    main()  # Запускаем основную функцию, если скрипт запущен напрямую