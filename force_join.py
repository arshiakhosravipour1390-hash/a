# force_join.py
import time
import asyncio
from typing import Set, Optional
from splusthon import SoroushClient
from splusthon.tl import functions, types
from config import FORCE_CHANNEL_USERNAME, FORCE_CHANNEL_NAME, MEMBER_CACHE_TTL


class ForceJoinManager:
    """
    مدیریت اجباری عضویت در کانال (برای یک کانال)
    بدون ارسال هیچ پیامی به کانال
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
    
    async def start(self):
        """راه‌اندازی مدیر Force Join"""
        print("🚀 در حال راه‌اندازی Force Join Manager...")
        
        try:
            self.channel = await self.client.get_entity(f"@{self.channel_username}")
            print(f"   ✅ کانال '{self.channel_name}' متصل شد!")
            print(f"   👥 تعداد اعضا: {self.channel.participants_count}")
        except Exception as e:
            print(f"   ❌ خطا در اتصال به کانال '{self.channel_name}': {e}")
            raise RuntimeError(f"خطا در اتصال به کانال اجباری: {e}")
        
        self.join_message = self._build_join_message()
        
        await self._update_cache()
        self.is_initialized = True
        
        self._stop_cache = False
        self.cache_task = asyncio.create_task(self._cache_worker())
        
        print("✅ Force Join Manager راه‌اندازی شد!")
        print(f"📊 {len(self.members)} عضو در کش ذخیره شد!")
    
    def _build_join_message(self) -> str:
        """ساخت پیام عضویت (فقط در گروه‌ها نمایش داده میشه)"""
        return (
            f"🐱 **سلام میویی عزیز!**\n\n"
            f"✨ برای اطلاع از آخرین اطلاعیه‌ها، ساعت خاموشی بات، آپدیت‌های جدید، آموزش‌ها و رویدادهای ویژه،\n"
            f"❄️ لطفاً در **{self.channel_name}** عضو شو:\n\n"
            f"📢 **راه عضویت:**\n"
            f"┘─ ۱️⃣ روی **پروفایل من** (ربات) کلیک کن\n"
            f"┘─ ۲️⃣ در بخش **بیوگرافی**، لینک کانال رو پیدا کن\n"
            f"┘─ ۳️⃣ روی لینک کلیک کن و عضو شو! 🎉\n\n"
            f"💛 بعد از عضویت، دستور **`عضو شدم`** رو بفرست تا تأیید بشه.\n"
            f"🌸 منتظرت هستیم! 🐱"
        )
    
    async def _cache_worker(self):
        """تسک پس‌زمینه برای به‌روزرسانی دوره‌ای کش"""
        print("🔄 تسک پس‌زمینه کش اعضا شروع شد!")
        while not self._stop_cache:
            try:
                await asyncio.sleep(self.cache_ttl)
                if not self._stop_cache:
                    await self._update_cache()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ خطا در تسک پس‌زمینه کش: {e}")
        print("🛑 تسک پس‌زمینه کش متوقف شد!")
    
    async def stop(self):
        """متوقف کردن تسک پس‌زمینه"""
        self._stop_cache = True
        if self.cache_task:
            self.cache_task.cancel()
            try:
                await self.cache_task
            except asyncio.CancelledError:
                pass
        print("✅ Force Join Manager متوقف شد!")
    
    async def _fetch_members(self) -> Optional[Set[int]]:
        """دریافت همه اعضای کانال با GetParticipantsRequest"""
        try:
            members = set()
            offset = 0
            limit = 200
            
            while True:
                result = await asyncio.wait_for(
                    self.client(
                        functions.channels.GetParticipantsRequest(
                            channel=self.channel,
                            filter=types.ChannelParticipantsRecent(),
                            offset=offset,
                            limit=limit,
                            hash=0
                        )
                    ),
                    timeout=30
                )
                
                for participant in result.participants:
                    if hasattr(participant, 'user_id'):
                        members.add(participant.user_id)
                    elif hasattr(participant, 'id'):
                        members.add(participant.id)
                
                if len(result.participants) < limit:
                    break
                
                offset += len(result.participants)
            
            return members
            
        except asyncio.TimeoutError:
            print(f"❌ Timeout در دریافت اعضای کانال '{self.channel_name}'")
            return None
        except Exception as e:
            print(f"❌ خطا در دریافت اعضای کانال '{self.channel_name}': {e}")
            return None
    
    async def _update_cache(self):
        """به‌روزرسانی کش (با Lock)"""
        async with self._lock:
            print(f"   🔄 در حال به‌روزرسانی کش کانال '{self.channel_name}'...")
            
            members = await self._fetch_members()
            
            if members is None:
                print(f"   ⚠️ خطا در دریافت اعضا، کش قبلی حفظ شد.")
                return False
            
            self.members = members
            self.cache_timestamp = time.time()
            print(f"   ✅ {len(members)} عضو کش شد!")
            return True
    
    async def refresh(self):
        """اجبار به‌روزرسانی کامل کش"""
        print(f"🔄 اجبار به‌روزرسانی کش کانال '{self.channel_name}'...")
        self.cache_timestamp = 0
        await self._update_cache()
    
    async def check_single_user(self, user_id: int) -> bool:
        """بررسی عضویت یک کاربر خاص (بدون دانلود همه اعضا)"""
        try:
            result = await asyncio.wait_for(
                self.client(
                    functions.channels.GetParticipantsRequest(
                        channel=self.channel,
                        filter=types.ChannelParticipantsRecent(),
                        offset=0,
                        limit=200,
                        hash=0
                    )
                ),
                timeout=30
            )
            
            for participant in result.participants:
                if hasattr(participant, 'user_id') and participant.user_id == user_id:
                    return True
                elif hasattr(participant, 'id') and participant.id == user_id:
                    return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ خطا در بررسی کاربر {user_id}: {e}")
            return False
    
    def _is_cache_expired(self) -> bool:
        """بررسی انقضای کش"""
        if self.cache_timestamp == 0:
            return True
        return (time.time() - self.cache_timestamp) > self.cache_ttl
    
    def is_member(self, user_id: int) -> bool:
        """بررسی عضویت کاربر (فقط از کش می‌خواند)"""
        return user_id in self.members
    
    def get_member_count(self) -> int:
        """تعداد اعضای کش شده"""
        return len(self.members)
    
    def get_join_message(self) -> str:
        """دریافت پیام عضویت (برای ارسال در گروه‌ها)"""
        return self.join_message
    
    def get_missing_message(self, user_id: int) -> str:
        """ساخت پیام عدم عضویت (برای ارسال در گروه‌ها)"""
        return (
            f"😊 **هنوز عضو {self.channel_name} نشدی میویی!**\n\n"
            f"📢 **راه عضویت:**\n"
            f"┘─ روی **پروفایل من** کلیک کن\n"
            f"┘─ در بخش **بیوگرافی**، لینک کانال رو پیدا کن\n"
            f"┘─ روی لینک کلیک کن و عضو شو\n\n"
            f"🌸 بعد از عضویت، دوباره `عضو شدم` رو بفرست."
        )
    
    # ============================================================
    # ✅ اصلاح شده با auto_delete
    # ============================================================
    
    async def send_join_message(self, chat_id, message, send_func):
        """ارسال پیام عضویت در گروه (با حذف خودکار بعد از 60 ثانیه)"""
        await send_func(
            chat_id,
            self.join_message,
            reply_to=message.id,
            auto_delete=True,
            delete_after=60
        )
    
    async def send_missing_message(self, user_id, chat_id, message, send_func):
        """ارسال پیام عدم عضویت در گروه (با حذف خودکار بعد از 30 ثانیه)"""
        await send_func(
            chat_id,
            self.get_missing_message(user_id),
            reply_to=message.id,
            auto_delete=True,
            delete_after=30
        )