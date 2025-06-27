#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Утилиты для Telegram бота с платежами звездами

Этот модуль содержит вспомогательные функции для:
- Форматирования сообщений
- Валидации данных
- Работы с датами
- Экспорта данных
- Логирования
"""

import csv
import json
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from io import StringIO

# Настройка логирования
logger = logging.getLogger(__name__)

def format_datetime(dt: datetime, format_type: str = "full") -> str:
    """
    Форматирует дату и время для отображения пользователю
    
    Args:
        dt: Объект datetime
        format_type: Тип форматирования ('full', 'date', 'time', 'relative')
    
    Returns:
        Отформатированная строка
    """
    if dt is None:
        return "Не указано"
    
    if format_type == "full":
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    elif format_type == "date":
        return dt.strftime("%d.%m.%Y")
    elif format_type == "time":
        return dt.strftime("%H:%M:%S")
    elif format_type == "relative":
        return format_relative_time(dt)
    else:
        return dt.strftime("%d.%m.%Y %H:%M")

def format_relative_time(dt: datetime) -> str:
    """
    Форматирует время относительно текущего момента
    
    Args:
        dt: Объект datetime
    
    Returns:
        Строка вида "2 дня назад", "через 5 часов"
    """
    now = datetime.now()
    diff = dt - now
    
    if diff.total_seconds() > 0:
        # Будущее время
        if diff.days > 0:
            return f"через {diff.days} дн."
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"через {hours} ч."
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"через {minutes} мин."
        else:
            return "через несколько секунд"
    else:
        # Прошедшее время
        diff = now - dt
        if diff.days > 0:
            return f"{diff.days} дн. назад"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} ч. назад"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} мин. назад"
        else:
            return "только что"

def format_stars_amount(amount: int) -> str:
    """
    Форматирует количество звезд для отображения
    
    Args:
        amount: Количество звезд
    
    Returns:
        Отформатированная строка
    """
    if amount == 1:
        return "1 звезда"
    elif 2 <= amount <= 4:
        return f"{amount} звезды"
    else:
        return f"{amount} звезд"

def format_premium_status(is_active: bool, until: Optional[datetime] = None) -> str:
    """
    Форматирует статус премиума
    
    Args:
        is_active: Активен ли премиум
        until: Дата окончания премиума
    
    Returns:
        Отформатированная строка статуса
    """
    if not is_active:
        return "❌ Обычный пользователь"
    
    if until:
        if until > datetime.now():
            return f"⭐ Премиум до {format_datetime(until, 'date')}"
        else:
            return "❌ Премиум истек"
    else:
        return "⭐ Премиум активен"

def validate_telegram_id(telegram_id: Any) -> bool:
    """
    Валидирует Telegram ID
    
    Args:
        telegram_id: ID для проверки
    
    Returns:
        True если ID валиден
    """
    try:
        tid = int(telegram_id)
        return 1 <= tid <= 999999999999  # Примерные границы Telegram ID
    except (ValueError, TypeError):
        return False

def validate_username(username: str) -> bool:
    """
    Валидирует username Telegram
    
    Args:
        username: Username для проверки
    
    Returns:
        True если username валиден
    """
    if not username:
        return True  # Username может быть пустым
    
    # Username должен содержать только буквы, цифры и подчеркивания
    # Длина от 5 до 32 символов
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    return bool(re.match(pattern, username))

def validate_product_id(product_id: str, products: Dict) -> bool:
    """
    Валидирует ID товара
    
    Args:
        product_id: ID товара
        products: Словарь доступных товаров
    
    Returns:
        True если товар существует
    """
    return product_id in products

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """
    Очищает текст от потенциально опасных символов
    
    Args:
        text: Текст для очистки
        max_length: Максимальная длина
    
    Returns:
        Очищенный текст
    """
    if not text:
        return ""
    
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    
    # Ограничиваем длину
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text.strip()

def create_pagination_keyboard(current_page: int, total_pages: int, callback_prefix: str) -> List[List[Dict]]:
    """
    Создает клавиатуру для пагинации
    
    Args:
        current_page: Текущая страница (начиная с 1)
        total_pages: Общее количество страниц
        callback_prefix: Префикс для callback data
    
    Returns:
        Список кнопок для InlineKeyboardMarkup
    """
    keyboard = []
    
    if total_pages <= 1:
        return keyboard
    
    buttons = []
    
    # Кнопка "Назад"
    if current_page > 1:
        buttons.append({
            "text": "⬅️ Назад",
            "callback_data": f"{callback_prefix}_{current_page - 1}"
        })
    
    # Информация о странице
    buttons.append({
        "text": f"{current_page}/{total_pages}",
        "callback_data": "noop"
    })
    
    # Кнопка "Вперед"
    if current_page < total_pages:
        buttons.append({
            "text": "Вперед ➡️",
            "callback_data": f"{callback_prefix}_{current_page + 1}"
        })
    
    if buttons:
        keyboard.append(buttons)
    
    return keyboard

def export_users_to_csv(users: List[Any]) -> str:
    """
    Экспортирует пользователей в CSV формат
    
    Args:
        users: Список пользователей
    
    Returns:
        CSV строка
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'Telegram ID',
        'Username',
        'Имя',
        'Фамилия',
        'Дата регистрации',
        'Премиум статус',
        'Премиум до'
    ])
    
    # Данные пользователей
    for user in users:
        writer.writerow([
            user.telegram_id,
            user.username or '',
            user.first_name or '',
            user.last_name or '',
            format_datetime(user.registration_date, 'full'),
            'Да' if user.is_premium_active else 'Нет',
            format_datetime(user.premium_until, 'full') if user.premium_until else ''
        ])
    
    return output.getvalue()

def export_purchases_to_csv(purchases: List[Any]) -> str:
    """
    Экспортирует покупки в CSV формат
    
    Args:
        purchases: Список покупок
    
    Returns:
        CSV строка
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # Заголовки
    writer.writerow([
        'ID покупки',
        'Telegram ID пользователя',
        'ID товара',
        'Название товара',
        'Сумма (звезды)',
        'Дата покупки',
        'ID платежа Telegram'
    ])
    
    # Данные покупок
    for purchase in purchases:
        writer.writerow([
            purchase.id,
            purchase.user_id,
            purchase.product_id,
            purchase.product_title,
            purchase.amount,
            format_datetime(purchase.purchase_date, 'full'),
            purchase.telegram_payment_charge_id
        ])
    
    return output.getvalue()

def calculate_statistics(users: List[Any], purchases: List[Any]) -> Dict[str, Any]:
    """
    Вычисляет статистику по пользователям и покупкам
    
    Args:
        users: Список пользователей
        purchases: Список покупок
    
    Returns:
        Словарь со статистикой
    """
    now = datetime.now()
    
    # Статистика пользователей
    total_users = len(users)
    premium_users = sum(1 for user in users if user.is_premium_active)
    
    # Новые пользователи за последние 7 дней
    week_ago = now - timedelta(days=7)
    new_users_week = sum(
        1 for user in users 
        if user.registration_date and user.registration_date >= week_ago
    )
    
    # Статистика покупок
    total_purchases = len(purchases)
    total_revenue = sum(purchase.amount for purchase in purchases)
    
    # Покупки за последние 7 дней
    purchases_week = [
        purchase for purchase in purchases
        if purchase.purchase_date and purchase.purchase_date >= week_ago
    ]
    revenue_week = sum(purchase.amount for purchase in purchases_week)
    
    # Средний чек
    avg_purchase = total_revenue / total_purchases if total_purchases > 0 else 0
    
    # Популярные товары
    product_stats = {}
    for purchase in purchases:
        product_id = purchase.product_id
        if product_id not in product_stats:
            product_stats[product_id] = {
                'count': 0,
                'revenue': 0,
                'title': purchase.product_title
            }
        product_stats[product_id]['count'] += 1
        product_stats[product_id]['revenue'] += purchase.amount
    
    # Сортируем по количеству продаж
    popular_products = sorted(
        product_stats.items(),
        key=lambda x: x[1]['count'],
        reverse=True
    )[:5]
    
    return {
        'users': {
            'total': total_users,
            'premium': premium_users,
            'premium_percentage': (premium_users / total_users * 100) if total_users > 0 else 0,
            'new_week': new_users_week
        },
        'purchases': {
            'total': total_purchases,
            'revenue': total_revenue,
            'week_count': len(purchases_week),
            'week_revenue': revenue_week,
            'avg_purchase': avg_purchase
        },
        'popular_products': popular_products
    }

def format_statistics_message(stats: Dict[str, Any]) -> str:
    """
    Форматирует статистику для отображения в сообщении
    
    Args:
        stats: Словарь со статистикой
    
    Returns:
        Отформатированное сообщение
    """
    message = "📊 **Статистика бота**\n\n"
    
    # Пользователи
    users = stats['users']
    message += f"👥 **Пользователи:**\n"
    message += f"   Всего: {users['total']}\n"
    message += f"   Премиум: {users['premium']} ({users['premium_percentage']:.1f}%)\n"
    message += f"   Новых за неделю: {users['new_week']}\n\n"
    
    # Покупки
    purchases = stats['purchases']
    message += f"💰 **Покупки:**\n"
    message += f"   Всего: {purchases['total']}\n"
    message += f"   Доход: {format_stars_amount(purchases['revenue'])}\n"
    message += f"   За неделю: {purchases['week_count']} ({format_stars_amount(purchases['week_revenue'])})\n"
    message += f"   Средний чек: {purchases['avg_purchase']:.1f} звезд\n\n"
    
    # Популярные товары
    if stats['popular_products']:
        message += f"🏆 **Популярные товары:**\n"
        for i, (product_id, data) in enumerate(stats['popular_products'], 1):
            message += f"   {i}. {data['title']}: {data['count']} продаж\n"
    
    return message

def log_user_action(user_id: int, action: str, details: str = ""):
    """
    Логирует действие пользователя
    
    Args:
        user_id: ID пользователя
        action: Тип действия
        details: Дополнительные детали
    """
    logger.info(f"User {user_id} performed action: {action}. Details: {details}")

def log_payment(user_id: int, product_id: str, amount: int, charge_id: str):
    """
    Логирует платеж
    
    Args:
        user_id: ID пользователя
        product_id: ID товара
        amount: Сумма платежа
        charge_id: ID платежа
    """
    logger.info(
        f"Payment processed: User {user_id}, Product {product_id}, "
        f"Amount {amount} stars, Charge ID {charge_id}"
    )

def log_error(error: Exception, context: str = ""):
    """
    Логирует ошибку
    
    Args:
        error: Объект исключения
        context: Контекст ошибки
    """
    logger.error(f"Error in {context}: {str(error)}", exc_info=True)

def create_backup_filename() -> str:
    """
    Создает имя файла для резервной копии
    
    Returns:
        Имя файла с текущей датой и временем
    """
    now = datetime.now()
    return f"bot_backup_{now.strftime('%Y%m%d_%H%M%S')}.db"

def parse_admin_ids(admin_ids_str: str) -> List[int]:
    """
    Парсит строку с ID администраторов
    
    Args:
        admin_ids_str: Строка с ID через запятую
    
    Returns:
        Список ID администраторов
    """
    if not admin_ids_str:
        return []
    
    admin_ids = []
    for id_str in admin_ids_str.split(','):
        try:
            admin_id = int(id_str.strip())
            if validate_telegram_id(admin_id):
                admin_ids.append(admin_id)
        except ValueError:
            logger.warning(f"Invalid admin ID: {id_str}")
    
    return admin_ids

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Разбивает список на части заданного размера
    
    Args:
        lst: Исходный список
        chunk_size: Размер части
    
    Returns:
        Список частей
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def escape_markdown(text: str) -> str:
    """
    Экранирует специальные символы для Markdown
    
    Args:
        text: Исходный текст
    
    Returns:
        Экранированный текст
    """
    if not text:
        return ""
    
    # Символы, которые нужно экранировать в Markdown
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

# Константы для форматирования
EMOJI_SUCCESS = "✅"
EMOJI_ERROR = "❌"
EMOJI_WARNING = "⚠️"
EMOJI_INFO = "ℹ️"
EMOJI_PREMIUM = "⭐"
EMOJI_MONEY = "💰"
EMOJI_STATS = "📊"
EMOJI_USER = "👤"
EMOJI_USERS = "👥"
EMOJI_SETTINGS = "⚙️"
EMOJI_BACK = "🔙"
EMOJI_MENU = "📋"