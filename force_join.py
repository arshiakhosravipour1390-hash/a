# force_join.py
import time
import asyncio
from typing import Set, Optional
from splusthon import SoroushClient
from splusthon.tl import functions, types
from config import FORCE_CHANNEL_USERNAME, FORCE_CHANNEL_NAME, MEMBER_CACHE_TTL


class ForceJoinManager:
    """
    مدیریت اجباری عضویت در کانال (غیرفعال)
    """
    
    def __init__(self, client: SoroushClient):
        self.client = client
        self.channel = None
        self.channel_name = FORCE_CHANNEL_NAME
        self.channel_username = FORCE_CHANNEL_USERNAME
        self.members: Set[int] = set()
        self.cache_timestamp = 0
        self.cache_ttl = MEMBER_CACHE_TTL
        self.is_initialized = False
        self.join_message = ""
        self.cache_task: Optional[asyncio.Task] = None
        self._stop_cache = False
        self._lock = asyncio.Lock()
        self._enabled = False  # ✅ غیرفعال
    
    async def start(self):
        """راه‌اندازی مدیر Force Join (غیرفعال)"""
        print("🚀 در حال راه‌اندازی Force Join Manager...")
        print("   ⚠️ سیستم Force Join غیرفعال است!")
        self.is_initialized = True
        print("✅ Force Join Manager راه‌اندازی شد (غیرفعال)!")
    
    def _build_join_message(self) -> str:
        """ساخت پیام عضویت (استفاده نمیشه)"""
        return ""
    
    async def _cache_worker(self):
        """تسک پس‌زمینه (غیرفعال)"""
        pass
    
    async def stop(self):
        """متوقف کردن تسک پس‌زمینه"""
        self._stop_cache = True
        print("✅ Force Join Manager متوقف شد!")
    
    async def _fetch_members(self) -> Optional[Set[int]]:
        """دریافت اعضا (استفاده نمیشه)"""
        return set()
    
    async def _update_cache(self):
        """به‌روزرسانی کش (استفاده نمیشه)"""
        pass
    
    async def refresh(self):
        """اجبار به‌روزرسانی (استفاده نمیشه)"""
        pass
    
    async def check_single_user(self, user_id: int) -> bool:
        """بررسی عضویت (همیشه True برمیگردونه)"""
        return True
    
    def _is_cache_expired(self) -> bool:
        """بررسی انقضای کش (استفاده نمیشه)"""
        return False
    
    def is_member(self, user_id: int) -> bool:
        """بررسی عضویت کاربر (همیشه True)"""
        if not self._enabled:
            return True
        return user_id in self.members
    
    def get_member_count(self) -> int:
        """تعداد اعضا (همیشه 0)"""
        return 0
    
    def get_join_message(self) -> str:
        """دریافت پیام عضویت (خالی)"""
        return ""
    
    def get_missing_message(self, user_id: int) -> str:
        """ساخت پیام عدم عضویت (استفاده نمیشه)"""
        return ""
    
    async def send_join_message(self, chat_id, message, send_func):
        """ارسال پیام عضویت (غیرفعال)"""
        pass
    
    async def send_missing_message(self, user_id, chat_id, message, send_func):
        """ارسال پیام عدم عضویت (غیرفعال)"""
        pass
