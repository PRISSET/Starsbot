# 🚀 Руководство по развертыванию Telegram бота

Это руководство поможет вам развернуть и настроить Telegram бота для приема платежей звездами.

## 📋 Содержание

- [Требования](#требования)
- [Быстрый старт](#быстрый-старт)
- [Подробная настройка](#подробная-настройка)
- [Настройка платежей](#настройка-платежей)
- [Развертывание на сервере](#развертывание-на-сервере)
- [Мониторинг и логи](#мониторинг-и-логи)
- [Резервное копирование](#резервное-копирование)
- [Устранение неполадок](#устранение-неполадок)

## 🔧 Требования

### Системные требования
- Python 3.8 или выше
- Windows 10/11, Linux, или macOS
- Минимум 512 МБ RAM
- 1 ГБ свободного места на диске

### Необходимые аккаунты и токены
1. **Telegram Bot Token** - получить у [@BotFather](https://t.me/BotFather)
2. **Telegram Stars** - настроить в боте для приема платежей
3. **Администраторские права** - ID администраторов бота

## ⚡ Быстрый старт

### Windows

1. **Скачайте проект** и распакуйте в папку
2. **Запустите автоматическую установку:**
   ```cmd
   setup.bat
   ```
3. **Настройте конфигурацию** в файле `.env`
4. **Запустите бота:**
   ```cmd
   run.bat
   ```

### Linux/macOS

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd telegram-bot-stars
   ```

2. **Создайте виртуальное окружение:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/macOS
   ```

3. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Настройте конфигурацию:**
   ```bash
   cp .env.example .env
   nano .env  # или любой другой редактор
   ```

5. **Запустите бота:**
   ```bash
   python bot.py
   ```

## 🔧 Подробная настройка

### 1. Создание Telegram бота

1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Сохраните полученный **Bot Token**

### 2. Настройка файла .env

Создайте файл `.env` в корневой папке проекта:

```env
# Основные настройки бота
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789,987654321
DATABASE_URL=bot.db

# Настройки логирования
LOG_LEVEL=INFO
LOG_FILE=bot.log

# Настройки платежей
PAYMENT_PROVIDER_TOKEN=your_payment_token
CURRENCY=XTR

# Дополнительные настройки
WEBHOOK_URL=
WEBHOOK_PORT=8080
DEBUG=False
```

### 3. Настройка товаров

Отредактируйте файл `config.py` для настройки товаров:

```python
PRODUCTS = {
    "premium_1_month": {
        "title": "Премиум на 1 месяц",
        "description": "Доступ к премиум функциям на 1 месяц",
        "price": 100,  # цена в звездах
        "duration_days": 30
    },
    "premium_3_months": {
        "title": "Премиум на 3 месяца",
        "description": "Доступ к премиум функциям на 3 месяца",
        "price": 250,
        "duration_days": 90
    }
}
```

## 💳 Настройка платежей

### Включение Telegram Stars

1. **Откройте [@BotFather](https://t.me/BotFather)**
2. **Выберите вашего бота** из списка
3. **Перейдите в Bot Settings → Payments**
4. **Выберите Telegram Stars** как провайдера платежей
5. **Подтвердите настройки**

### Тестирование платежей

1. **Запустите бота** в тестовом режиме
2. **Используйте тестовые звезды** для проверки
3. **Проверьте логи** на наличие ошибок
4. **Убедитесь в корректной работе** базы данных

## 🖥️ Развертывание на сервере

### VPS/Dedicated Server

#### 1. Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и зависимостей
sudo apt install python3 python3-pip python3-venv git -y

# Создание пользователя для бота
sudo useradd -m -s /bin/bash botuser
sudo su - botuser
```

#### 2. Установка проекта

```bash
# Клонирование репозитория
git clone <repository-url> telegram-bot
cd telegram-bot

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка конфигурации
cp .env.example .env
nano .env
```

#### 3. Создание systemd сервиса

Создайте файл `/etc/systemd/system/telegram-bot.service`:

```ini
[Unit]
Description=Telegram Bot with Stars Payment
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/home/botuser/telegram-bot
Environment=PATH=/home/botuser/telegram-bot/venv/bin
ExecStart=/home/botuser/telegram-bot/venv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 4. Запуск сервиса

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Включение автозапуска
sudo systemctl enable telegram-bot

# Запуск сервиса
sudo systemctl start telegram-bot

# Проверка статуса
sudo systemctl status telegram-bot
```

### Docker развертывание

#### 1. Создание Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "bot.py"]
```

#### 2. Создание docker-compose.yml

```yaml
version: '3.8'

services:
  telegram-bot:
    build: .
    container_name: telegram-bot-stars
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - ADMIN_IDS=${ADMIN_IDS}
      - DATABASE_URL=/app/data/bot.db
    env_file:
      - .env
```

#### 3. Запуск через Docker

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## 📊 Мониторинг и логи

### Настройка логирования

Бот автоматически создает логи в файле `bot.log`. Для настройки уровня логирования измените `LOG_LEVEL` в `.env`:

- `DEBUG` - подробная отладочная информация
- `INFO` - общая информация о работе
- `WARNING` - предупреждения
- `ERROR` - только ошибки

### Мониторинг через systemd

```bash
# Просмотр логов сервиса
sudo journalctl -u telegram-bot -f

# Просмотр статуса
sudo systemctl status telegram-bot

# Перезапуск при необходимости
sudo systemctl restart telegram-bot
```

### Мониторинг базы данных

```bash
# Проверка размера базы данных
ls -lh bot.db

# Резервная копия
cp bot.db bot_backup_$(date +%Y%m%d_%H%M%S).db
```

## 💾 Резервное копирование

### Автоматическое резервное копирование

Создайте скрипт `backup.sh`:

```bash
#!/bin/bash

# Настройки
BOT_DIR="/home/botuser/telegram-bot"
BACKUP_DIR="/home/botuser/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание папки для бэкапов
mkdir -p $BACKUP_DIR

# Резервная копия базы данных
cp $BOT_DIR/bot.db $BACKUP_DIR/bot_$DATE.db

# Резервная копия конфигурации
cp $BOT_DIR/.env $BACKUP_DIR/env_$DATE.backup

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Настройка cron для автоматических бэкапов

```bash
# Редактирование crontab
crontab -e

# Добавление задачи (ежедневно в 2:00)
0 2 * * * /home/botuser/backup.sh >> /home/botuser/backup.log 2>&1
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 1. Бот не отвечает

**Проверьте:**
- Правильность Bot Token в `.env`
- Интернет соединение
- Логи на наличие ошибок

**Решение:**
```bash
# Проверка статуса
sudo systemctl status telegram-bot

# Просмотр логов
sudo journalctl -u telegram-bot -n 50

# Перезапуск
sudo systemctl restart telegram-bot
```

#### 2. Ошибки базы данных

**Проверьте:**
- Права доступа к файлу базы данных
- Целостность базы данных
- Свободное место на диске

**Решение:**
```bash
# Проверка целостности
sqlite3 bot.db "PRAGMA integrity_check;"

# Восстановление из бэкапа
cp bot_backup_YYYYMMDD_HHMMSS.db bot.db
```

#### 3. Проблемы с платежами

**Проверьте:**
- Настройки Telegram Stars в BotFather
- Правильность конфигурации товаров
- Логи платежных операций

**Решение:**
- Пересоздайте настройки платежей в BotFather
- Проверьте формат цен в `config.py`
- Убедитесь в корректности обработчиков платежей

### Диагностические команды

```bash
# Проверка процессов
ps aux | grep python

# Проверка портов
netstat -tlnp | grep :8080

# Проверка места на диске
df -h

# Проверка памяти
free -h

# Проверка логов
tail -f bot.log
```

### Контакты для поддержки

Если у вас возникли проблемы:

1. **Проверьте документацию** - README.md и API_DOCS.md
2. **Изучите логи** - файл bot.log содержит подробную информацию
3. **Запустите тесты** - `python test_bot.py`
4. **Проверьте примеры** - файл examples.py содержит примеры использования

## 📈 Оптимизация производительности

### Настройки базы данных

```python
# В database.py добавьте оптимизации
async def optimize_database(self):
    """Оптимизация базы данных"""
    async with aiosqlite.connect(self.db_path) as db:
        await db.execute("PRAGMA optimize")
        await db.execute("VACUUM")
        await db.commit()
```

### Мониторинг ресурсов

```bash
# Создание скрипта мониторинга
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
    echo "$(date): CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}'), RAM: $(free | grep Mem | awk '{printf "%.1f%%", $3/$2 * 100.0}')"
    sleep 60
done
EOF

chmod +x monitor.sh
./monitor.sh >> monitor.log &
```

## 🔄 Обновление бота

### Обновление кода

```bash
# Остановка бота
sudo systemctl stop telegram-bot

# Обновление кода
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt

# Применение миграций
python migrations.py migrate

# Запуск бота
sudo systemctl start telegram-bot
```

### Откат к предыдущей версии

```bash
# Остановка бота
sudo systemctl stop telegram-bot

# Откат к предыдущему коммиту
git reset --hard HEAD~1

# Откат миграций при необходимости
python migrations.py rollback 001

# Запуск бота
sudo systemctl start telegram-bot
```

Это руководство поможет вам успешно развернуть и поддерживать Telegram бота с приемом платежей звездами. Следуйте инструкциям пошагово и не забывайте делать резервные копии!