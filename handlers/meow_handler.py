# handlers/meow_handler.py
from datetime import datetime, timedelta
import sqlite3
from database import *
from utils import *
from config import MEOW_COOLDOWN, AUTO_DELETE_MEOW, AUTO_DELETE_MEOW_DELAY, AUTO_DELETE_WARNING_DELAY
from handlers.academy_handler import AcademyHandler

class MeowHandler:
    def __init__(self):
        self.client = None
    
    def set_client(self, client):
        self.client = client
    
    # ============================================================
    # ✅ تابع اصلی میو کردن
    # ============================================================
    
    async def handle_meow(self, user_id, group_id, chat_id, message, send_func, send_private_func=None):
        user = get_user(user_id)
        if not user:
            create_user(user_id, "", "")
            user = get_user(user_id)
        
        if not self.can_meow(user_id):
            remaining = self.get_remaining_time(user_id)
            if remaining:
                await send_func(
                    chat_id,
                    f"🐱 صبر کن! {remaining} دیگه میو کن.",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=5
                )
            return
        
        result = add_meow(user_id)
        if not result:
            await send_func(
                chat_id,
                "❌ خطا در ثبت میو!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        meow_response = get_random_meow_response()
        level_emoji = get_level_emoji(result["level"])
        
        response = f"{meow_response}\n\n"
        response += f"➕ {result['points_earned']} 🪙 پوینت!\n"
        response += f"📊 مجموع: {format_number(result['points'])} 🪙\n"
        response += f"🐾 میوها: {result['meows']}\n"
        response += f"{level_emoji} سطح: {result['level']}"
        
        if result.get("reward", 0) > 0:
            response += f"\n🎉 ارتقا سطح! +{format_number(result['reward'])} 🪙 پاداش!"
        
        await send_func(
            chat_id,
            response,
            reply_to=message.id,
            auto_delete=True,
            delete_after=10
        )
        
        # ====== اگر ارتقا سطح رخ داده، پیام تبریک بفرست ======
        if result.get("level_up", False) and send_private_func:
            academy = AcademyHandler()
            await academy.send_level_up(
                user_id,
                chat_id,
                result.get("old_level", result["level"]),
                result["level"],
                result.get("reward", 0),
                send_func,
                send_private_func
            )
        
        group = get_group(group_id)
        if group:
            update_group(group_id, total_meows=int(group[4] + 1))
    
    # ============================================================
    # ✅ توابع کمکی
    # ============================================================
    
    def can_meow(self, user_id):
        user = get_user(user_id)
        if not user or not user[7]:
            return True
        try:
            last = datetime.fromisoformat(user[7])
            return (datetime.now() - last).seconds >= MEOW_COOLDOWN
        except:
            return True
    
    def get_remaining_time(self, user_id):
        user = get_user(user_id)
        if not user or not user[7]:
            return None
        try:
            last = datetime.fromisoformat(user[7])
            remaining = (last + timedelta(seconds=MEOW_COOLDOWN)) - datetime.now()
            if remaining.total_seconds() <= 0:
                return None
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            if minutes > 0:
                return f"{minutes} دقیقه و {seconds} ثانیه"
            else:
                return f"{seconds} ثانیه"
        except:
            return None
    
    # ============================================================
    # ✅ پروفایل (با تشخیص مخفی بودن) - با auto_delete
    # ============================================================
    
    async def get_profile(self, user_id, chat_id, message, send_func, target_id=None):
        from config import ADMIN_ID, ADMIN_VANITY_MODE, ADMIN_VANITY_MESSAGE
        
        if target_id is None:
            target_id = user_id
        
        # ✅ اگر کاربر ادمین بود، پیام ویژه (با auto_delete)
        if ADMIN_VANITY_MODE and int(target_id) == int(ADMIN_ID):
            await send_func(
                chat_id,
                f"👑 **پروفایل ویژه**\n\n"
                f"{ADMIN_VANITY_MESSAGE}\n\n"
                f"🌸 برای اطلاع از بروزرسانی‌ها، کانال رو دنبال کن!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
            return
        
        user = get_user(target_id)
        if not user:
            await send_func(
                chat_id,
                "❌ کاربر پیدا نشد.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        # ============================================================
        # ✅ اگر کاربر مخفی هست و کسی غیر از خودش میخواد ببینه
        # ============================================================
        is_private = 0
        if len(user) > 17:
            is_private = safe_int(user[17])
        
        if is_private == 1 and user_id != target_id:
            await send_func(
                chat_id,
                "🔒 **این کاربر پروفایل خود را مخفی کرده است!**\n\n"
                "🌸 برای مشاهده پروفایل دیگران، از اونها بخواهید که پروفایل خود را عمومی کنند.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=15
            )
            return
        
        display_name = get_user_display(user)
        level = safe_int(user[4], 1)
        meows = safe_int(user[5])
        points = safe_int(user[6])
        street_pets = safe_int(user[12]) if len(user) > 12 else 0
        
        meow_rank = get_rank(target_id, "meows")
        point_rank = get_rank(target_id, "points")
        street_rank = get_rank(target_id, "street_pets") if len(user) > 12 else 0
        
        level_emoji = get_level_emoji(level)
        
        from config import LEVELS
        
        current_level = level
        next_level = current_level + 1
        
        current_required = LEVELS[current_level]["required"] if current_level in LEVELS else 0
        next_required = LEVELS[next_level]["required"] if next_level in LEVELS else current_required
        
        progress_meows = meows - current_required
        required_for_next = next_required - current_required
        
        if required_for_next > 0:
            progress = f"{format_number(progress_meows)} / {format_number(required_for_next)}"
            bar = get_progress_bar(progress_meows, required_for_next)
        else:
            progress = f"{format_number(meows)}"
            bar = "▰" * 10
        
        profile = (
            f"🐱 **پروفایل میویی**\n\n"
            f"👤 کاربر: {display_name}\n"
            f"🪪 آیدی: {target_id}\n\n"
            f"💰 میو پوینت‌ها: {format_number(points)} 🪙\n"
            f"🎖️ رتبه: {format_number(point_rank)}\n"
            f"🐾 میو میو‌ها: {format_number(meows)}\n"
            f"🎖️ رتبه: {format_number(meow_rank)}\n\n"
            f"🐈 پیشی‌های خیابونی: {format_number(street_pets)}\n"
            f"🎖️ رتبه: {format_number(street_rank)}\n\n"
            f"{level_emoji} سطح: {level} | {progress}\n"
            f"   {bar}\n"
        )
        
        if user[8]:
            hunger_status = "😿 من دیگه کار نمیکنمیووو" if is_pet_hungry(target_id) else "😺 سیر و خوشحال!"
            profile += (
                f"\n🐈 **پیشی:** {user[8]}\n"
                f"   📊 سطح: {safe_int(user[9], 1)}\n"
                f"   📦 پوینت‌ها: {format_number(user[10])} 🪙\n"
                f"   🍖 وضعیت: {hunger_status}\n"
            )
        
        if target_id == user_id:
            status_text = "🔒 مخفی" if is_private == 1 else "🌐 عمومی"
            profile += f"\n📌 **وضعیت پروفایل:** {status_text}\n"
            profile += f"📌 `مخفی کردن پروفایل` - مخفی/عمومی کردن پروفایل"
        
        # ✅ پروفایل با auto_delete=True (در گروه پاک میشه، در پیوی نه)
        await send_func(chat_id, profile, reply_to=message.id, auto_delete=True, delete_after=30)
    
    # ============================================================
    # ✅ لیدربرد (بدون مخفی کردن) - با auto_delete
    # ============================================================
    
    async def get_leaderboard(self, chat_id, message, send_func, limit=5):
        import sqlite3
        from config import ADMIN_ID, ADMIN_EXCLUDE_FROM_LEADERBOARD
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        if ADMIN_EXCLUDE_FROM_LEADERBOARD:
            c.execute(
                f"SELECT user_id, username, first_name, meows, points, level FROM users WHERE user_id != ? ORDER BY points DESC LIMIT ?",
                (ADMIN_ID, limit)
            )
        else:
            c.execute(
                f"SELECT user_id, username, first_name, meows, points, level FROM users ORDER BY points DESC LIMIT ?",
                (limit,)
            )
        top_users = c.fetchall()
        
        user = get_user(message.sender_id)
        user_rank = 1
        
        if user:
            try:
                user_points = safe_int(user[6])
                c.execute("SELECT COUNT(*) + 1 FROM users WHERE points > ?", (user_points,))
                result = c.fetchone()
                if result:
                    user_rank = result[0]
            except Exception as e:
                print(f"⚠️ خطا در محاسبه رتبه: {e}")
        
        conn.close()
        
        if not top_users:
            await send_func(
                chat_id,
                "📭 هنوز کاربری وجود ندارد.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        medals = ["👑", "🥈", "🥉", "🎖️", "🏅"]
        titles = ["پادشاه پیشی‌ها", "قهرمان پیشی‌ها", "وزیر پیشی‌ها", "پیشی برتر", "پیشی برتر"]
        
        text = "🏆 **لیدربرد جهانی میویی** 🐱\n\n"
        text += "💰 ثروتمندترین گربه‌های میویی\n\n"
        
        for i, user_data in enumerate(top_users):
            uid, username, first_name, meows, points, level = user_data
            if first_name:
                name = first_name
            elif username:
                name = username
            else:
                name = "پیشی ناشناس"
            
            text += f"{medals[i]} {titles[i]} : {name}\n"
            text += f"   💰 {format_number(points)} پوینت\n"
            text += f"   🐾 {format_number(meows)} میو\n\n"
        
        if user:
            user_display = get_user_display(user)
            if int(user[1]) == int(ADMIN_ID) and ADMIN_EXCLUDE_FROM_LEADERBOARD:
                text += f"🎖️ شما از لیست خارج شده‌اید (حالت توسعه‌دهنده)"
            else:
                text += f"🎖️ رتبه شما : {format_number(user_rank)} - {user_display}"
        else:
            text += f"🎖️ رتبه شما : {format_number(user_rank)}"
        
        # ✅ لیدربرد با auto_delete=True (در گروه پاک میشه، در پیوی نه)
        await send_func(chat_id, text, reply_to=message.id, auto_delete=True, delete_after=30)
    
    # ============================================================
    # ✅ مخفی کردن پروفایل
    # ============================================================
    
    async def toggle_privacy(self, user_id, chat_id, message, send_func):
        user = get_user(user_id)
        if not user:
            await send_func(
                chat_id,
                "❌ کاربر پیدا نشد.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        current = safe_int(user[17]) if len(user) > 17 else 0
        new_status = 0 if current == 1 else 1
        
        update_user(user_id, is_private=int(new_status))
        
        status_text = "🔒 مخفی" if new_status == 1 else "🌐 عمومی"
        
        # ✅ پیام تغییر وضعیت با auto_delete
        await send_func(
            chat_id,
            f"✅ **وضعیت پروفایل تغییر کرد!**\n\n"
            f"📌 وضعیت جدید: {status_text}",
            reply_to=message.id,
            auto_delete=True,
            delete_after=10
        )