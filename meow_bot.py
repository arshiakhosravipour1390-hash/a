# meow_bot.py
import asyncio
import re
import traceback
import time
from collections import deque
from datetime import datetime, timedelta
from splusthon import SoroushClient
from splusthon.sessions import StringSession
from splusthon.errors import RPCError

from config import *
from database import *
from utils import *

from handlers.pet_handler import PetHandler
from handlers.bank_handler import BankHandler
from handlers.casino_handler import CasinoHandler
from handlers.transfer_handler import TransferHandler
from handlers.fishing_handler import FishingHandler
from handlers.meow_handler import MeowHandler
from handlers.fridge_handler import FridgeHandler
from handlers.academy_handler import AcademyHandler

# ✅ غیرفعال کردن Force Join
# from force_join import ForceJoinManager

init_db()

# ====== دستورات ویژه ======
SPECIAL_COMMANDS = {
    "میوهام", "میوهاش", "پروفایل", "لیدربرد", "پیشی", "غذا",
    "جمع‌آوری", "جمع آوری", "برداشت",
    "ارتقا سطح", "ارتقا مقام",
    "بانک میویی", "میو بانک", "کازینو میویی",
    "قلاب ماهیگیری", "ماهی", "ارتقا قلاب",
    "یخچال میویی", "ارتقا یخچال",
    "مخفی کردن پروفایل", "کمک", "راهنما", "آکادمی میویی", "بس کن"
}

# ====== دستوراتی که فقط در گروه اجرا میشن ======
GROUP_ONLY_COMMANDS = {
    "میو", "مع", "مو", "پیشی", "غذا", "جمع‌آوری", "جمع آوری", "برداشت",
    "ارتقا سطح", "ارتقا مقام", "ماهی", "قلاب ماهیگیری", "ارتقا قلاب",
    "یخچال میویی", "ارتقا یخچال", "بانک میویی", "میو بانک",
    "واریز", "برداشت از بانک", "کارت به کارت", "کازینو میویی",
    "تاس", "گردونه", "معدن", "انتقال میویی", "انتقال",
    "میوهاش", "بس کن", "فروش ماهی", "بده پیشی بخوره", "بندازش تو یخچال",
    "پختن", "یام یام کردن", "بیرون آوردن"
}


class MeowBot:
    def __init__(self):
        self.client = None
        self.me = None
        self.processed_messages = deque(maxlen=5000)
        self.invalid_channels = set()
        
        self.pet_handler = PetHandler()
        self.bank_handler = BankHandler()
        self.casino_handler = CasinoHandler()
        self.transfer_handler = TransferHandler()
        self.fishing_handler = FishingHandler()
        self.meow_handler = MeowHandler()
        self.fridge_handler = FridgeHandler()
        self.academy_handler = AcademyHandler()
        
        self.force_join = None  # ✅ غیرفعال
        self._join_cooldowns = {}
        self._panel_states = {}
    
    async def start(self):
        print(f"🐱 ربات {BOT_NAME} در حال راه‌اندازی...")
        print("=" * 50)
        
        try:
            self.client = SoroushClient(StringSession(BOT_SESSION))
            await self.client.start()
            self.me = await self.client.get_me()
            print(f"✅ ربات متصل شد! (@{self.me.username or self.me.first_name})")
            print(f"📌 ID ربات: {self.me.id}")
            print("=" * 50)
            print(f"👑 ادمین: @{ADMIN_NAME}")
            print(f"📢 کانال: @{CHANNEL_NAME}")
            print("=" * 50)
            print("📦 هندلرها:")
            print("  ✅ PetHandler")
            print("  ✅ BankHandler")
            print("  ✅ CasinoHandler")
            print("  ✅ TransferHandler")
            print("  ✅ FishingHandler")
            print("  ✅ MeowHandler")
            print("  ✅ FridgeHandler")
            print("  ✅ AcademyHandler")
            print("=" * 50)
            
            self.transfer_handler.set_client(self.client)
            self.fishing_handler.set_client(self.client)
            self.pet_handler.set_client(self.client)
            self.bank_handler.set_client(self.client)
            self.meow_handler.set_client(self.client)
            self.fridge_handler.set_client(self.client)
            self.casino_handler.set_client(self.client)
            self.academy_handler.set_client(self.client)
            print(f"✅ کلاینت در همه هندلرها تنظیم شد!")
            print("=" * 50)
            
            # ✅ Force Join غیرفعال
            print("🔒 سیستم Force Join غیرفعال است!")
            self.force_join = None
            print("=" * 50)
            
            print(f"🗑️ حذف خودکار میو: {'فعال' if AUTO_DELETE_MEOW else 'غیرفعال'}")
            print(f"⏱️ تاخیر حذف: {AUTO_DELETE_MEOW_DELAY} ثانیه")
            print("=" * 50)
            
            await self._main_loop()
            
        except KeyboardInterrupt:
            print("\n🛑 در حال خاموش کردن ربات...")
            if self.force_join:
                await self.force_join.stop()
            print("👋 ربات خاموش شد!")
            raise
        except Exception as e:
            print(f"❌ خطا در راه‌اندازی: {e}")
            traceback.print_exc()
            if self.force_join:
                await self.force_join.stop()
    
    async def _main_loop(self):
        print("🔄 گوش دادن به پیام‌ها...")
        
        while True:
            try:
                try:
                    dialogs = await self.client.get_dialogs()
                except Exception as e:
                    print(f"⚠️ خطا در دریافت دیالوگ‌ها: {e}")
                    await asyncio.sleep(5)
                    continue
                
                for dialog in dialogs:
                    try:
                        entity = dialog.entity
                        entity_id = getattr(entity, 'id', None)
                        
                        if entity_id in self.invalid_channels:
                            continue
                        
                        try:
                            messages = await self.client.get_messages(entity, limit=2)
                        except RPCError as e:
                            if "private" in str(e).lower() or "access" in str(e).lower():
                                print(f"⏭️ رد کردن کانال/گروه خصوصی: {getattr(entity, 'title', 'نامشخص')}")
                                if entity_id:
                                    self.invalid_channels.add(entity_id)
                            continue
                        except Exception as e:
                            print(f"⚠️ خطا در دریافت پیام‌ها: {e}")
                            continue
                        
                        for message in messages:
                            if not message or not message.message:
                                continue
                            
                            msg_id = f"{message.id}_{message.sender_id}_{message.date}"
                            if msg_id in self.processed_messages:
                                continue
                            
                            self.processed_messages.append(msg_id)
                            await self._process(message)
                    
                    except Exception as e:
                        print(f"⚠️ خطا در پردازش دیالوگ: {e}")
                        continue
                
                await asyncio.sleep(2)
            
            except Exception as e:
                print(f"❌ خطا در حلقه اصلی: {e}")
                traceback.print_exc()
                await asyncio.sleep(5)
    
    async def _is_admin(self, user_id):
        return int(user_id) == int(ADMIN_ID)
    
    def _can_send_join_message(self, user_id: int) -> bool:
        if user_id not in self._join_cooldowns:
            return True
        
        last_sent = self._join_cooldowns[user_id]
        elapsed = time.time() - last_sent
        return elapsed >= 300
    
    def _set_join_cooldown(self, user_id: int):
        self._join_cooldowns[user_id] = time.time()
        
        if len(self._join_cooldowns) > 1000:
            now = time.time()
            to_remove = []
            for uid, timestamp in self._join_cooldowns.items():
                if now - timestamp > 3600:
                    to_remove.append(uid)
            for uid in to_remove:
                del self._join_cooldowns[uid]
    
    # ============================================================
    # ✅ ارسال پیام با تشخیص پیوی
    # ============================================================
    
    async def _send_message(self, entity, text, reply_to=None, auto_delete=False, delete_after=10):
        try:
            if not text:
                return None
            if len(text) > 4000:
                text = text[:3997] + "..."
            
            import re
            text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[آی‌پی]', text)
            
            is_private = False
            
            if isinstance(entity, int) or (isinstance(entity, str) and entity.isdigit()):
                is_private = True
            
            if hasattr(entity, 'type'):
                try:
                    if entity.type == 'private':
                        is_private = True
                except:
                    pass
            
            if hasattr(entity, 'peer_id'):
                try:
                    if hasattr(entity.peer_id, 'user_id'):
                        is_private = True
                except:
                    pass
            
            if is_private:
                auto_delete = False
            
            if reply_to:
                try:
                    msg = await self.client.send_message(entity, text, reply_to=reply_to)
                except Exception as e:
                    print(f"⚠️ خطا در ارسال با ریپلای ({reply_to}): {e}")
                    msg = await self.client.send_message(entity, text)
            else:
                msg = await self.client.send_message(entity, text)
            
            if auto_delete and msg and not is_private:
                asyncio.create_task(self._auto_delete_message(msg, delete_after))
            
            return msg
        except Exception as e:
            print(f"❌ خطا در ارسال پیام: {e}")
            return None
    
    async def _auto_delete_message(self, message, delay=10):
        await asyncio.sleep(delay)
        try:
            await self.client.delete_messages(message.peer_id, [message.id])
            print(f"🗑️ پیام {message.id} حذف شد!")
        except Exception as e:
            print(f"❌ خطا در حذف پیام: {e}")
    
    async def _edit_message(self, chat_id, msg_id, new_text):
        try:
            if self.client:
                await self.client.edit_message(chat_id, msg_id, new_text)
                print(f"✅ پیام {msg_id} ویرایش شد!")
        except Exception as e:
            print(f"❌ خطا در ویرایش: {e}")
    
    # ============================================================
    # ✅ ارسال راهنمای کامل در پیوی
    # ============================================================
    
    async def _send_complete_help(self, user_id):
        text = (
            "🐱 **به دنیای میویی خوش اومدی!** 🐱\n\n"
            "🌸 اینجا یه دنیای جادویی پر از پیشی‌های بامزه، ماجراجویی‌های هیجان‌انگیز و کلی پوینت هست!\n\n"
            "═══════════════════════\n"
            "**🔰 هدف بازی چیه؟**\n"
            "تو قراره با میو کردن، ماهیگیری، پرورش پیشی و بازی‌های مختلف، **میو پوینت** 🪙 جمع کنی و به یک پیشی افسانه‌ای تبدیل بشی!\n\n"
            "═══════════════════════\n"
            "**🐱 چطور شروع کنم؟**\n"
            "❶ برو توی گروه و `میو` کن (هر ۵ میو = ۱ سطح)\n"
            "❷ `قلاب ماهیگیری` بخر و `ماهی` بگیر\n"
            "❸ `پیشی` بخر و ازش پوینت جمع کن\n"
            "❹ `پروفایل` رو چک کن و پیشرفتتو ببین\n\n"
            "═══════════════════════\n"
            "**📚 آموزش کامل (`آکادمی میویی`)**\n"
            "برای یادگیری قدم به قدم همه چیز، توی پیوی همین ربات بفرست:\n"
            "`آکادمی میویی`\n\n"
            "═══════════════════════\n"
            "**📌 دستورات سریع:**\n\n"
            "🐱 **اصلی:**\n"
            "• `میو` / `مع` / `مو` - میو کردن (فقط گروه)\n"
            "• `پروفایل` / `میوهام` - پروفایل خودت\n"
            "• `میوهاش` - پروفایل دیگران (با ریپلای)\n"
            "• `لیدربرد` - برترین‌ها\n\n"
            "🐈 **پیشی (سطح ۳):**\n"
            "• `پیشی` - خرید/مدیریت پیشی\n"
            "• `غذا` - غذا دادن به پیشی\n"
            "• `جمع‌آوری` / `برداشت` - برداشت پوینت\n"
            "• `ارتقا سطح` - قوی‌تر کردن پیشی\n"
            "• `ارتقا مقام` - تغییر مقام پیشی\n"
            "• `تغییر اسم پیشی` - اسم جدید بذار\n\n"
            "🎣 **ماهیگیری (سطح ۲):**\n"
            "• `قلاب ماهیگیری` - خرید قلاب\n"
            "• `ماهی` - ماهیگیری\n"
            "• `ارتقا قلاب` - قلاب قوی‌تر\n\n"
            "❄️ **یخچال (سطح ۵):**\n"
            "• `یخچال میویی` - مشاهده یخچال\n"
            "• `ارتقا یخچال` - افزایش ظرفیت\n"
            "• `پختن (شماره)` - پختن ماهی\n"
            "• `یام یام کردن (شماره)` - غذا به پیشی\n"
            "• `فروش ماهی (شماره)` - فروش از یخچال\n\n"
            "🏦 **بانک (سطح ۴):**\n"
            "• `بانک میویی` - مدیریت بانک\n"
            "• `واریز 1000` - واریز\n"
            "• `برداشت 1000` - برداشت\n"
            "• `کارت به کارت 1000` - انتقال (با ریپلای)\n\n"
            "🎰 **کازینو (سطح ۴):**\n"
            "• `کازینو میویی` - ورود\n"
            "• `تاس زوج 1000` - شرط زوج\n"
            "• `تاس فرد 1000` - شرط فرد\n"
            "• `گردونه 1000` - گردونه شانس (سطح ۵)\n"
            "• `معدن 1000` - معدن الماس (سطح ۶)\n\n"
            "💰 **انتقال (سطح ۳):**\n"
            "• `انتقال میویی 1000` - انتقال پوینت (با ریپلای)\n\n"
            "═══════════════════════\n"
            "**🌟 سطوح و قابلیت‌ها:**\n"
            "• سطح ۱: شروع ماجراجویی\n"
            "• سطح ۲: 🎣 ماهیگیری باز میشه\n"
            "• سطح ۳: 🐈 پیشی و 💰 انتقال باز میشه\n"
            "• سطح ۴: 🏦 بانک و 🎰 کازینو باز میشه\n"
            "• سطح ۵: ❄️ یخچال میویی باز میشه\n"
            "• سطح ۶: 💎 معدن الماس باز میشه\n\n"
            "═══════════════════════\n"
            f"📢 **کانال رسمی:** @{CHANNEL_NAME}\n"
            "🌸 سوالی داری؟ توی گروه بپرس! 🐱"
        )
        await self._send_message(user_id, text)
    
    async def _send_help(self, user_id):
        await self._send_complete_help(user_id)
    
    async def _process_private_commands(self, user_id, chat_id, text, message):
        if text in ["پروفایل", "میوهام"]:
            await self.meow_handler.get_profile(user_id, chat_id, message, self._send_message)
        
        elif text == "لیدربرد":
            await self.meow_handler.get_leaderboard(chat_id, message, self._send_message)
        
        elif text == "مخفی کردن پروفایل":
            await self.meow_handler.toggle_privacy(user_id, chat_id, message, self._send_message)
        
        elif text in ["کمک", "راهنما"]:
            await self._send_complete_help(user_id)
        
        elif text == "آکادمی میویی":
            await self.academy_handler.handle(user_id, chat_id, text, message, self._send_message)
    
    async def _process(self, message):
        try:
            if not message or not message.message:
                return
            
            user_id = message.sender_id
            if not user_id:
                return
            
            if user_id == self.me.id:
                return
            
            if hasattr(message, 'post') and message.post:
                if hasattr(message, 'from_id') and message.from_id:
                    if message.from_id == self.me.id:
                        return
            
            if hasattr(message, 'via_bot_id') and message.via_bot_id == self.me.id:
                return
            
            text = message.message or ""
            chat_id = message.peer_id
            
            is_group_chat = (
                hasattr(message.peer_id, "channel_id") or
                hasattr(message.peer_id, "chat_id")
            )
            
            # ============================================================
            # ✅ اگر پیوی هست
            # ============================================================
            
            if not is_group_chat:
                # اگر کاربر در آکادمی هست
                if user_id in self.academy_handler.user_sessions:
                    session = self.academy_handler.user_sessions.get(user_id, {})
                    if session.get("state") in ["selecting_section", "viewing_topic"]:
                        await self.academy_handler.handle(user_id, chat_id, text, message, self._send_message)
                        return
                
                if text.strip() == "آکادمی میویی":
                    await self.academy_handler.handle(user_id, chat_id, text, message, self._send_message)
                    return
                
                if text in ["پروفایل", "میوهام", "لیدربرد", "کمک", "راهنما", "مخفی کردن پروفایل"]:
                    await self._process_private_commands(user_id, chat_id, text, message)
                    return
                
                is_group_command = False
                for cmd in GROUP_ONLY_COMMANDS:
                    if text.startswith(cmd):
                        is_group_command = True
                        break
                    if text.startswith("واریز") or text.startswith("برداشت") or text.startswith("کارت به کارت") or text.startswith("انتقال"):
                        is_group_command = True
                        break
                    if text.startswith("پختن") or text.startswith("یام یام کردن") or text.startswith("بیرون آوردن"):
                        is_group_command = True
                        break
                
                if is_group_command:
                    await self._send_auto_delete(
                        chat_id,
                        f"❌ **این دستور فقط در گروه‌ها قابل اجراست!** 🐱\n\n"
                        f"💡 لطفاً در یکی از گروه‌هایی که ربات عضو هست، این دستور رو بفرست.\n"
                        f"📚 برای آموزش، `آکادمی میویی` رو بفرست.",
                        reply_to=message.id,
                        delay=10
                    )
                    return
                
                if text.startswith('/'):
                    if text == '/start' or text == '/help':
                        await self._send_complete_help(user_id)
                    elif text == '/stats' and await self._is_admin(user_id):
                        await self._handle_stats(user_id)
                elif text in ["کمک", "راهنما"]:
                    await self._send_complete_help(user_id)
                return
            
            # ============================================================
            # ✅ اگر گروه هست
            # ============================================================
            
            # راهنما در گروه
            if text in ["راهنما", "کمک"]:
                await self._send_message(
                    chat_id,
                    "📚 **راهنمای میویی** 🐱\n\n"
                    "🌸 راهنمای کامل بازی در **پیوی** برای شما ارسال شد!",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=15
                )
                await self._send_complete_help(user_id)
                return
            
            # آکادمی در گروه
            if text == "آکادمی میویی":
                await self._send_message(
                    chat_id,
                    "📚 **آکادمی میویی** 🐱\n\n"
                    "🌸 لطفاً این دستور را در **پیوی** ربات اجرا کنید.\n"
                    f"💡 پیوی ربات: `@{BOT_USERNAME}`\n\n"
                    "📌 بعد از رفتن به پیوی، دوباره `آکادمی میویی` رو بفرست.",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=20
                )
                return
            
            # ============================================================
            # ✅ بررسی عضویت در کانال اجباری (غیرفعال)
            # ============================================================
            
            # ✅ عضویت اجباری غیرفعال است - این بخش کاملاً حذف شده
            
            # ============================================================
            # ادامه کد قبلی برای گروه‌ها
            # ============================================================
            
            first_name = ""
            username = ""
            if hasattr(message, 'sender') and message.sender:
                first_name = getattr(message.sender, 'first_name', '')
                username = getattr(message.sender, 'username', '')
            
            user = get_user(user_id)
            if not user:
                create_user(user_id, username, first_name)
                user = get_user(user_id)
            else:
                if (not user[2] or not user[3]) and (username or first_name):
                    update_user_info(user_id, username, first_name)
                    user = get_user(user_id)
            
            if is_group_chat:
                group_id = message.peer_id.channel_id
                
                if not get_group(group_id):
                    create_group(group_id, "")
                
                if text in SPECIAL_COMMANDS:
                    await self._process_commands(user_id, chat_id, group_id, text, message)
                    return
                
                # فقط در گروه، اعداد ۱ تا ۹ به کازینو برن
                if is_group_chat and text.isdigit() and len(text) == 1 and 1 <= int(text) <= 9:
                    await self.casino_handler.handle_mine_action(user_id, chat_id, text, message, self._send_message)
                    return
                
                if is_meow_word(text):
                    await self.meow_handler.handle_meow(
                        user_id, group_id, chat_id, message, self._send_message, self._send_private_message
                    )
                    return
                
                if user[8] and text.strip() == user[8]:
                    await self.pet_handler._handle_pet_panel(user_id, chat_id, message, self._send_message)
                    return
                
                await self._process_commands(user_id, chat_id, group_id, text, message)
        
        except Exception as e:
            print(f"❌ خطا در _process: {e}")
            traceback.print_exc()
    
    async def _send_private_welcome(self, user_id):
        text = (
            "🎉 **به خانواده میویی خوش اومدی!** 🐱\n\n"
            "🌸 عضویت تو در کانال رسمی میویی تأیید شد!\n\n"
            "📌 **برای شروع، این دستورات رو امتحان کن:**\n"
            "- `میو` - پوینت بگیر (فقط گروه)\n"
            "- `پیشی` - یه پیشی بامزه بگیر (فقط گروه - سطح ۳)\n"
            "- `پروفایل` - پروفایلت رو ببین\n\n"
            "📚 **آکادمی میویی:**\n"
            "- برای یادگیری کامل بازی، دستور `آکادمی میویی` رو بفرست.\n"
            "- همه چیز رو قدم به قدم بهت آموزش میدم! 🎓\n\n"
            "🌸 منتظرت هستیم! 🐱💕"
        )
        await self._send_message(user_id, text)
    
    async def _send_private_message(self, user_id, text):
        try:
            await self._send_message(user_id, text)
            print(f"📨 پیام خصوصی به کاربر {user_id} ارسال شد!")
        except Exception as e:
            print(f"❌ خطا در ارسال پیام خصوصی به {user_id}: {e}")
    
    async def _send_auto_delete(self, entity, text, reply_to=None, delay=5):
        try:
            await self._send_message(entity, text, reply_to=reply_to, auto_delete=True, delete_after=delay)
        except Exception as e:
            print(f"❌ خطا در ارسال پیام خودکار: {e}")
    
    async def _process_commands(self, user_id, chat_id, group_id, text, message):
        if text in ["پروفایل", "میوهام"]:
            await self.meow_handler.get_profile(user_id, chat_id, message, self._send_message)
        
        elif text == "میوهاش":
            target_id = None
            if hasattr(message, 'is_reply') and message.is_reply:
                if hasattr(message, 'reply_to') and message.reply_to:
                    replied_msg_id = message.reply_to.reply_to_msg_id
                    try:
                        replied_message = await self.client.get_messages(message.peer_id, ids=replied_msg_id)
                        if replied_message:
                            if isinstance(replied_message, list) and len(replied_message) > 0:
                                target_id = replied_message[0].sender_id
                            else:
                                target_id = replied_message.sender_id
                    except Exception as e:
                        print(f"⚠️ خطا در دریافت پیام اصلی: {e}")
            
            if target_id:
                await self.meow_handler.get_profile(user_id, chat_id, message, self._send_message, target_id)
            else:
                await self._send_message(
                    chat_id,
                    "❌ روی پیام کاربر ریپلای کنید تا پروفایلش رو ببینید!"
                )
        
        elif text == "لیدربرد":
            await self.meow_handler.get_leaderboard(chat_id, message, self._send_message)
        
        elif text == "مخفی کردن پروفایل":
            await self.meow_handler.toggle_privacy(user_id, chat_id, message, self._send_message)
        
        elif text in ["پیشی", "غذا", "جمع‌آوری", "جمع آوری", "برداشت", "ارتقا سطح", "ارتقا مقام"]:
            await self.pet_handler.handle(user_id, chat_id, text, message, self._send_message)
        
        elif text.startswith("تغییر اسم پیشی"):
            await self.pet_handler._handle_rename(user_id, chat_id, text, message, self._send_message)
        
        elif text.startswith("انتخاب غذا"):
            await self.pet_handler.handle(user_id, chat_id, text, message, self._send_message)
        
        elif text in ["قلاب ماهیگیری", "ماهی", "ارتقا قلاب", "فروش ماهی", "بده پیشی بخوره", "بندازش تو یخچال"]:
            await self.fishing_handler.handle(user_id, chat_id, text, message, self._send_message)
        
        elif text in ["یخچال میویی", "ارتقا یخچال"] or text.startswith("پختن") or text.startswith("یام یام کردن") or text.startswith("فروش ماهی"):
            await self.fridge_handler.handle(user_id, chat_id, text, message, self._send_message)
        
        elif text in ["بانک میویی", "میو بانک"]:
            await self.bank_handler.handle_main(user_id, chat_id, message, self._send_message)
        
        elif text.startswith("واریز"):
            await self.bank_handler.handle_deposit(user_id, chat_id, text, message, self._send_message)
        
        elif text.startswith("برداشت از بانک") or text.startswith("برداشت"):
            if text.startswith("برداشت") and not text.startswith("برداشت از بانک"):
                bank = get_bank(user_id)
                if bank:
                    await self.bank_handler.handle_withdraw(user_id, chat_id, text, message, self._send_message)
                else:
                    await self.pet_handler.handle(user_id, chat_id, text, message, self._send_message)
            else:
                await self.bank_handler.handle_withdraw(user_id, chat_id, text, message, self._send_message)
        
        elif text.startswith("کارت به کارت"):
            await self.bank_handler.handle_transfer(user_id, chat_id, text, message, self._send_message)
        
        elif text == "کازینو میویی":
            await self.casino_handler.handle_main(user_id, chat_id, message, self._send_message)
        
        elif text.startswith("تاس"):
            await self.casino_handler.handle_dice(user_id, chat_id, text, message, self._send_message)
        
        elif text.startswith("گردونه"):
            await self.casino_handler.handle_spin(user_id, chat_id, text, message, self._send_message)
        
        elif text.startswith("معدن"):
            await self.casino_handler.handle_mine(user_id, chat_id, text, message, self._send_message)
        
        elif text == "بس کن":
            await self.casino_handler.handle_mine_action(user_id, chat_id, text, message, self._send_message)
        
        elif text.startswith("انتقال میویی") or text.startswith("انتقال"):
            await self.transfer_handler.handle(user_id, chat_id, text, message, self._send_message)
        
        elif text in ["آکادمی میویی", "کمک", "راهنما"]:
            # در گروه، راهنما رو به پیوی ارجاع بده
            if text in ["کمک", "راهنما"]:
                await self._send_message(
                    chat_id,
                    "📚 **راهنمای میویی** 🐱\n\n"
                    "🌸 راهنمای کامل بازی در **پیوی** برای شما ارسال شد!",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=15
                )
                await self._send_complete_help(user_id)
            else:
                await self.academy_handler.handle(user_id, chat_id, text, message, self._send_message)
    
    async def _handle_stats(self, user_id):
        import sqlite3
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users")
        total_users = c.fetchone()[0]
        c.execute("SELECT SUM(meows) FROM users")
        total_meows = c.fetchone()[0] or 0
        c.execute("SELECT SUM(points) FROM users")
        total_points = c.fetchone()[0] or 0
        c.execute("SELECT COUNT(*) FROM groups")
        total_groups = c.fetchone()[0]
        conn.close()
        
        text = (
            f"📊 **آمار کلی میویی**\n\n"
            f"👥 کاربران: {format_number(total_users)}\n"
            f"🐾 مجموع میوها: {format_number(total_meows)}\n"
            f"🪙 مجموع پوینت‌ها: {format_number(total_points)}\n"
            f"🏰 گروه‌ها: {format_number(total_groups)}"
        )
        await self._send_message(user_id, text)


async def main():
    bot = MeowBot()
    await bot.start()


if __name__ == "__main__":
    asyncio.run(main())
