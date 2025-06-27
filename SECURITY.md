# 🔒 Руководство по безопасности Telegram бота

Этот документ содержит рекомендации по обеспечению безопасности вашего Telegram бота с платежами звездами.

## 📋 Содержание

- [Основы безопасности](#основы-безопасности)
- [Защита токенов и ключей](#защита-токенов-и-ключей)
- [Безопасность базы данных](#безопасность-базы-данных)
- [Защита от атак](#защита-от-атак)
- [Мониторинг безопасности](#мониторинг-безопасности)
- [Резервное копирование](#резервное-копирование)
- [Аудит безопасности](#аудит-безопасности)
- [Инцидент-менеджмент](#инцидент-менеджмент)

## 🛡️ Основы безопасности

### Принципы безопасности

1. **Минимальные привилегии** - предоставляйте только необходимые права
2. **Глубокая защита** - используйте несколько уровней защиты
3. **Регулярные обновления** - поддерживайте систему в актуальном состоянии
4. **Мониторинг** - отслеживайте подозрительную активность
5. **Резервное копирование** - регулярно создавайте бэкапы

### Базовые настройки безопасности

```python
# config.py - Безопасные настройки
SECURITY_SETTINGS = {
    'MAX_REQUESTS_PER_MINUTE': 60,
    'MAX_PAYMENT_ATTEMPTS': 3,
    'SESSION_TIMEOUT': 3600,  # 1 час
    'ADMIN_SESSION_TIMEOUT': 1800,  # 30 минут
    'ENABLE_RATE_LIMITING': True,
    'LOG_SENSITIVE_DATA': False,
    'REQUIRE_ADMIN_2FA': True
}
```

## 🔑 Защита токенов и ключей

### Управление секретами

#### 1. Файл .env

**✅ Правильно:**
```env
# .env - НЕ добавляйте в git!
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789,987654321
DATABASE_ENCRYPTION_KEY=your-32-char-encryption-key-here
```

**❌ Неправильно:**
```python
# bot.py - НИКОГДА не делайте так!
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"  # Хардкод токена
```

#### 2. Проверка .gitignore

```gitignore
# Обязательно добавьте в .gitignore
.env
*.log
bot.db
backups/
__pycache__/
*.pyc
.venv/
venv/
```

#### 3. Ротация токенов

```bash
# Скрипт для ротации токенов
#!/bin/bash

echo "🔄 Ротация токенов бота"
echo "1. Создайте новый токен в @BotFather"
echo "2. Обновите BOT_TOKEN в .env"
echo "3. Перезапустите бота"
echo "4. Отзовите старый токен в @BotFather"
```

### Шифрование данных

```python
# utils.py - Функции шифрования
import os
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self):
        key = os.getenv('DATABASE_ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            print(f"Generated new encryption key: {key.decode()}")
        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)
    
    def encrypt(self, data: str) -> str:
        """Шифрование строки"""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Расшифровка строки"""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Использование
encryption = DataEncryption()
sensitive_data = encryption.encrypt("sensitive information")
```

## 🗄️ Безопасность базы данных

### Защита SQLite

```python
# database.py - Безопасные запросы
class SecureDatabase:
    async def safe_query(self, query: str, params: tuple = ()):
        """Безопасное выполнение запросов с параметрами"""
        async with aiosqlite.connect(self.db_path) as db:
            # Всегда используйте параметризованные запросы
            cursor = await db.execute(query, params)
            return await cursor.fetchall()
    
    async def get_user_safe(self, user_id: int):
        """Безопасное получение пользователя"""
        # ✅ Правильно - параметризованный запрос
        query = "SELECT * FROM users WHERE telegram_id = ?"
        return await self.safe_query(query, (user_id,))
    
    async def get_user_unsafe(self, user_id: int):
        """❌ НЕБЕЗОПАСНО - уязвимо к SQL-инъекциям"""
        query = f"SELECT * FROM users WHERE telegram_id = {user_id}"
        # НЕ ИСПОЛЬЗУЙТЕ такие запросы!
```

### Права доступа к файлам

```bash
# Установка правильных прав доступа
chmod 600 .env          # Только владелец может читать/писать
chmod 600 bot.db        # Только владелец может читать/писать
chmod 700 backups/      # Только владелец может входить в папку
chmod 644 *.py          # Все могут читать, владелец может писать
```

### Резервное копирование с шифрованием

```bash
#!/bin/bash
# secure_backup.sh

BACKUP_DIR="/secure/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PASSWORD="your-backup-password"

# Создание зашифрованного архива
tar -czf - bot.db .env | gpg --symmetric --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 --s2k-digest-algo SHA512 --s2k-count 65536 --force-mdc --passphrase "$PASSWORD" > "$BACKUP_DIR/backup_$DATE.tar.gz.gpg"

echo "Encrypted backup created: backup_$DATE.tar.gz.gpg"
```

## 🛡️ Защита от атак

### Rate Limiting (Ограничение частоты запросов)

```python
# rate_limiter.py
import time
from collections import defaultdict, deque
from typing import Dict, Deque

class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[int, Deque[float]] = defaultdict(deque)
    
    def is_allowed(self, user_id: int) -> bool:
        """Проверка, разрешен ли запрос от пользователя"""
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Удаляем старые запросы
        while user_requests and user_requests[0] < now - self.window_seconds:
            user_requests.popleft()
        
        # Проверяем лимит
        if len(user_requests) >= self.max_requests:
            return False
        
        # Добавляем текущий запрос
        user_requests.append(now)
        return True
    
    def get_remaining_requests(self, user_id: int) -> int:
        """Получить количество оставшихся запросов"""
        return max(0, self.max_requests - len(self.requests[user_id]))

# Использование в боте
rate_limiter = RateLimiter(max_requests=30, window_seconds=60)

@dp.message()
async def handle_message(message: types.Message):
    if not rate_limiter.is_allowed(message.from_user.id):
        await message.answer("⚠️ Слишком много запросов. Попробуйте позже.")
        return
    
    # Обработка сообщения
    await process_message(message)
```

### Валидация входных данных

```python
# validators.py
import re
from typing import Optional

class InputValidator:
    @staticmethod
    def validate_telegram_id(user_id: int) -> bool:
        """Валидация Telegram ID"""
        return isinstance(user_id, int) and 1 <= user_id <= 2**63 - 1
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """Валидация username"""
        if not username:
            return True  # Username может быть пустым
        pattern = r'^[a-zA-Z0-9_]{5,32}$'
        return bool(re.match(pattern, username))
    
    @staticmethod
    def validate_amount(amount: int) -> bool:
        """Валидация суммы платежа"""
        return isinstance(amount, int) and 1 <= amount <= 2500  # Лимиты Telegram Stars
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """Очистка текста от опасных символов"""
        if not text:
            return ""
        
        # Удаляем опасные символы
        text = re.sub(r'[<>"\'\/]', '', text)
        
        # Ограничиваем длину
        return text[:max_length]
    
    @staticmethod
    def validate_product_id(product_id: str) -> bool:
        """Валидация ID товара"""
        pattern = r'^[a-zA-Z0-9_]{1,50}$'
        return bool(re.match(pattern, product_id))

# Использование
validator = InputValidator()

async def process_payment(user_id: int, product_id: str, amount: int):
    if not validator.validate_telegram_id(user_id):
        raise ValueError("Invalid user ID")
    
    if not validator.validate_product_id(product_id):
        raise ValueError("Invalid product ID")
    
    if not validator.validate_amount(amount):
        raise ValueError("Invalid amount")
    
    # Обработка платежа
```

### Защита от спама

```python
# anti_spam.py
from datetime import datetime, timedelta
from typing import Dict, Set

class AntiSpam:
    def __init__(self):
        self.user_messages: Dict[int, list] = {}
        self.blocked_users: Set[int] = set()
        self.spam_threshold = 10  # сообщений
        self.time_window = 60  # секунд
        self.block_duration = 300  # 5 минут
    
    def is_spam(self, user_id: int) -> bool:
        """Проверка на спам"""
        now = datetime.now()
        
        # Проверяем, заблокирован ли пользователь
        if user_id in self.blocked_users:
            return True
        
        # Инициализируем список сообщений пользователя
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        
        # Удаляем старые сообщения
        cutoff_time = now - timedelta(seconds=self.time_window)
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if msg_time > cutoff_time
        ]
        
        # Добавляем текущее сообщение
        self.user_messages[user_id].append(now)
        
        # Проверяем превышение лимита
        if len(self.user_messages[user_id]) > self.spam_threshold:
            self.blocked_users.add(user_id)
            # Планируем разблокировку
            # В реальном приложении используйте планировщик задач
            return True
        
        return False
    
    def unblock_user(self, user_id: int):
        """Разблокировка пользователя"""
        self.blocked_users.discard(user_id)
        if user_id in self.user_messages:
            del self.user_messages[user_id]

# Использование
anti_spam = AntiSpam()

@dp.message()
async def handle_message(message: types.Message):
    if anti_spam.is_spam(message.from_user.id):
        await message.answer("🚫 Вы заблокированы за спам. Попробуйте позже.")
        return
    
    # Обработка сообщения
```

## 📊 Мониторинг безопасности

### Логирование событий безопасности

```python
# security_logger.py
import logging
from datetime import datetime
from typing import Optional

class SecurityLogger:
    def __init__(self):
        self.logger = logging.getLogger('security')
        handler = logging.FileHandler('security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_login_attempt(self, user_id: int, success: bool, ip: Optional[str] = None):
        """Логирование попыток входа"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"LOGIN_{status}: User {user_id} from {ip or 'unknown'}")
    
    def log_payment_attempt(self, user_id: int, amount: int, success: bool):
        """Логирование попыток платежа"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"PAYMENT_{status}: User {user_id}, Amount {amount}")
    
    def log_admin_action(self, admin_id: int, action: str, target: Optional[str] = None):
        """Логирование действий администратора"""
        self.logger.warning(f"ADMIN_ACTION: Admin {admin_id} performed {action} on {target or 'system'}")
    
    def log_security_incident(self, incident_type: str, user_id: int, details: str):
        """Логирование инцидентов безопасности"""
        self.logger.error(f"SECURITY_INCIDENT: {incident_type} - User {user_id} - {details}")
    
    def log_suspicious_activity(self, user_id: int, activity: str):
        """Логирование подозрительной активности"""
        self.logger.warning(f"SUSPICIOUS_ACTIVITY: User {user_id} - {activity}")

# Использование
security_logger = SecurityLogger()

async def process_payment(user_id: int, amount: int):
    try:
        # Обработка платежа
        result = await handle_payment(user_id, amount)
        security_logger.log_payment_attempt(user_id, amount, True)
        return result
    except Exception as e:
        security_logger.log_payment_attempt(user_id, amount, False)
        security_logger.log_security_incident(
            "PAYMENT_ERROR", user_id, str(e)
        )
        raise
```

### Мониторинг системных ресурсов

```python
# system_monitor.py
import psutil
import asyncio
from datetime import datetime

class SystemMonitor:
    def __init__(self):
        self.alerts_sent = set()
    
    async def check_system_health(self):
        """Проверка состояния системы"""
        # Проверка использования CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        if cpu_percent > 80:
            await self.send_alert(f"High CPU usage: {cpu_percent}%")
        
        # Проверка использования памяти
        memory = psutil.virtual_memory()
        if memory.percent > 85:
            await self.send_alert(f"High memory usage: {memory.percent}%")
        
        # Проверка свободного места на диске
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            await self.send_alert(f"Low disk space: {disk.percent}% used")
    
    async def send_alert(self, message: str):
        """Отправка уведомления администраторам"""
        alert_key = f"{message}_{datetime.now().hour}"
        if alert_key not in self.alerts_sent:
            # Отправка уведомления администраторам
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, f"🚨 System Alert: {message}")
                except:
                    pass
            self.alerts_sent.add(alert_key)
    
    async def start_monitoring(self):
        """Запуск мониторинга"""
        while True:
            try:
                await self.check_system_health()
                await asyncio.sleep(300)  # Проверка каждые 5 минут
            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(60)

# Запуск мониторинга
monitor = SystemMonitor()
asyncio.create_task(monitor.start_monitoring())
```

## 💾 Безопасное резервное копирование

### Автоматизированные бэкапы

```python
# backup_manager.py
import os
import shutil
import asyncio
from datetime import datetime, timedelta
from cryptography.fernet import Fernet

class SecureBackupManager:
    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = backup_dir
        self.encryption_key = os.getenv('BACKUP_ENCRYPTION_KEY')
        if not self.encryption_key:
            self.encryption_key = Fernet.generate_key()
            print(f"Generated backup encryption key: {self.encryption_key.decode()}")
        
        self.cipher = Fernet(self.encryption_key)
        os.makedirs(backup_dir, exist_ok=True)
    
    async def create_backup(self):
        """Создание зашифрованного бэкапа"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        
        try:
            # Создание временной папки
            temp_dir = f"temp_{backup_name}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Копирование файлов
            shutil.copy2("bot.db", f"{temp_dir}/bot.db")
            shutil.copy2(".env", f"{temp_dir}/.env")
            
            # Создание архива
            archive_path = f"{self.backup_dir}/{backup_name}.tar.gz"
            shutil.make_archive(archive_path[:-7], 'gztar', temp_dir)
            
            # Шифрование архива
            with open(archive_path, 'rb') as f:
                encrypted_data = self.cipher.encrypt(f.read())
            
            encrypted_path = f"{archive_path}.enc"
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Удаление временных файлов
            os.remove(archive_path)
            shutil.rmtree(temp_dir)
            
            print(f"✅ Backup created: {encrypted_path}")
            return encrypted_path
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    
    async def restore_backup(self, backup_path: str):
        """Восстановление из зашифрованного бэкапа"""
        try:
            # Расшифровка
            with open(backup_path, 'rb') as f:
                decrypted_data = self.cipher.decrypt(f.read())
            
            # Создание временного архива
            temp_archive = "temp_restore.tar.gz"
            with open(temp_archive, 'wb') as f:
                f.write(decrypted_data)
            
            # Извлечение архива
            shutil.unpack_archive(temp_archive, "restored")
            
            # Восстановление файлов
            if os.path.exists("restored/bot.db"):
                shutil.copy2("restored/bot.db", "bot.db")
            if os.path.exists("restored/.env"):
                shutil.copy2("restored/.env", ".env")
            
            # Очистка
            os.remove(temp_archive)
            shutil.rmtree("restored")
            
            print("✅ Backup restored successfully")
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            return False
    
    async def cleanup_old_backups(self, days_to_keep: int = 30):
        """Удаление старых бэкапов"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        for filename in os.listdir(self.backup_dir):
            if filename.startswith("backup_") and filename.endswith(".tar.gz.enc"):
                file_path = os.path.join(self.backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                
                if file_time < cutoff_date:
                    os.remove(file_path)
                    print(f"🗑️ Removed old backup: {filename}")
    
    async def start_scheduled_backups(self, interval_hours: int = 24):
        """Запуск автоматических бэкапов"""
        while True:
            await self.create_backup()
            await self.cleanup_old_backups()
            await asyncio.sleep(interval_hours * 3600)

# Использование
backup_manager = SecureBackupManager()
asyncio.create_task(backup_manager.start_scheduled_backups(interval_hours=12))
```

## 🔍 Аудит безопасности

### Чек-лист безопасности

```python
# security_audit.py
import os
import stat
import sqlite3
from pathlib import Path

class SecurityAudit:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.passed = []
    
    def check_file_permissions(self):
        """Проверка прав доступа к файлам"""
        sensitive_files = ['.env', 'bot.db']
        
        for filename in sensitive_files:
            if os.path.exists(filename):
                file_stat = os.stat(filename)
                permissions = stat.filemode(file_stat.st_mode)
                
                if permissions != '-rw-------':
                    self.issues.append(f"File {filename} has insecure permissions: {permissions}")
                else:
                    self.passed.append(f"File {filename} has secure permissions")
            else:
                self.warnings.append(f"File {filename} not found")
    
    def check_environment_variables(self):
        """Проверка переменных окружения"""
        required_vars = ['BOT_TOKEN', 'ADMIN_IDS']
        
        for var in required_vars:
            if not os.getenv(var):
                self.issues.append(f"Missing required environment variable: {var}")
            else:
                self.passed.append(f"Environment variable {var} is set")
        
        # Проверка сложности токена
        bot_token = os.getenv('BOT_TOKEN', '')
        if len(bot_token) < 40:
            self.issues.append("BOT_TOKEN appears to be invalid or too short")
    
    def check_database_security(self):
        """Проверка безопасности базы данных"""
        if not os.path.exists('bot.db'):
            self.warnings.append("Database file not found")
            return
        
        try:
            conn = sqlite3.connect('bot.db')
            cursor = conn.cursor()
            
            # Проверка наличия индексов
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = cursor.fetchall()
            
            if len(indexes) < 3:
                self.warnings.append("Database may lack proper indexing")
            else:
                self.passed.append("Database has proper indexing")
            
            conn.close()
            
        except Exception as e:
            self.issues.append(f"Database check failed: {e}")
    
    def check_code_security(self):
        """Проверка безопасности кода"""
        python_files = list(Path('.').glob('*.py'))
        
        for file_path in python_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Поиск потенциальных проблем
                if 'eval(' in content:
                    self.issues.append(f"Dangerous eval() found in {file_path}")
                
                if 'exec(' in content:
                    self.issues.append(f"Dangerous exec() found in {file_path}")
                
                if 'shell=True' in content:
                    self.warnings.append(f"shell=True found in {file_path} - review for security")
                
                if 'password' in content.lower() and '=' in content:
                    self.warnings.append(f"Possible hardcoded password in {file_path}")
    
    def check_dependencies(self):
        """Проверка зависимостей"""
        if os.path.exists('requirements.txt'):
            with open('requirements.txt', 'r') as f:
                deps = f.read()
                
                # Проверка на устаревшие версии
                if 'aiogram==' not in deps:
                    self.warnings.append("Aiogram version not pinned in requirements.txt")
                
                self.passed.append("Requirements.txt exists")
        else:
            self.issues.append("requirements.txt not found")
    
    def run_audit(self):
        """Запуск полного аудита"""
        print("🔍 Starting security audit...\n")
        
        self.check_file_permissions()
        self.check_environment_variables()
        self.check_database_security()
        self.check_code_security()
        self.check_dependencies()
        
        # Вывод результатов
        if self.issues:
            print("❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"   • {issue}")
            print()
        
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")
            print()
        
        if self.passed:
            print("✅ PASSED CHECKS:")
            for check in self.passed:
                print(f"   • {check}")
            print()
        
        # Общая оценка
        total_checks = len(self.issues) + len(self.warnings) + len(self.passed)
        score = (len(self.passed) / total_checks) * 100 if total_checks > 0 else 0
        
        print(f"📊 Security Score: {score:.1f}%")
        
        if self.issues:
            print("\n🚨 Please fix critical issues before deploying!")
        elif self.warnings:
            print("\n⚠️  Consider addressing warnings for better security.")
        else:
            print("\n🎉 All security checks passed!")

if __name__ == "__main__":
    audit = SecurityAudit()
    audit.run_audit()
```

## 🚨 Инцидент-менеджмент

### План реагирования на инциденты

```python
# incident_response.py
import asyncio
from datetime import datetime
from enum import Enum

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentManager:
    def __init__(self):
        self.active_incidents = {}
        self.incident_counter = 0
    
    async def report_incident(self, incident_type: str, severity: IncidentSeverity, 
                            description: str, affected_users: list = None):
        """Регистрация инцидента"""
        self.incident_counter += 1
        incident_id = f"INC-{self.incident_counter:04d}"
        
        incident = {
            'id': incident_id,
            'type': incident_type,
            'severity': severity,
            'description': description,
            'affected_users': affected_users or [],
            'created_at': datetime.now(),
            'status': 'open',
            'actions_taken': []
        }
        
        self.active_incidents[incident_id] = incident
        
        # Автоматические действия в зависимости от серьезности
        await self._handle_incident_severity(incident)
        
        return incident_id
    
    async def _handle_incident_severity(self, incident):
        """Обработка инцидента в зависимости от серьезности"""
        if incident['severity'] == IncidentSeverity.CRITICAL:
            # Критический инцидент - немедленные действия
            await self._notify_all_admins(incident)
            await self._enable_maintenance_mode()
            
        elif incident['severity'] == IncidentSeverity.HIGH:
            # Высокий приоритет - уведомление администраторов
            await self._notify_all_admins(incident)
            
        elif incident['severity'] == IncidentSeverity.MEDIUM:
            # Средний приоритет - логирование и уведомление
            await self._log_incident(incident)
            await self._notify_primary_admin(incident)
    
    async def _notify_all_admins(self, incident):
        """Уведомление всех администраторов"""
        message = f"🚨 INCIDENT {incident['id']}\n"
        message += f"Severity: {incident['severity'].value.upper()}\n"
        message += f"Type: {incident['type']}\n"
        message += f"Description: {incident['description']}\n"
        message += f"Time: {incident['created_at']}\n"
        
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(admin_id, message)
            except:
                pass
    
    async def _enable_maintenance_mode(self):
        """Включение режима обслуживания"""
        # Здесь можно добавить логику для отключения бота
        # или ограничения функциональности
        pass
    
    async def close_incident(self, incident_id: str, resolution: str):
        """Закрытие инцидента"""
        if incident_id in self.active_incidents:
            self.active_incidents[incident_id]['status'] = 'closed'
            self.active_incidents[incident_id]['resolution'] = resolution
            self.active_incidents[incident_id]['closed_at'] = datetime.now()
            
            # Уведомление о закрытии
            message = f"✅ INCIDENT {incident_id} RESOLVED\n"
            message += f"Resolution: {resolution}"
            
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, message)
                except:
                    pass

# Использование
incident_manager = IncidentManager()

# Пример регистрации инцидента
async def handle_payment_failure(user_id: int, error: str):
    await incident_manager.report_incident(
        incident_type="payment_failure",
        severity=IncidentSeverity.HIGH,
        description=f"Payment failed for user {user_id}: {error}",
        affected_users=[user_id]
    )
```

## 📚 Дополнительные ресурсы

### Полезные ссылки

- [OWASP Top 10](https://owasp.org/www-project-top-ten/) - Топ уязвимостей веб-приложений
- [Telegram Bot Security](https://core.telegram.org/bots/faq#security) - Официальная документация по безопасности ботов
- [Python Security](https://python-security.readthedocs.io/) - Руководство по безопасности Python
- [SQLite Security](https://www.sqlite.org/security.html) - Безопасность SQLite

### Инструменты для аудита

```bash
# Установка инструментов безопасности
pip install bandit safety

# Проверка кода на уязвимости
bandit -r .

# Проверка зависимостей
safety check

# Проверка requirements.txt
safety check -r requirements.txt
```

### Регулярные задачи безопасности

**Ежедневно:**
- Проверка логов безопасности
- Мониторинг системных ресурсов
- Проверка резервных копий

**Еженедельно:**
- Обновление зависимостей
- Проверка новых уязвимостей
- Анализ трафика и активности

**Ежемесячно:**
- Полный аудит безопасности
- Ротация ключей и токенов
- Тестирование восстановления из бэкапов
- Обновление документации

**Ежеквартально:**
- Пентестирование
- Обзор политик безопасности
- Обучение команды

Следуя этим рекомендациям, вы обеспечите высокий уровень безопасности вашего Telegram бота с платежами звездами. Помните: безопасность - это непрерывный процесс, требующий постоянного внимания и обновления.