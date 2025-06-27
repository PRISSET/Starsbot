# API Документация - Telegram Bot для платежей звездами

## Обзор

Этот документ описывает API и архитектуру Telegram бота для обработки платежей звездами Telegram.

## Структура проекта

```
Telegrambot Stars/
├── bot.py              # Основной файл бота
├── config.py           # Конфигурация и настройки
├── database.py         # Работа с базой данных
├── admin.py            # Административные функции
├── examples.py         # Примеры использования
├── test_bot.py         # Тесты
├── requirements.txt    # Зависимости Python
├── .env               # Переменные окружения
├── setup.bat          # Скрипт установки
├── run.bat            # Скрипт запуска
├── README.md          # Основная документация
└── API_DOCS.md        # Этот файл
```

## Модули

### 1. bot.py - Основной модуль бота

#### Основные функции:

##### `start_command(message: types.Message)`
- **Описание**: Обработчик команды `/start`
- **Параметры**: `message` - объект сообщения Telegram
- **Возвращает**: None
- **Действия**: 
  - Создает или обновляет пользователя в БД
  - Отправляет приветственное сообщение
  - Показывает главное меню

##### `show_products(callback: types.CallbackQuery)`
- **Описание**: Показывает список доступных товаров
- **Параметры**: `callback` - объект callback query
- **Возвращает**: None

##### `buy_product(callback: types.CallbackQuery)`
- **Описание**: Инициирует процесс покупки товара
- **Параметры**: `callback` - содержит ID товара
- **Возвращает**: None
- **Действия**: Создает инвойс для оплаты звездами

##### `process_successful_payment(message: types.Message)`
- **Описание**: Обрабатывает успешные платежи
- **Параметры**: `message` - сообщение с данными платежа
- **Возвращает**: None
- **Действия**:
  - Сохраняет покупку в БД
  - Активирует премиум (если применимо)
  - Отправляет подтверждение

##### `show_profile(callback: types.CallbackQuery)`
- **Описание**: Показывает профиль пользователя
- **Параметры**: `callback` - объект callback query
- **Возвращает**: None
- **Отображает**:
  - Статус премиума
  - Дату регистрации
  - Кнопку истории покупок

##### `show_purchase_history(callback: types.CallbackQuery)`
- **Описание**: Показывает историю покупок пользователя
- **Параметры**: `callback` - объект callback query
- **Возвращает**: None

### 2. database.py - Модуль базы данных

#### Модели данных:

##### `User`
```python
class User:
    telegram_id: int          # ID пользователя в Telegram
    username: str             # Username пользователя
    first_name: str           # Имя пользователя
    last_name: str            # Фамилия пользователя
    registration_date: datetime # Дата регистрации
    premium_until: datetime   # Дата окончания премиума
    is_premium_active: bool   # Активен ли премиум
```

##### `Purchase`
```python
class Purchase:
    id: int                           # ID покупки
    user_id: int                      # ID пользователя
    product_id: str                   # ID товара
    product_title: str                # Название товара
    amount: int                       # Сумма в звездах
    purchase_date: datetime           # Дата покупки
    telegram_payment_charge_id: str   # ID платежа Telegram
```

#### Основные методы Database:

##### `create_or_update_user(telegram_id, username, first_name, last_name=None)`
- **Описание**: Создает нового пользователя или обновляет существующего
- **Параметры**:
  - `telegram_id` (int): ID пользователя в Telegram
  - `username` (str): Username пользователя
  - `first_name` (str): Имя пользователя
  - `last_name` (str, optional): Фамилия пользователя
- **Возвращает**: `User` объект

##### `get_user(telegram_id)`
- **Описание**: Получает пользователя по Telegram ID
- **Параметры**: `telegram_id` (int)
- **Возвращает**: `User` объект или `None`

##### `activate_premium(telegram_id, days)`
- **Описание**: Активирует премиум статус для пользователя
- **Параметры**:
  - `telegram_id` (int): ID пользователя
  - `days` (int): Количество дней премиума
- **Возвращает**: None

##### `create_purchase(user_id, product_id, product_title, amount, telegram_payment_charge_id)`
- **Описание**: Создает запись о покупке
- **Параметры**:
  - `user_id` (int): ID пользователя
  - `product_id` (str): ID товара
  - `product_title` (str): Название товара
  - `amount` (int): Сумма в звездах
  - `telegram_payment_charge_id` (str): ID платежа
- **Возвращает**: `Purchase` объект

##### `get_user_purchases(telegram_id, limit=10)`
- **Описание**: Получает покупки пользователя
- **Параметры**:
  - `telegram_id` (int): ID пользователя
  - `limit` (int): Максимальное количество записей
- **Возвращает**: Список `Purchase` объектов

#### Административные методы:

##### `get_total_users_count()`
- **Возвращает**: Общее количество пользователей

##### `get_premium_users_count()`
- **Возвращает**: Количество премиум пользователей

##### `get_total_purchases_count()`
- **Возвращает**: Общее количество покупок

##### `get_total_revenue()`
- **Возвращает**: Общий доход в звездах

##### `get_recent_users(limit=10)`
- **Возвращает**: Список последних зарегистрированных пользователей

##### `get_recent_purchases(limit=10)`
- **Возвращает**: Список последних покупок

### 3. admin.py - Административный модуль

#### Основные функции:

##### `is_admin(user_id)`
- **Описание**: Проверяет, является ли пользователь администратором
- **Параметры**: `user_id` (int)
- **Возвращает**: `bool`

##### `admin_menu(callback: types.CallbackQuery)`
- **Описание**: Показывает главное меню администратора
- **Доступ**: Только для администраторов

##### `admin_stats(callback: types.CallbackQuery)`
- **Описание**: Показывает статистику бота
- **Отображает**:
  - Общее количество пользователей
  - Количество премиум пользователей
  - Общее количество покупок
  - Общий доход

##### `admin_users(callback: types.CallbackQuery)`
- **Описание**: Показывает информацию о пользователях
- **Отображает**: Список последних зарегистрированных пользователей

##### `admin_payments(callback: types.CallbackQuery)`
- **Описание**: Показывает информацию о платежах
- **Отображает**: Список последних покупок

##### `broadcast_message(callback: types.CallbackQuery)`
- **Описание**: Инициирует процесс рассылки сообщений
- **Функционал**: Отправка сообщения всем пользователям

##### `export_users(callback: types.CallbackQuery)`
- **Описание**: Экспортирует данные пользователей
- **Формат**: CSV файл с информацией о пользователях

### 4. config.py - Конфигурация

#### Переменные окружения:

- `BOT_TOKEN`: Токен Telegram бота
- `ADMIN_IDS`: Список ID администраторов (через запятую)

#### Конфигурация товаров:

```python
PRODUCTS = {
    "premium_access": {
        "title": "Премиум доступ",
        "description": "Получите премиум статус на 30 дней",
        "price": 100,  # в звездах
        "premium_days": 30
    },
    "extra_features": {
        "title": "Дополнительные функции",
        "description": "Разблокируйте дополнительные возможности",
        "price": 50,
        "premium_days": 7
    }
}
```

## Callback Data Format

Бот использует следующие форматы callback data:

- `products` - Показать товары
- `buy_{product_id}` - Купить товар
- `profile` - Показать профиль
- `purchase_history` - История покупок
- `main_menu` - Главное меню
- `admin_menu` - Меню администратора
- `admin_stats` - Статистика
- `admin_users` - Пользователи
- `admin_payments` - Платежи
- `admin_settings` - Настройки
- `broadcast` - Рассылка
- `export_users` - Экспорт пользователей

## Обработка платежей

### Процесс оплаты:

1. Пользователь выбирает товар
2. Бот создает инвойс с помощью `bot.send_invoice()`
3. Пользователь оплачивает через Telegram Stars
4. Telegram отправляет `successful_payment` событие
5. Бот обрабатывает платеж в `process_successful_payment()`
6. Создается запись в БД и активируется премиум

### Параметры инвойса:

```python
await bot.send_invoice(
    chat_id=user_id,
    title=product['title'],
    description=product['description'],
    payload=product_id,  # Используется для идентификации товара
    provider_token="",   # Пустой для Telegram Stars
    currency="XTR",      # Валюта Telegram Stars
    prices=[LabeledPrice(label=product['title'], amount=product['price'])]
)
```

## База данных

### Схема таблиц:

#### Таблица `users`:
```sql
CREATE TABLE users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    premium_until TIMESTAMP
);
```

#### Таблица `purchases`:
```sql
CREATE TABLE purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    product_title TEXT NOT NULL,
    amount INTEGER NOT NULL,
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    telegram_payment_charge_id TEXT UNIQUE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (telegram_id)
);
```

## Безопасность

### Проверки:

1. **Валидация платежей**: Проверка `telegram_payment_charge_id` на уникальность
2. **Права администратора**: Проверка ID пользователя в списке `ADMIN_IDS`
3. **Валидация товаров**: Проверка существования `product_id` в конфигурации
4. **Обработка ошибок**: Try-catch блоки для всех операций с БД

### Рекомендации:

1. Регулярно делайте резервные копии базы данных
2. Не храните токен бота в коде - используйте `.env` файл
3. Ограничьте доступ к административным функциям
4. Логируйте все важные операции

## Расширение функциональности

### Добавление нового товара:

1. Добавьте товар в `PRODUCTS` в `config.py`
2. При необходимости обновите логику в `buy_product()`
3. Добавьте обработку в `process_successful_payment()`

### Добавление новой административной функции:

1. Создайте функцию в `admin.py`
2. Добавьте кнопку в `admin_menu()`
3. Зарегистрируйте обработчик в `register_admin_handlers()`

### Добавление новых полей в БД:

1. Обновите модели в `database.py`
2. Создайте миграцию для существующих данных
3. Обновите соответствующие методы

## Мониторинг и логирование

### Логи:

Бот использует стандартный модуль `logging` Python:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

### Метрики для мониторинга:

- Количество активных пользователей
- Количество успешных платежей
- Общий доход
- Ошибки при обработке платежей
- Время отклика бота

## Тестирование

### Запуск тестов:

```bash
python test_bot.py
```

### Типы тестов:

1. **Unit тесты**: Тестирование отдельных функций
2. **Интеграционные тесты**: Тестирование взаимодействия с БД
3. **Тесты конфигурации**: Проверка настроек товаров
4. **Тесты обработки ошибок**: Проверка обработки исключений

### Примеры использования:

```bash
python examples.py
```

## Развертывание

### Локальное развертывание:

1. Запустите `setup.bat` для установки
2. Настройте `.env` файл
3. Запустите `run.bat`

### Продакшн развертывание:

1. Используйте виртуальное окружение
2. Настройте systemd service (Linux) или Windows Service
3. Настройте логирование в файл
4. Настройте мониторинг
5. Регулярно делайте резервные копии БД

## Поддержка и обновления

### Обновление зависимостей:

```bash
pip install --upgrade -r requirements.txt
```

### Резервное копирование:

```bash
cp bot.db bot_backup_$(date +%Y%m%d).db
```

### Миграции БД:

При изменении схемы БД создавайте скрипты миграции для сохранения существующих данных.

---

*Документация обновлена: $(date)*