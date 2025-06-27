import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Базовый класс для моделей
Base = declarative_base()

# Модель пользователя
class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime)
    subscription_until = Column(DateTime)  # Дата окончания подписки на канал
    is_in_channel = Column(Boolean, default=False)  # Находится ли пользователь в канале
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"
    
    @property
    def is_premium_active(self):
        """Проверка активности премиум статуса"""
        if not self.is_premium or not self.premium_until:
            return False
        return datetime.utcnow() < self.premium_until
    
    @property
    def is_subscription_active(self):
        """Проверка активности подписки на канал"""
        if not self.subscription_until:
            return False
        return datetime.utcnow() < self.subscription_until

# Модель покупки
class Purchase(Base):
    __tablename__ = 'purchases'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)  # telegram_id пользователя
    product_id = Column(String(100), nullable=False)
    product_title = Column(String(255), nullable=False)
    amount = Column(Integer, nullable=False)  # количество звезд
    telegram_payment_charge_id = Column(String(255), unique=True)
    provider_payment_charge_id = Column(String(255))
    status = Column(String(50), default='completed')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Purchase(user_id={self.user_id}, product_id={self.product_id}, amount={self.amount})>"

# Класс для работы с базой данных
class Database:
    def __init__(self, database_url: str):
        # Преобразование URL для async SQLAlchemy
        if database_url.startswith('sqlite:///'):
            self.database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
        else:
            self.database_url = database_url
        
        self.engine = create_async_engine(self.database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
    
    async def create_tables(self):
        """Создание таблиц в базе данных"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Таблицы базы данных созданы")
    
    async def get_user(self, telegram_id: int) -> User:
        """Получение пользователя по telegram_id"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_id(self, telegram_id: int) -> User:
        """Получение пользователя по telegram_id (алиас для get_user)"""
        return await self.get_user(telegram_id)
    
    async def get_user_by_username(self, username: str) -> User:
        """Получение пользователя по username"""
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
    
    async def get_all_users(self) -> list[User]:
        """Получение всех пользователей"""
        async with self.async_session() as session:
            result = await session.execute(select(User))
            return result.scalars().all()
    
    async def get_user_subscriptions(self, telegram_id: int) -> list:
        """Получение подписок пользователя"""
        # Возвращаем информацию о подписке на основе данных пользователя
        user = await self.get_user(telegram_id)
        if not user:
            return []
        
        subscriptions = []
        if user.is_subscription_active:
            # Создаем объект подписки на основе данных пользователя
            class Subscription:
                def __init__(self, title, is_active):
                    self.product_title = title
                    self.is_active = is_active
            
            subscriptions.append(Subscription("Подписка на канал", True))
        
        return subscriptions
    
    async def create_or_update_user(self, telegram_id: int, username: str = None, 
                                  first_name: str = None, last_name: str = None) -> User:
        """Создание или обновление пользователя"""
        async with self.async_session() as session:
            # Попытка найти существующего пользователя по telegram_id
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                # Обновление существующего пользователя
                user.username = username
                user.first_name = first_name
                user.last_name = last_name
                user.updated_at = datetime.utcnow()
            else:
                # Создание нового пользователя
                user = User(
                    telegram_id=telegram_id,
                    username=username,
                    first_name=first_name,
                    last_name=last_name
                )
                session.add(user)
            
            await session.commit()
            await session.refresh(user)
            return user
    
    async def activate_premium(self, telegram_id: int, days: int = 30):
        """Активация премиум статуса для пользователя"""
        async with self.async_session() as session:
            user = await session.get(User, telegram_id)
            if user:
                user.is_premium = True
                user.premium_until = datetime.utcnow() + timedelta(days=days)
                user.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"Премиум активирован для пользователя {telegram_id} на {days} дней")
    
    async def activate_subscription(self, telegram_id: int, days: int = 30):
        """Активация подписки на канал для пользователя"""
        async with self.async_session() as session:
            user = await session.get(User, telegram_id)
            if user:
                # Если у пользователя уже есть активная подписка, продлеваем её
                if user.is_subscription_active:
                    user.subscription_until = user.subscription_until + timedelta(days=days)
                else:
                    user.subscription_until = datetime.utcnow() + timedelta(days=days)
                user.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"Подписка активирована для пользователя {telegram_id} на {days} дней")
    
    async def update_channel_status(self, telegram_id: int, is_in_channel: bool):
        """Обновление статуса нахождения пользователя в канале"""
        from sqlalchemy import select
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            user = result.scalar_one_or_none()
            if user:
                user.is_in_channel = is_in_channel
                user.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"Статус канала обновлен для пользователя {telegram_id}: {is_in_channel}")
            else:
                logger.warning(f"Пользователь с telegram_id {telegram_id} не найден")
    
    async def get_expired_subscriptions(self) -> list[User]:
        """Получение пользователей с истекшей подпиской"""
        from sqlalchemy import select
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(
                    User.subscription_until < datetime.utcnow(),
                    User.is_in_channel == True
                )
            )
            return result.scalars().all()
    
    async def get_active_subscribers(self) -> list[User]:
        """Получение пользователей с активной подпиской"""
        from sqlalchemy import select
        async with self.async_session() as session:
            result = await session.execute(
                select(User).where(
                    User.subscription_until > datetime.utcnow()
                )
            )
            return result.scalars().all()
    
    async def create_purchase(self, user_id: int, product_id: str, product_title: str,
                            amount: int, telegram_payment_charge_id: str,
                            provider_payment_charge_id: str = None) -> Purchase:
        """Создание записи о покупке"""
        async with self.async_session() as session:
            purchase = Purchase(
                user_id=user_id,
                product_id=product_id,
                product_title=product_title,
                amount=amount,
                telegram_payment_charge_id=telegram_payment_charge_id,
                provider_payment_charge_id=provider_payment_charge_id
            )
            session.add(purchase)
            await session.commit()
            await session.refresh(purchase)
            logger.info(f"Создана запись о покупке: {purchase}")
            return purchase
    
    async def get_user_purchases(self, telegram_id: int) -> list[Purchase]:
        """Получение всех покупок пользователя"""
        from sqlalchemy import select
        async with self.async_session() as session:
            result = await session.execute(
                select(Purchase).where(Purchase.user_id == telegram_id)
            )
            return result.scalars().all()
    
    async def get_total_users_count(self) -> int:
        """Получение общего количества пользователей"""
        from sqlalchemy import select, func
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(User.telegram_id))
            )
            return result.scalar() or 0
    
    async def get_premium_users_count(self) -> int:
        """Получение количества премиум пользователей"""
        from sqlalchemy import select, func
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(User.telegram_id)).where(
                    User.is_premium == True,
                    User.premium_until > datetime.utcnow()
                )
            )
            return result.scalar() or 0
    
    async def get_total_purchases_count(self) -> int:
        """Получение общего количества покупок"""
        from sqlalchemy import select, func
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(Purchase.id))
            )
            return result.scalar() or 0
    
    async def get_total_revenue(self) -> int:
        """Получение общего дохода в звездах"""
        from sqlalchemy import select, func
        async with self.async_session() as session:
            result = await session.execute(
                select(func.sum(Purchase.amount))
            )
            return result.scalar() or 0
    
    async def get_recent_users(self, limit: int = 10) -> list[User]:
        """Получение последних зарегистрированных пользователей"""
        from sqlalchemy import select
        async with self.async_session() as session:
            result = await session.execute(
                select(User).order_by(User.created_at.desc()).limit(limit)
            )
            return result.scalars().all()
    
    async def get_recent_purchases(self, limit: int = 10) -> list[Purchase]:
        """Получение последних покупок"""
        from sqlalchemy import select
        async with self.async_session() as session:
            result = await session.execute(
                select(Purchase).order_by(Purchase.created_at.desc()).limit(limit)
            )
            return result.scalars().all()
    
    async def get_all_user_ids(self) -> list[int]:
        """Получение всех ID пользователей для рассылки"""
        from sqlalchemy import select
        async with self.async_session() as session:
            result = await session.execute(
                select(User.telegram_id)
            )
            return [row[0] for row in result.fetchall()]
    
    async def get_all_users(self) -> list[User]:
        """Получение всех пользователей"""
        from sqlalchemy import select
        async with self.async_session() as session:
            result = await session.execute(
                select(User).order_by(User.created_at.desc())
            )
            return result.scalars().all()
    
    async def get_revenue_by_date(self, date) -> int:
        """Получение дохода за определенную дату"""
        from sqlalchemy import select, func, and_
        from datetime import datetime, timedelta
        
        # Преобразуем дату в datetime для начала и конца дня
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)
        
        async with self.async_session() as session:
            result = await session.execute(
                select(func.sum(Purchase.amount)).where(
                    and_(
                        Purchase.created_at >= start_of_day,
                        Purchase.created_at < end_of_day
                    )
                )
            )
            return result.scalar() or 0
    
    async def get_purchases_count_by_date(self, date) -> int:
        """Получение количества покупок за определенную дату"""
        from sqlalchemy import select, func, and_
        from datetime import datetime, timedelta
        
        # Преобразуем дату в datetime для начала и конца дня
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = start_of_day + timedelta(days=1)
        
        async with self.async_session() as session:
            result = await session.execute(
                select(func.count(Purchase.id)).where(
                    and_(
                        Purchase.created_at >= start_of_day,
                        Purchase.created_at < end_of_day
                    )
                )
            )
            return result.scalar() or 0
    
    async def close(self):
        """Закрытие соединения с базой данных"""
        await self.engine.dispose()

# Глобальный экземпляр базы данных
db = Database(DATABASE_URL)

async def init_database():
    """Инициализация базы данных"""
    await db.create_tables()
    logger.info("База данных инициализирована")

if __name__ == "__main__":
    # Тестирование базы данных
    async def test_db():
        await init_database()
        
        # Создание тестового пользователя
        user = await db.create_or_update_user(
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        print(f"Создан пользователь: {user}")
        
        # Активация премиума
        await db.activate_premium(123456789, 30)
        
        # Создание покупки
        purchase = await db.create_purchase(
            user_id=123456789,
            product_id="premium_access",
            product_title="Премиум доступ",
            amount=100,
            telegram_payment_charge_id="test_charge_id"
        )
        print(f"Создана покупка: {purchase}")
        
        await db.close()
    
    asyncio.run(test_db())