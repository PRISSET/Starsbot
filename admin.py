import asyncio
import logging
from aiogram import types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_IDS, CHANNEL_ID
from database import db

logger = logging.getLogger(__name__)

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

def admin_required(func):
    """Декоратор для проверки прав администратора"""
    async def wrapper(message_or_callback, *args, **kwargs):
        user_id = message_or_callback.from_user.id
        if not is_admin(user_id):
            if isinstance(message_or_callback, types.Message):
                await message_or_callback.answer("❌ У вас нет прав администратора.")
            else:
                await message_or_callback.answer("❌ У вас нет прав администратора.", show_alert=True)
            return
        return await func(message_or_callback, *args, **kwargs)
    return wrapper

# Административные команды

async def admin_start(message: types.Message):
    """Главное меню администратора"""
    if not is_admin(message.from_user.id):
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Статистика", callback_data="admin_stats")
    keyboard.button(text="👥 Пользователи", callback_data="admin_users")
    keyboard.button(text="💰 Платежи", callback_data="admin_payments")
    keyboard.button(text="📺 Канал", callback_data="admin_channel")
    keyboard.button(text="🔧 Настройки", callback_data="admin_settings")
    keyboard.adjust(2)
    
    await message.answer(
        "🔧 **Панель администратора**\n\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )

async def admin_menu_show(callback: types.CallbackQuery):
    """Показать главное меню администратора для callback"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Статистика", callback_data="admin_stats")
    keyboard.button(text="👥 Пользователи", callback_data="admin_users")
    keyboard.button(text="💰 Платежи", callback_data="admin_payments")
    keyboard.button(text="📺 Канал", callback_data="admin_channel")
    keyboard.button(text="🔧 Настройки", callback_data="admin_settings")
    keyboard.adjust(2)
    
    await callback.message.edit_text(
        "🔧 **Панель администратора**\n\n"
        "Выберите действие:",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@admin_required
async def show_admin_stats(callback: types.CallbackQuery):
    """Показать статистику бота"""
    # Получение статистики из базы данных
    total_users = await db.get_total_users_count()
    premium_users = await db.get_premium_users_count()
    total_purchases = await db.get_total_purchases_count()
    total_revenue = await db.get_total_revenue()
    
    stats_text = (
        "📊 **Статистика бота**\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"🌟 Премиум пользователей: {premium_users}\n"
        f"💰 Всего покупок: {total_purchases}\n"
        f"⭐ Общий доход: {total_revenue} звезд\n"
    )
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔄 Обновить", callback_data="admin_stats")
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(2)
    
    try:
        await callback.message.edit_text(
            stats_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        # Игнорируем ошибку, если сообщение не изменилось
        if "message is not modified" not in str(e):
            raise e

@admin_required
async def show_admin_users(callback: types.CallbackQuery):
    """Показать информацию о пользователях"""
    recent_users = await db.get_recent_users(10)
    
    users_text = "👥 **Последние пользователи:**\n\n"
    
    for user in recent_users:
        status = "🌟" if user.is_premium_active else "👤"
        users_text += (
            f"{status} {user.first_name or 'Без имени'} "
            f"(@{user.username or 'без username'})\n"
            f"ID: `{user.telegram_id}`\n"
            f"Регистрация: {user.created_at.strftime('%d.%m.%Y')}\n\n"
        )
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔍 Поиск пользователя", callback_data="admin_search_user")
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    try:
        await callback.message.edit_text(
            users_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise e

@admin_required
async def show_admin_payments(callback: types.CallbackQuery):
    """Показать информацию о платежах"""
    recent_payments = await db.get_recent_purchases(10)
    
    payments_text = "💰 **Последние платежи:**\n\n"
    
    for payment in recent_payments:
        payments_text += (
            f"• {payment.product_title}\n"
            f"  👤 ID: `{payment.user_id}`\n"
            f"  💰 {payment.amount} ⭐\n"
            f"  📅 {payment.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 Статистика платежей", callback_data="admin_payment_stats")
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    try:
        await callback.message.edit_text(
            payments_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise e

@admin_required
async def show_admin_settings(callback: types.CallbackQuery):
    """Показать настройки бота"""
    settings_text = (
        "🔧 **Настройки бота**\n\n"
        "Доступные действия:"
    )
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📢 Рассылка", callback_data="admin_broadcast")
    keyboard.button(text="🗄️ Экспорт данных", callback_data="admin_export")
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    try:
        await callback.message.edit_text(
            settings_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise e

@admin_required
async def show_admin_channel(callback: types.CallbackQuery):
    """Показать информацию о канале и управление подписками"""
    # Получаем статистику по подпискам
    active_subscribers = await db.get_active_subscribers()
    expired_subscriptions = await db.get_expired_subscriptions()
    
    # Получаем общую статистику
    all_users = await db.get_all_users()
    total_users = len(all_users)
    users_in_channel = len([u for u in all_users if u.is_in_channel])
    
    stats_text = (
        f"📺 **Управление каналом**\n\n"
        f"🆔 ID канала: `{CHANNEL_ID}`\n\n"
        f"📊 **Статистика:**\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"✅ Активных подписок: {len(active_subscribers)}\n"
        f"❌ Истекших подписок: {len(expired_subscriptions)}\n"
        f"📺 В канале: {users_in_channel}\n\n"
        f"📈 **Конверсия:** {(len(active_subscribers)/total_users*100):.1f}%"
    )
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔄 Синхронизировать канал", callback_data="admin_sync_channel")
    keyboard.button(text="🧹 Очистить истекшие", callback_data="admin_cleanup_expired")
    keyboard.button(text="📋 Список подписчиков", callback_data="admin_subscribers_list")
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    keyboard.adjust(1)
    
    try:
        await callback.message.edit_text(
            stats_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise e
    await callback.answer()

@admin_required
async def admin_sync_channel(callback: types.CallbackQuery):
    """Синхронизация пользователей с каналом"""
    from channel_manager import ChannelManager
    
    channel_manager = ChannelManager(callback.bot)
    
    # Получаем всех пользователей с активными подписками
    active_subscribers = await db.get_active_subscribers()
    
    added_count = 0
    removed_count = 0
    
    # Добавляем пользователей с активными подписками
    for user in active_subscribers:
        if not user.is_in_channel:
            success = await channel_manager.add_user_to_channel(user.user_id)
            if success:
                added_count += 1
    
    # Удаляем пользователей с истекшими подписками
    expired_users = await db.get_expired_subscriptions()
    for user in expired_users:
        if user.is_in_channel:
            success = await channel_manager.remove_user_from_channel(user.user_id)
            if success:
                removed_count += 1
    
    result_text = (
        f"✅ **Синхронизация завершена**\n\n"
        f"➕ Добавлено: {added_count}\n"
        f"➖ Удалено: {removed_count}"
    )
    
    await callback.answer(result_text, show_alert=True)
    
    # Обновляем статистику
    await show_admin_channel(callback)

@admin_required
async def admin_cleanup_expired(callback: types.CallbackQuery):
    """Очистка пользователей с истекшими подписками"""
    from channel_manager import ChannelManager
    
    channel_manager = ChannelManager(callback.bot)
    removed_count = await channel_manager.cleanup_expired_subscriptions()
    
    result_text = f"🧹 Удалено пользователей с истекшими подписками: {removed_count}"
    await callback.answer(result_text, show_alert=True)
    
    # Обновляем статистику
    await show_admin_channel(callback)

@admin_required
async def admin_subscribers_list(callback: types.CallbackQuery):
    """Показать список активных подписчиков"""
    active_subscribers = await db.get_active_subscribers()
    
    if not active_subscribers:
        await callback.answer("📭 Нет активных подписчиков", show_alert=True)
        return
    
    # Ограничиваем список первыми 20 пользователями
    subscribers_text = "👥 **Активные подписчики:**\n\n"
    
    for i, user in enumerate(active_subscribers[:20], 1):
        status_emoji = "✅" if user.is_in_channel else "❌"
        subscribers_text += (
            f"{i}. {status_emoji} {user.first_name} (@{user.username or 'нет'})\n"
            f"   До: {user.subscription_until.strftime('%d.%m.%Y %H:%M')}\n\n"
        )
    
    if len(active_subscribers) > 20:
        subscribers_text += f"... и еще {len(active_subscribers) - 20} подписчиков"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="admin_channel")
    
    try:
        await callback.message.edit_text(
            subscribers_text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        if "message is not modified" not in str(e):
            raise e
    await callback.answer()

async def show_admin_broadcast(callback_or_message):
    """Показать интерфейс рассылки"""
    user_id = callback_or_message.from_user.id
    
    if not is_admin(user_id):
        if hasattr(callback_or_message, 'answer'):
            await callback_or_message.answer("❌ У вас нет прав администратора", show_alert=True)
        else:
            await callback_or_message.reply("❌ У вас нет прав администратора")
        return
    
    text = (
        "📢 **Рассылка сообщений**\n\n"
        "Для отправки рассылки используйте команду:\n"
        "`/broadcast <текст сообщения>`\n\n"
        "Сообщение будет отправлено всем пользователям бота."
    )
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    
    if hasattr(callback_or_message, 'message'):
        # Это callback
        await callback_or_message.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await callback_or_message.answer()
    else:
        # Это message
        await callback_or_message.reply(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

@admin_required
async def show_admin_export(callback: types.CallbackQuery):
    """Экспорт данных пользователей"""
    try:
        csv_data = await export_users_data()
        
        # Создаем временный файл
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(csv_data)
            temp_file_path = f.name
        
        # Отправляем файл
        from aiogram.types import FSInputFile
        file = FSInputFile(temp_file_path, filename="users_export.csv")
        
        await callback.message.answer_document(
            file,
            caption="📊 Экспорт данных пользователей"
        )
        
        # Удаляем временный файл
        os.unlink(temp_file_path)
        
        await callback.answer("✅ Данные экспортированы", show_alert=True)
        
    except Exception as e:
        await callback.answer(f"❌ Ошибка экспорта: {str(e)}", show_alert=True)

async def show_admin_search_user(callback_or_message):
    """Показать интерфейс поиска пользователя"""
    user_id = callback_or_message.from_user.id
    
    if not is_admin(user_id):
        if hasattr(callback_or_message, 'answer'):
            await callback_or_message.answer("❌ У вас нет прав администратора", show_alert=True)
        else:
            await callback_or_message.reply("❌ У вас нет прав администратора")
        return
    
    text = (
        "🔍 **Поиск пользователя**\n\n"
        "Для поиска пользователя используйте команду:\n"
        "`/search_user <ID или username>`\n\n"
        "Вы получите информацию о пользователе и его подписках."
    )
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="admin_menu")
    
    if hasattr(callback_or_message, 'message'):
        # Это callback
        await callback_or_message.message.edit_text(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )
        await callback_or_message.answer()
    else:
        # Это message
        await callback_or_message.reply(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode="Markdown"
        )

@admin_required
async def show_admin_payment_stats(callback: types.CallbackQuery):
    """Показать детальную статистику платежей"""
    # Получаем статистику платежей
    total_revenue = await db.get_total_revenue()
    total_purchases = await db.get_total_purchases_count()
    recent_payments = await db.get_recent_purchases(5)
    
    # Получаем статистику по дням (последние 7 дней)
    from datetime import datetime, timedelta
    today = datetime.now()
    daily_stats = []
    
    for i in range(7):
        date = today - timedelta(days=i)
        day_revenue = await db.get_revenue_by_date(date.date())
        day_purchases = await db.get_purchases_count_by_date(date.date())
        daily_stats.append((date.strftime('%d.%m'), day_revenue, day_purchases))
    
    stats_text = (
        "📊 **Детальная статистика платежей**\n\n"
        f"💰 Общий доход: {total_revenue} ⭐\n"
        f"🛒 Всего покупок: {total_purchases}\n\n"
        "📈 **Статистика по дням:**\n"
    )
    
    for date_str, revenue, purchases in daily_stats:
        stats_text += f"• {date_str}: {revenue} ⭐ ({purchases} покупок)\n"
    
    if recent_payments:
        stats_text += "\n🕒 **Последние платежи:**\n"
        for payment in recent_payments:
            stats_text += (
                f"• {payment.product_title} - {payment.amount} ⭐\n"
                f"  👤 ID: {payment.user_id}\n"
            )
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="admin_payments")
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

# Функции для регистрации обработчиков
def register_admin_handlers(dp):
    """Регистрация административных обработчиков"""
    
    @dp.message(Command("admin"))
    async def admin_command(message: types.Message):
        await admin_start(message)
    
    @dp.callback_query(lambda c: c.data == "admin_stats")
    async def admin_stats_callback(callback: types.CallbackQuery):
        await show_admin_stats(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_users")
    async def admin_users_callback(callback: types.CallbackQuery):
        await show_admin_users(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_payments")
    async def admin_payments_callback(callback: types.CallbackQuery):
        await show_admin_payments(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_channel")
    async def admin_channel_callback(callback: types.CallbackQuery):
        await show_admin_channel(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_sync_channel")
    async def admin_sync_channel_callback(callback: types.CallbackQuery):
        await admin_sync_channel(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_cleanup_expired")
    async def admin_cleanup_expired_callback(callback: types.CallbackQuery):
        await admin_cleanup_expired(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_subscribers_list")
    async def admin_subscribers_list_callback(callback: types.CallbackQuery):
        await admin_subscribers_list(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_settings")
    async def admin_settings_callback(callback: types.CallbackQuery):
        await show_admin_settings(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_menu")
    async def admin_menu_callback(callback: types.CallbackQuery):
        await admin_menu_show(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_broadcast")
    async def admin_broadcast_callback(callback: types.CallbackQuery):
        await show_admin_broadcast(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_export")
    async def admin_export_callback(callback: types.CallbackQuery):
        await show_admin_export(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_search_user")
    async def admin_search_user_callback(callback: types.CallbackQuery):
        await show_admin_search_user(callback)
    
    @dp.callback_query(lambda c: c.data == "admin_payment_stats")
    async def admin_payment_stats_callback(callback: types.CallbackQuery):
        await show_admin_payment_stats(callback)

# Дополнительные административные функции

async def send_broadcast(bot, message_text: str, user_ids: list = None):
    """Отправка рассылки пользователям"""
    if user_ids is None:
        user_ids = await db.get_all_user_ids()
    
    success_count = 0
    error_count = 0
    
    for user_id in user_ids:
        try:
            await bot.send_message(user_id, message_text, parse_mode="Markdown")
            success_count += 1
            await asyncio.sleep(0.05)  # Задержка для избежания лимитов
        except Exception as e:
            error_count += 1
            logger.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
    
    return success_count, error_count

async def export_users_data():
    """Экспорт данных пользователей в CSV формат"""
    users = await db.get_all_users()
    
    csv_data = "ID,Username,First Name,Last Name,Is Premium,Created At\n"
    
    for user in users:
        csv_data += (
            f"{user.telegram_id},"
            f"{user.username or ''},"
            f"{user.first_name or ''},"
            f"{user.last_name or ''},"
            f"{user.is_premium_active},"
            f"{user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
    
    return csv_data