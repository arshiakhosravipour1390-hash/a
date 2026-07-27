# handlers/transfer_handler.py
import re
import sqlite3
from datetime import datetime, timedelta
from database import *
from utils import *
from config import *

class TransferHandler:
    def __init__(self):
        self.cooldowns = {}
        self.daily_transfers = {}  # {user_id: {"amount": 0, "date": "2026-07-25"}}
        self.client = None
    
    def set_client(self, client):
        self.client = client
    
    # ============================================================
    # سقف روزانه
    # ============================================================
    
    def _get_daily_usage(self, user_id):
        """دریافت مقدار انتقال داده شده امروز"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user_id not in self.daily_transfers:
            self.daily_transfers[user_id] = {"amount": 0, "date": today}
            return 0
        
        if self.daily_transfers[user_id]["date"] != today:
            self.daily_transfers[user_id] = {"amount": 0, "date": today}
            return 0
        
        return self.daily_transfers[user_id]["amount"]
    
    def _add_daily_usage(self, user_id, amount):
        """افزودن مبلغ به سقف روزانه"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if user_id not in self.daily_transfers or self.daily_transfers[user_id]["date"] != today:
            self.daily_transfers[user_id] = {"amount": 0, "date": today}
        
        self.daily_transfers[user_id]["amount"] += amount
    
    def _get_remaining_daily(self, user_id):
        """دریافت مقدار باقی‌مونده از سقف روزانه"""
        used = self._get_daily_usage(user_id)
        remaining = TRANSFER_DAILY_LIMIT - used
        return max(0, remaining)
    
    # ============================================================
    # هندلر اصلی
    # ============================================================
    
    async def handle(self, user_id, chat_id, text, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        level = safe_int(user[4], 1)
        
        if level < TRANSFER_MIN_LEVEL:
            await send_func(
                chat_id,
                f"❌ **نیاز به سطح {TRANSFER_MIN_LEVEL} داری!**\n"
                f"📊 سطح فعلی: {level}\n"
                f"🎯 سطح مورد نیاز: {TRANSFER_MIN_LEVEL}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if not self._check_cooldown(user_id):
            await send_func(
                chat_id,
                "⏳ باید ۳۰ ثانیه صبر کنی تا دوباره انتقال بدی!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        parts = text.split()
        if len(parts) < 3:
            await send_func(
                chat_id,
                "❌ **فرمت صحیح:**\n"
                "`انتقال میویی 1000` (با ریپلای روی کاربر)",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        amount_index = 1
        if parts[0] == "انتقال" and parts[1] == "میویی":
            amount_index = 2
        elif parts[0] == "انتقال":
            amount_index = 1
        
        amount = self._extract_amount(parts[amount_index])
        if not amount:
            await send_func(
                chat_id,
                "❌ مبلغ نامعتبر. مثال: `1000`, `5k`, `۱۰۰۰۰`",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        if amount < TRANSFER_MIN_AMOUNT:
            await send_func(
                chat_id,
                f"❌ **حداقل مبلغ انتقال {TRANSFER_MIN_AMOUNT} 🪙 است!**",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if amount > TRANSFER_MAX_AMOUNT:
            await send_func(
                chat_id,
                f"❌ **حداکثر مبلغ انتقال {format_number(TRANSFER_MAX_AMOUNT)} 🪙 است!**",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        # ====== بررسی سقف روزانه ======
        remaining_daily = self._get_remaining_daily(user_id)
        if remaining_daily < amount:
            await send_func(
                chat_id,
                f"❌ **سقف روزانه انتقال پر شده!**\n\n"
                f"💰 سقف روزانه: {format_number(TRANSFER_DAILY_LIMIT)} 🪙\n"
                f"💰 باقی‌مونده امروز: {format_number(remaining_daily)} 🪙\n"
                f"📌 فردا دوباره می‌تونی انتقال بدی.\n\n"
                f"💡 یا مبلغ رو کمتر کن (حداکثر {format_number(remaining_daily)} 🪙)",
                reply_to=message.id,
                auto_delete=True,
                delete_after=15
            )
            return
        
        if user[6] < amount:
            await send_func(
                chat_id,
                f"❌ **پوینت کافی نیست!**\n"
                f"💰 موجودی: {format_number(user[6])} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        # ====== دریافت ریپلای ======
        target_id = None
        
        if hasattr(message, 'reply_to_msg_id') and message.reply_to_msg_id:
            replied_msg_id = message.reply_to_msg_id
            
            if self.client:
                try:
                    replied_message = await self.client.get_messages(message.peer_id, ids=replied_msg_id)
                    if replied_message:
                        if isinstance(replied_message, list) and len(replied_message) > 0:
                            target_id = replied_message[0].sender_id
                        else:
                            target_id = replied_message.sender_id
                except Exception as e:
                    print(f"⚠️ خطا در دریافت پیام اصلی: {e}")
        
        if not target_id and hasattr(message, 'is_reply') and message.is_reply:
            if self.client:
                try:
                    history = await self.client.get_messages(message.peer_id, limit=2)
                    if history and len(history) >= 2:
                        replied_msg = history[1]
                        if replied_msg and replied_msg.sender_id != user_id:
                            target_id = replied_msg.sender_id
                except Exception as e:
                    print(f"⚠️ خطا در دریافت history: {e}")
        
        if not target_id:
            await send_func(
                chat_id,
                "❌ **روی پیام کاربر ریپلای کنید!**\n\n"
                "💡 روی پیام کاربر ریپلای کنید و سپس دستور را بفرستید.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if target_id == user_id:
            await send_func(
                chat_id,
                "❌ نمی‌تونی به خودت انتقال بدی!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        target_user = get_user(target_id)
        if not target_user:
            await send_func(
                chat_id,
                "❌ کاربر مورد نظر پیدا نشد!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        if safe_int(target_user[4]) < TRANSFER_RECEIVER_MIN_LEVEL:
            await send_func(
                chat_id,
                f"❌ **گیرنده باید حداقل سطح {TRANSFER_RECEIVER_MIN_LEVEL} داشته باشد!**\n"
                f"📊 سطح گیرنده: {target_user[4]}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        # ====== انجام انتقال ======
        update_user(user_id, points=int(user[6] - amount))
        update_user(target_id, points=int(target_user[6] + amount))
        
        # ====== ثبت در سقف روزانه ======
        self._add_daily_usage(user_id, amount)
        self._set_cooldown(user_id)
        
        sender_name = get_user_name(user)
        target_name = get_user_name(target_user)
        
        remaining_after = self._get_remaining_daily(user_id)
        
        await send_func(
            chat_id,
            f"✅ **انتقال انجام شد!**\n\n"
            f"💰 مبلغ: {format_number(amount)} 🪙\n"
            f"👤 گیرنده: {target_name}\n"
            f"📊 موجودی جدید شما: {format_number(user[6] - amount)} 🪙\n"
            f"📊 باقی‌مونده از سقف روزانه: {format_number(remaining_after)} 🪙",
            reply_to=message.id,
            auto_delete=True,
            delete_after=30
        )
        
        try:
            await send_func(
                target_id,
                f"💰 **انتقال پوینت دریافت شد!**\n\n"
                f"👤 از: {sender_name}\n"
                f"💰 مبلغ: {format_number(amount)} 🪙\n"
                f"📊 موجودی جدید: {format_number(target_user[6] + amount)} 🪙",
                auto_delete=True,
                delete_after=30
            )
        except:
            pass
    
    def _extract_amount(self, text):
        persian_to_english = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
        }
        
        for persian, english in persian_to_english.items():
            text = text.replace(persian, english)
        
        text = text.replace(',', '').replace(' ', '')
        
        match = re.search(r'(\d+)(k|m|کی|میل)?', text.lower())
        if not match:
            return None
        
        amount = int(match.group(1))
        suffix = match.group(2) or ''
        
        if suffix in ['k', 'کی']:
            amount *= 1000
        elif suffix in ['m', 'میل']:
            amount *= 1000000
        
        return amount
    
    def _check_cooldown(self, user_id):
        if user_id not in self.cooldowns:
            return True
        return (datetime.now() - self.cooldowns[user_id]).seconds >= TRANSFER_COOLDOWN
    
    def _set_cooldown(self, user_id):
        self.cooldowns[user_id] = datetime.now()