import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Токен бота (получить у @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Токен провайдера платежей (для звезд Telegram не требуется)
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN", "")

# Настройки базы данных (опционально)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot.db")

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Список администраторов бота
ADMIN_IDS_STR = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(id.strip()) for id in ADMIN_IDS_STR.split(",") if id.strip().isdigit()]

# Настройки приватного канала
CHANNEL_ID = os.getenv("CHANNEL_ID", "")  # ID приватного канала (например: -1001234567890)
CHANNEL_INVITE_LINK = os.getenv("CHANNEL_INVITE_LINK", "")  # Пригласительная ссылка на канал

# Цены подписок (в звездах Telegram)
SUBSCRIPTION_PRICES = {
    "1_month": 100,   # 1 месяц - 100 звезд
    "3_months": 250,  # 3 месяца - 250 звезд
    "6_months": 450,  # 6 месяцев - 450 звезд
    "12_months": 800  # 12 месяцев - 800 звезд
}

# Проверка обязательных настроек
if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    raise ValueError(
        "Необходимо установить BOT_TOKEN в файле .env или переменных окружения"
    )