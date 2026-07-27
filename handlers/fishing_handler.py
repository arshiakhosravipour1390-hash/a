# handlers/fishing_handler.py
import random
import asyncio
from datetime import datetime, timedelta
from database import *
from utils import *
from config import *

class FishingHandler:
    def __init__(self):
        self.active_fish = {}
        self.client = None
    
    def set_client(self, client):
        self.client = client
    
    async def handle(self, user_id, chat_id, text, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        level = safe_int(user[4], 1)
        
        if level < 2:
            await send_func(
                chat_id,
                f"🐱 **تو هنوز یک گربه نوب و ضعیف بی‌خاصیتی!**\n"
                f"📊 سطح فعلی: {level}\n"
                f"🎯 سطح مورد نیاز برای ماهیگیری: 2\n"
                f"💪 {2 - level} سطح دیگه باید میو کنی تا به درد ماهیگیری بخوری!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if text in ["فروش ماهی", "بده پیشی بخوره", "بندازش تو یخچال"]:
            await self._handle_fish_action(user_id, chat_id, text, message, send_func)
            return
        
        if text == "قلاب ماهیگیری":
            await self._handle_rod(user_id, chat_id, message, send_func)
        elif text == "ارتقا قلاب":
            await self._handle_upgrade_rod(user_id, chat_id, message, send_func)
        elif text == "ماهی":
            await self._handle_fish(user_id, chat_id, message, send_func)
    
    # ============================================================
    # تابع کمکی برای فرمت زمان
    # ============================================================
    
    def _format_time(self, seconds):
        """تبدیل ثانیه به فرمت خوانا"""
        seconds = int(seconds)
        if seconds < 0:
            return "اکنون"
        elif seconds < 60:
            return f"{seconds} ثانیه"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            if secs > 0:
                return f"{minutes} دقیقه و {secs} ثانیه"
            return f"{minutes} دقیقه"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours} ساعت و {minutes} دقیقه"
            return f"{hours} ساعت"
    
    # ============================================================
    # خرید و مشاهده قلاب
    # ============================================================
    
    async def _handle_rod(self, user_id, chat_id, message, send_func):
        fishing = get_fishing(user_id)
        
        if not fishing:
            user = get_user(user_id)
            points = safe_int(user[6], 0)
            if points < FISHING_ROD_PRICE:
                await send_func(
                    chat_id,
                    f"❌ **پوینت کافی نیست!**\n"
                    f"💰 قیمت قلاب: {format_number(FISHING_ROD_PRICE)} 🪙\n"
                    f"💰 موجودی: {format_number(points)} 🪙",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            
            create_fishing(user_id)
            update_user(user_id, points=int(points - FISHING_ROD_PRICE))
            await send_func(
                chat_id,
                f"🎣 **قلاب ماهیگیری سطح ۱ خریداری شد!**\n\n"
                f"💰 هزینه: {format_number(FISHING_ROD_PRICE)} 🪙\n"
                f"⏳ زمان استراحت: {self._format_time(FISHING_LEVELS[1]['cooldown'])}\n"
                f"🐟 شانس ماهیگیری:\n"
                f"  🔡 معمولی: ۹۵%\n"
                f"  🔡 کمیاب: ۵%\n\n"
                f"📌 حالا با `ماهی` می‌تونی ماهی بگیری!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
            return
        
        level = safe_int(fishing[2], 1)
        cooldown = FISHING_LEVELS[level]["cooldown"]
        next_level = level + 1
        max_level = len(FISHING_LEVELS)  # 7 سطح
        
        text = f"🎣 **قلاب ماهیگیری شما**\n\n"
        text += f"📊 سطح: {level}\n"
        text += f"⏳ زمان استراحت: {self._format_time(cooldown)}\n"
        text += f"🐟 کل ماهی‌ها: {fishing[4]}\n\n"
        text += "🍀 **شانس ماهیگیری:**\n"
        
        chances = FISHING_LEVELS[level]["chances"]
        for ftype, prob in chances.items():
            name = get_rarity_name(ftype)
            emoji = get_fish_emoji(ftype)
            text += f"  {emoji} {name}: {int(prob*100)}%\n"
        
        if level < max_level:
            cost = FISHING_LEVELS[next_level]["cost"]
            text += f"\n💰 **ارتقا به سطح {next_level}:** {format_number(cost)} 🪙\n"
            text += f"📌 برای ارتقا: `ارتقا قلاب`"
        else:
            text += "\n⭐ **به بالاترین سطح رسیدی!**"
        
        await send_func(chat_id, text, reply_to=message.id, auto_delete=True, delete_after=30)
    
    # ============================================================
    # ارتقا قلاب
    # ============================================================
    
    async def _handle_upgrade_rod(self, user_id, chat_id, message, send_func):
        fishing = get_fishing(user_id)
        if not fishing:
            await send_func(
                chat_id,
                "❌ اول باید `قلاب ماهیگیری` بخری!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        current_level = safe_int(fishing[2], 1)
        max_level = len(FISHING_LEVELS)  # 7 سطح
        
        if current_level >= max_level:
            await send_func(
                chat_id,
                "⭐ قلابت در بالاترین سطح هست!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        next_level = current_level + 1
        cost = FISHING_LEVELS[next_level]["cost"]
        
        user = get_user(user_id)
        points = safe_int(user[6], 0)
        if points < cost:
            await send_func(
                chat_id,
                f"❌ **پوینت کافی نیست!**\n"
                f"💰 هزینه: {format_number(cost)} 🪙\n"
                f"💰 موجودی: {format_number(points)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if upgrade_rod(user_id):
            await send_func(
                chat_id,
                f"🎣 **قلاب ارتقا یافت!**\n\n"
                f"📊 سطح جدید: {next_level}\n"
                f"💰 هزینه: {format_number(cost)} 🪙\n"
                f"⏳ زمان استراحت جدید: {self._format_time(FISHING_LEVELS[next_level]['cooldown'])}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
        else:
            await send_func(
                chat_id,
                "❌ خطا در ارتقا قلاب.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
    
    # ============================================================
    # ✅ ماهیگیری (نسخه اصلی - بدون امتیاز ویژه برای ادمین)
    # ============================================================
    
    async def _handle_fish(self, user_id, chat_id, message, send_func):
        fishing = get_fishing(user_id)
        if not fishing:
            await send_func(
                chat_id,
                "❌ اول باید `قلاب ماهیگیری` بخری!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        if not can_fish(user_id):
            level = safe_int(fishing[2], 1)
            cooldown = FISHING_LEVELS[level]["cooldown"]
            
            try:
                last = datetime.fromisoformat(fishing[3])
                remaining = (last + timedelta(seconds=cooldown)) - datetime.now()
                remaining_seconds = remaining.total_seconds()
                
                if remaining_seconds <= 0:
                    pass
                else:
                    await send_func(
                        chat_id,
                        f"⏳ **صبر کن!**\n"
                        f"{self._format_time(remaining_seconds)} دیگه می‌تونی ماهی بگیری.",
                        reply_to=message.id,
                        auto_delete=True,
                        delete_after=10
                    )
                    return
            except Exception as e:
                print(f"⚠️ خطا در محاسبه زمان: {e}")
        
        result = fish(user_id)
        if not result:
            await send_func(
                chat_id,
                "❌ خطا در ماهیگیری.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        fish_emojis = {
            "common": "🐟",
            "uncommon": "🐠",
            "rare": "🐡",
            "epic": "🐙",
            "legendary": "🐉"
        }
        
        name = get_rarity_name(result["type"])
        
        msg = f"🎣 شما با موفقیت {fish_emojis.get(result['type'], '🐟')} گرفتید…\n\n"
        msg += f"⭐️ **سطح :** {name} 🔡\n"
        msg += f"⚖️ **وزن :** {result['weight']} کیلو\n"
        msg += f"💰 **ارزش :** {format_number(result['value'])} 🪙\n\n"
        msg += f"🍖 **ارزش غذایی :** {result['food_value']}\n\n"
        msg += f"⏳ شما {FISHING_WAIT_TIME} ثانیه فرصت تصمیم گیری دارید\n\n"
        msg += f"📌 **برای فروش:** روی همین پیام ریپلای کنید و بنویسید `فروش ماهی`\n"
        msg += f"📌 **برای غذا دادن به پیشی:** `بده پیشی بخوره`\n"
        msg += f"📌 **برای ذخیره در یخچال:** `بندازش تو یخچال`"
        
        fish_msg = await send_func(chat_id, msg, reply_to=message.id, auto_delete=False)
        
        self.active_fish[user_id] = {
            "message": fish_msg,
            "fish_data": result,
            "expire_time": datetime.now() + timedelta(seconds=FISHING_WAIT_TIME)
        }
        
        asyncio.create_task(self._fish_expire_timer(user_id, chat_id, fish_msg.id, send_func))
    
    # ============================================================
    # اقدامات روی ماهی
    # ============================================================
    
    async def _handle_fish_action(self, user_id, chat_id, text, message, send_func):
        if user_id not in self.active_fish:
            await send_func(
                chat_id,
                "❌ تو که ماهی نداری! اول برو یه ماهی بگیر!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        fish_data = self.active_fish[user_id]
        fish_msg = fish_data["message"]
        fish_info = fish_data["fish_data"]
        
        target_id = None
        if hasattr(message, 'is_reply') and message.is_reply:
            if hasattr(message, 'reply_to') and message.reply_to:
                replied_msg_id = message.reply_to.reply_to_msg_id
                if replied_msg_id == fish_msg.id:
                    target_id = user_id
        
        if not target_id:
            await send_func(
                chat_id,
                "❌ **روی پیام ماهی ریپلای کن!**\n"
                "💡 روی پیامی که ماهی رو نشون میده ریپلای بزن و بعد دستور رو بفرست.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        del self.active_fish[user_id]
        
        if text == "فروش ماهی":
            user = get_user(user_id)
            new_points = safe_int(user[6]) + fish_info["value"]
            update_user(user_id, points=int(new_points))
            
            new_text = (
                f"🎣 شما ماهی را فروختید! 💰\n\n"
                f"⭐️ **سطح :** {get_rarity_name(fish_info['type'])} 🔡\n"
                f"⚖️ **وزن :** {fish_info['weight']} کیلو\n"
                f"💰 **فروخته شد به :** {format_number(fish_info['value'])} 🪙\n\n"
                f"📊 موجودی جدید: {format_number(new_points)} 🪙"
            )
            await self._edit_message(chat_id, fish_msg.id, new_text)
            
            await send_func(
                chat_id,
                f"✅ ماهی فروخته شد! +{format_number(fish_info['value'])} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
            return
        
        if text == "بده پیشی بخوره":
            user = get_user(user_id)
            if not user[8]:
                await send_func(
                    chat_id,
                    "❌ شما پیشی ندارید! اول `پیشی` بخرید.",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=5
                )
                return
            
            feed_pet(user_id, fish_info.get("food_value", 1))
            
            new_text = (
                f"🍖 پیشی ماهی رو یام یام کرد! 😺\n\n"
                f"⭐️ **سطح :** {get_rarity_name(fish_info['type'])} 🔡\n"
                f"⚖️ **وزن :** {fish_info['weight']} کیلو\n"
                f"🍖 **ارزش غذایی :** {fish_info.get('food_value', 1)}\n\n"
                f"😺 پیشی {user[8]} سیر و خوشحال شد!"
            )
            await self._edit_message(chat_id, fish_msg.id, new_text)
            
            await send_func(
                chat_id,
                f"🍖 {user[8]} ماهی رو خورد! 😺\n"
                f"⏳ تا {fish_info.get('food_value', 1) * 2} ساعت سیر می‌مونه.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
            return
        
        if text == "بندازش تو یخچال":
            from handlers.fridge_handler import FridgeHandler
            fridge_handler = FridgeHandler()
            
            success, msg = fridge_handler.add_fish_to_fridge(user_id, fish_info)
            
            if success:
                new_text = (
                    f"❄️ **ماهی در یخچال ذخیره شد!**\n\n"
                    f"⭐️ **سطح :** {get_rarity_name(fish_info['type'])} 🔡\n"
                    f"⚖️ **وزن :** {fish_info['weight']} کیلو\n"
                    f"💰 **ارزش :** {format_number(fish_info['value'])} 🪙\n"
                    f"🍖 **ارزش غذایی :** {fish_info.get('food_value', 1)}\n\n"
                    f"📌 برای دیدن یخچال: `یخچال میویی`"
                )
                await self._edit_message(chat_id, fish_msg.id, new_text)
                
                await send_func(
                    chat_id,
                    f"❄️ {msg}",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=30
                )
            else:
                await send_func(
                    chat_id,
                    f"❌ {msg}",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
            return
    
    # ============================================================
    # تایمر انقضای ماهی
    # ============================================================
    
    async def _fish_expire_timer(self, user_id, chat_id, msg_id, send_func):
        await asyncio.sleep(FISHING_WAIT_TIME)
        
        if user_id in self.active_fish:
            fish_data = self.active_fish[user_id]
            if fish_data["message"].id == msg_id:
                del self.active_fish[user_id]
                
                new_text = (
                    f"🎣 شما با موفقیت ماهی گرفتید… اما ماهی فرار کرد! 😿\n\n"
                    f"⏳ زمان شما به پایان رسید.\n"
                    f"📌 دوباره `ماهی` بزنید تا شانس خود را امتحان کنید."
                )
                await self._edit_message(chat_id, msg_id, new_text)
    
    # ============================================================
    # ویرایش پیام
    # ============================================================
    
    async def _edit_message(self, chat_id, msg_id, new_text):
        try:
            if self.client:
                await self.client.edit_message(chat_id, msg_id, new_text)
                print(f"✅ پیام {msg_id} ویرایش شد!")
            else:
                print(f"⚠️ client تنظیم نشده! پیام {msg_id} ویرایش نشد.")
        except Exception as e:
            print(f"❌ خطا در ویرایش پیام {msg_id}: {e}")