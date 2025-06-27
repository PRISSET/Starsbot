import asyncio
import logging
from datetime import datetime
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from config import CHANNEL_ID, CHANNEL_INVITE_LINK
from database import db

logger = logging.getLogger(__name__)

class ChannelManager:
    """Класс для управления участниками приватного канала"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.channel_id = CHANNEL_ID
        self.invite_link = CHANNEL_INVITE_LINK
    
    async def add_user_to_channel(self, user_id: int) -> bool:
        """Добавление пользователя в приватный канал"""
        try:
            # Создаем пригласительную ссылку для конкретного пользователя
            invite_link = await self.bot.create_chat_invite_link(
                chat_id=self.channel_id,
                member_limit=1,  # Ссылка только для одного пользователя
                expire_date=datetime.now().timestamp() + 3600  # Ссылка действует 1 час
            )
            
            # Отправляем пользователю ссылку для вступления
            await self.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Ваша подписка активирована!\n\n"
                     f"Присоединяйтесь к нашему приватному каналу:\n"
                     f"{invite_link.invite_link}\n\n"
                     f"⚠️ Ссылка действительна в течение 1 часа."
            )
            
            # Обновляем статус в базе данных
            await db.update_channel_status(user_id, True)
            
            logger.info(f"Пользователь {user_id} приглашен в канал")
            return True
            
        except TelegramBadRequest as e:
            logger.error(f"Ошибка при добавлении пользователя {user_id} в канал: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при добавлении пользователя {user_id}: {e}")
            return False
    
    async def remove_user_from_channel(self, user_id: int) -> bool:
        """Удаление пользователя из приватного канала"""
        try:
            # Банним пользователя (удаляем из канала)
            await self.bot.ban_chat_member(
                chat_id=self.channel_id,
                user_id=user_id
            )
            
            # Сразу разбаниваем, чтобы пользователь мог вернуться при покупке новой подписки
            await self.bot.unban_chat_member(
                chat_id=self.channel_id,
                user_id=user_id
            )
            
            # Обновляем статус в базе данных
            await db.update_channel_status(user_id, False)
            
            # Уведомляем пользователя
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text="⏰ Ваша подписка истекла.\n\n"
                         "Вы были удалены из приватного канала.\n"
                         "Для продления подписки используйте команду /start"
                )
            except (TelegramBadRequest, TelegramForbiddenError):
                # Пользователь заблокировал бота или удалил аккаунт
                pass
            
            logger.info(f"Пользователь {user_id} удален из канала")
            return True
            
        except TelegramBadRequest as e:
            logger.error(f"Ошибка при удалении пользователя {user_id} из канала: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при удалении пользователя {user_id}: {e}")
            return False
    
    async def check_user_in_channel(self, user_id: int) -> bool:
        """Проверка, находится ли пользователь в канале"""
        try:
            member = await self.bot.get_chat_member(
                chat_id=self.channel_id,
                user_id=user_id
            )
            
            # Пользователь в канале, если он участник, администратор или создатель
            is_member = member.status in ['member', 'administrator', 'creator']
            
            # Обновляем статус в базе данных
            await db.update_channel_status(user_id, is_member)
            
            return is_member
            
        except TelegramBadRequest:
            # Пользователь не в канале
            await db.update_channel_status(user_id, False)
            return False
        except Exception as e:
            logger.error(f"Ошибка при проверке пользователя {user_id} в канале: {e}")
            return False
    
    async def cleanup_expired_subscriptions(self):
        """Очистка пользователей с истекшими подписками"""
        try:
            expired_users = await db.get_expired_subscriptions()
            
            for user in expired_users:
                await self.remove_user_from_channel(user.telegram_id)
                await asyncio.sleep(0.1)  # Небольшая задержка между запросами
            
            if expired_users:
                logger.info(f"Удалено {len(expired_users)} пользователей с истекшими подписками")
            
        except Exception as e:
            logger.error(f"Ошибка при очистке истекших подписок: {e}")
    
    async def get_channel_info(self) -> dict:
        """Получение информации о канале"""
        try:
            chat = await self.bot.get_chat(self.channel_id)
            member_count = await self.bot.get_chat_member_count(self.channel_id)
            
            return {
                'title': chat.title,
                'username': chat.username,
                'member_count': member_count,
                'description': chat.description
            }
        except Exception as e:
            logger.error(f"Ошибка при получении информации о канале: {e}")
            return {}

# Функция для периодической очистки истекших подписок
async def subscription_cleanup_task(bot: Bot):
    """Задача для периодической очистки истекших подписок"""
    channel_manager = ChannelManager(bot)
    
    while True:
        try:
            await channel_manager.cleanup_expired_subscriptions()
            # Проверяем каждые 30 минут
            await asyncio.sleep(1800)
        except Exception as e:
            logger.error(f"Ошибка в задаче очистки подписок: {e}")
            await asyncio.sleep(300)  # При ошибке ждем 5 минут