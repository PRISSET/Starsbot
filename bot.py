import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import BOT_TOKEN, PROVIDER_TOKEN, SUBSCRIPTION_PRICES, CHANNEL_ID, CHANNEL_INVITE_LINK
from database import db, init_database
from admin import register_admin_handlers, show_admin_broadcast, show_admin_search_user
from channel_manager import ChannelManager, subscription_cleanup_task

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
channel_manager = ChannelManager(bot)

def get_back_keyboard():
    """Создать клавиатуру с кнопкой назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    return keyboard

# Подписки для покупки
SUBSCRIPTIONS = {
    "1_month": {
        "title": "Подписка на 1 месяц",
        "description": "Доступ к приватному каналу на 1 месяц",
        "price": SUBSCRIPTION_PRICES["1_month"],
        "days": 30
    },
    "3_months": {
        "title": "Подписка на 3 месяца",
        "description": "Доступ к приватному каналу на 3 месяца",
        "price": SUBSCRIPTION_PRICES["3_months"],
        "days": 90
    },
    "6_months": {
        "title": "Подписка на 6 месяцев",
        "description": "Доступ к приватному каналу на 6 месяцев",
        "price": SUBSCRIPTION_PRICES["6_months"],
        "days": 180
    },
    "12_months": {
        "title": "Подписка на 12 месяцев",
        "description": "Доступ к приватному каналу на 12 месяцев",
        "price": SUBSCRIPTION_PRICES["12_months"],
        "days": 365
    }
}

@dp.message(Command("start"))
async def start_command(message: types.Message):
    """Обработчик команды /start"""
    # Создание или обновление пользователя в базе данных
    user = await db.create_or_update_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    # Проверяем статус подписки
    subscription_status = ""
    if user.is_subscription_active:
        subscription_status = f"\n✅ У вас активная подписка до {user.subscription_until.strftime('%d.%m.%Y %H:%M')}"
    else:
        subscription_status = "\n❌ У вас нет активной подписки"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💎 Подписки", callback_data="subscriptions")
    keyboard.button(text="ℹ️ О канале", callback_data="channel_info")
    keyboard.button(text="👤 Профиль", callback_data="profile")
    keyboard.adjust(2, 1)
    
    await message.answer(
        f"🌟 Добро пожаловать в бот подписок!\n\n"
        f"Здесь вы можете приобрести доступ к нашему приватному каналу за звезды Telegram.{subscription_status}",
        reply_markup=keyboard.as_markup()
    )

@dp.callback_query(lambda c: c.data == "subscriptions")
async def show_subscriptions(callback: types.CallbackQuery):
    """Показать доступные подписки"""
    keyboard = InlineKeyboardBuilder()
    
    for subscription_id, subscription in SUBSCRIPTIONS.items():
        keyboard.button(
            text=f"{subscription['title']} - {subscription['price']} ⭐",
            callback_data=f"buy_{subscription_id}"
        )
    
    keyboard.button(text="🔙 Назад", callback_data="back_to_main")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "💎 **Доступные подписки**\n\n"
        "Выберите подписку для покупки:\n\n"
        "📺 Получите доступ к эксклюзивному контенту нашего приватного канала!",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def process_purchase(callback: types.CallbackQuery):
    """Обработка покупки подписки"""
    subscription_id = callback.data.replace("buy_", "")
    
    if subscription_id not in SUBSCRIPTIONS:
        await callback.answer("Подписка не найдена!", show_alert=True)
        return
    
    subscription = SUBSCRIPTIONS[subscription_id]
    
    # Проверяем, есть ли у пользователя уже активная подписка
    user = await db.get_user(callback.from_user.id)
    if user and user.is_subscription_active:
        await callback.answer(
            f"У вас уже есть активная подписка до {user.subscription_until.strftime('%d.%m.%Y')}. "
            "Новая подписка будет добавлена к текущей.",
            show_alert=True
        )
    
    # Создание инвойса для оплаты звездами
    prices = [LabeledPrice(label=subscription["title"], amount=subscription["price"])]
    
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=subscription["title"],
        description=subscription["description"],
        payload=f"subscription_{subscription_id}",
        provider_token="",  # Для звезд Telegram не нужен
        currency="XTR",  # Валюта для звезд Telegram
        prices=prices
    )
    
    await callback.answer()

@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Обработка предварительной проверки платежа"""
    # Здесь можно добавить дополнительные проверки
    await bot.answer_pre_checkout_query(
        pre_checkout_query.id,
        ok=True
    )

@dp.message(lambda message: message.content_type == types.ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    """Обработка успешного платежа"""
    payment = message.successful_payment
    subscription_id = payment.invoice_payload.replace("subscription_", "")
    
    if subscription_id in SUBSCRIPTIONS:
        subscription = SUBSCRIPTIONS[subscription_id]
        
        # Сохранение покупки в базе данных
        await db.create_purchase(
            user_id=message.from_user.id,
            product_id=subscription_id,
            product_title=subscription['title'],
            amount=payment.total_amount,
            telegram_payment_charge_id=payment.telegram_payment_charge_id,
            provider_payment_charge_id=payment.provider_payment_charge_id
        )
        
        # Активация подписки
        await db.activate_subscription(message.from_user.id, subscription['days'])
        
        # Добавление пользователя в канал
        success = await channel_manager.add_user_to_channel(message.from_user.id)
        
        if success:
            await message.answer(
                f"✅ **Платеж успешно обработан!**\n\n"
                f"Подписка: {subscription['title']}\n"
                f"Сумма: {payment.total_amount} ⭐\n"
                f"Период: {subscription['days']} дней\n"
                f"ID транзакции: `{payment.telegram_payment_charge_id}`\n\n"
                f"🎉 Ваша подписка активирована!\n"
                f"Проверьте личные сообщения - вам отправлена ссылка для вступления в канал.",
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                f"✅ **Платеж обработан, но возникла проблема с добавлением в канал.**\n\n"
                f"Подписка: {subscription['title']}\n"
                f"Сумма: {payment.total_amount} ⭐\n\n"
                f"⚠️ Обратитесь в поддержку для получения доступа к каналу.",
                parse_mode="Markdown"
            )
        
        # Логирование успешного платежа
        logger.info(
            f"Successful payment: User {message.from_user.id}, "
            f"Subscription {subscription_id}, Amount {payment.total_amount} stars, "
            f"Days {subscription['days']}"
        )
    else:
        await message.answer("❌ Ошибка при обработке платежа. Обратитесь в поддержку.")

@dp.callback_query(lambda c: c.data == "info")
async def show_info(callback: types.CallbackQuery):
    """Показать информацию о боте"""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 Назад", callback_data="back_to_main")
    
    await callback.message.edit_text(
        "ℹ️ **Информация о боте**\n\n"
        "Этот бот позволяет покупать премиум функции за звезды Telegram.\n\n"
        "🌟 **Что такое звезды Telegram?**\n"
        "Звезды - это внутренняя валюта Telegram для покупок в ботах.\n\n"
        "💳 **Как купить звезды?**\n"
        "Звезды можно купить прямо в Telegram через настройки.",
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "profile")
async def show_profile(callback: types.CallbackQuery):
    """Показать профиль пользователя"""
    user = await db.get_user(callback.from_user.id)
    
    if user:
        subscription_status = "✅ Активна" if user.is_subscription_active else "❌ Неактивна"
        subscription_until = user.subscription_until.strftime("%d.%m.%Y %H:%M") if user.subscription_until else "Не установлено"
        channel_status = "✅ В канале" if user.is_in_channel else "❌ Не в канале"
        
        profile_text = (
            f"👤 **Ваш профиль**\n\n"
            f"🆔 ID: `{user.telegram_id}`\n"
            f"👤 Имя: {user.first_name}\n"
            f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📺 Подписка на канал: {subscription_status}\n"
            f"⏰ Подписка до: {subscription_until}\n"
            f"📍 Статус в канале: {channel_status}\n\n"
            f"💰 Всего покупок: 0"
        )
    else:
        profile_text = "❌ Профиль не найден. Попробуйте перезапустить бота командой /start"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📊 История покупок", callback_data="purchase_history")
    keyboard.button(text="🔙 Назад", callback_data="back_to_main")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "purchase_history")
async def show_purchase_history(callback: types.CallbackQuery):
    """Показать историю покупок"""
    purchases = await db.get_user_purchases(callback.from_user.id)
    
    if purchases:
        history_text = "📊 **История ваших покупок:**\n\n"
        for purchase in purchases[-5:]:  # Показываем последние 5 покупок
            history_text += (
                f"• {purchase.product_title}\n"
                f"  💰 {purchase.amount} ⭐\n"
                f"  📅 {purchase.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
    else:
        history_text = "📊 **История покупок**\n\nУ вас пока нет покупок."
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🔙 К профилю", callback_data="profile")
    
    await callback.message.edit_text(
        history_text,
        reply_markup=keyboard.as_markup(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "channel_info")
async def show_channel_info(callback: types.CallbackQuery):
    """Показать информацию о канале"""
    user = await db.get_user(callback.from_user.id)
    
    if user and user.is_subscription_active:
        # Получаем информацию о канале
        channel_info = await channel_manager.get_channel_info()
        
        if channel_info:
            info_text = (
                f"📺 **Информация о канале**\n\n"
                f"📋 Название: {channel_info.get('title', 'Приватный канал')}\n"
                f"👥 Участников: {channel_info.get('members_count', 'Неизвестно')}\n"
                f"📝 Описание: {channel_info.get('description', 'Эксклюзивный контент для подписчиков')}\n\n"
                f"✅ У вас есть активная подписка!\n"
                f"⏰ Действует до: {user.subscription_until.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
            
            if user.is_in_channel:
                info_text += "🎉 Вы уже состоите в канале!"
            else:
                info_text += "🔗 Нажмите кнопку ниже для вступления в канал."
                
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔗 Вступить в канал", url=CHANNEL_INVITE_LINK)
            keyboard.button(text="🔙 Назад", callback_data="back_to_main")
            keyboard.adjust(1)
        else:
            info_text = "❌ Не удалось получить информацию о канале."
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="🔙 Назад", callback_data="back_to_main")
    else:
        info_text = (
            f"📺 **Приватный канал**\n\n"
            f"🔒 Для доступа к каналу необходима активная подписка.\n\n"
            f"💎 В канале вы найдете:\n"
            f"• Эксклюзивный контент\n"
            f"• Полезные материалы\n"
            f"• Общение с единомышленниками\n\n"
            f"📺 Оформите подписку для получения доступа!"
        )
        
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="📺 Подписки", callback_data="subscriptions")
        keyboard.button(text="🔙 Назад", callback_data="back_to_main")
        keyboard.adjust(1)
    
    await callback.message.edit_text(
        info_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback: types.CallbackQuery):
    """Вернуться в главное меню"""
    user = await db.get_user(callback.from_user.id)
    
    if user:
        subscription_status = "✅ Активна" if user.is_subscription_active else "❌ Неактивна"
        subscription_info = ""
        
        if user.is_subscription_active:
            subscription_info = f"\n⏰ Действует до: {user.subscription_until.strftime('%d.%m.%Y %H:%M')}"
        
        welcome_text = (
            f"🏠 **Добро пожаловать, {user.first_name}!**\n\n"
            f"📺 Статус подписки: {subscription_status}{subscription_info}\n\n"
            f"Выберите действие:"
        )
    else:
        welcome_text = "🏠 **Главное меню**\n\nВыберите действие:"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="💎 Подписки", callback_data="subscriptions")
    keyboard.button(text="ℹ️ О канале", callback_data="channel_info")
    keyboard.button(text="👤 Профиль", callback_data="profile")
    keyboard.adjust(2, 1)
    
    await callback.message.edit_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    """Обработчик команды /broadcast"""
    from admin import is_admin, send_broadcast
    
    if not is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав администратора")
        return
    
    # Получаем текст после команды
    command_args = message.text.split(' ', 1)
    if len(command_args) < 2:
        await show_admin_broadcast(message)
        return
    
    broadcast_text = command_args[1]
    
    # Отправляем рассылку
    await message.reply("📤 Начинаю рассылку...")
    success_count, error_count = await send_broadcast(bot, broadcast_text)
    
    result_text = (
        f"✅ Рассылка завершена!\n\n"
        f"📊 Статистика:\n"
        f"• Успешно отправлено: {success_count}\n"
        f"• Ошибок: {error_count}"
    )
    
    await message.reply(result_text)

@dp.message(Command("search_user"))
async def search_user_command(message: types.Message):
    """Обработчик команды /search_user"""
    from admin import is_admin
    
    if not is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав администратора")
        return
    
    # Получаем аргумент после команды
    command_args = message.text.split(' ', 1)
    if len(command_args) < 2:
        await show_admin_search_user(message)
        return
    
    search_query = command_args[1].strip()
    
    # Поиск пользователя
    try:
        if search_query.startswith('@'):
            username = search_query[1:]
            user = await db.get_user_by_username(username)
        else:
            user_id = int(search_query)
            user = await db.get_user_by_id(user_id)
        
        if not user:
            await message.reply(f"❌ Пользователь '{search_query}' не найден")
            return
        
        # Получаем информацию о подписках
        subscriptions = await db.get_user_subscriptions(user.telegram_id)
        
        user_info = (
            f"👤 **Информация о пользователе**\n\n"
            f"🆔 ID: `{user.telegram_id}`\n"
            f"👤 Имя: {user.first_name or 'Не указано'}\n"
            f"📝 Username: @{user.username or 'Не указан'}\n"
            f"💎 Премиум: {'Да' if user.is_premium_active else 'Нет'}\n"
            f"📅 Регистрация: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        )
        
        if subscriptions:
            user_info += "📋 **Подписки:**\n"
            for sub in subscriptions:
                status = "Активна" if sub.is_active else "Неактивна"
                user_info += f"• {sub.product_title} - {status}\n"
        else:
            user_info += "📋 **Подписки:** Нет активных подписок\n"
        
        await message.reply(user_info, parse_mode="Markdown")
        
    except ValueError:
        await message.reply("❌ Неверный формат ID пользователя")
    except Exception as e:
        await message.reply(f"❌ Ошибка поиска: {str(e)}")

async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")
    
    try:
        # Инициализация базы данных
        await init_database()
        
        # Запуск задачи очистки истекших подписок
        asyncio.create_task(subscription_cleanup_task(bot))
        
        # Регистрация административных обработчиков
        register_admin_handlers(dp)
        
        # Удаление вебхука (если был установлен)
        await bot.delete_webhook(drop_pending_updates=True)
        
        logger.info("Bot started with subscription cleanup task")
        
        # Запуск поллинга
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())