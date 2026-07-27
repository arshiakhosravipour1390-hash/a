# handlers/pet_handler.py
from database import *
from utils import *
from config import PET_PRICE
import sqlite3
import asyncio
import math
import re
from datetime import datetime, timedelta

# ============================================================
# تابع کمکی برای پاک کردن کاراکترهای خاص
# ============================================================

def clean_name(name):
    """حذف کاراکترهای خاص از اسم"""
    if not name:
        return "کاربر"
    cleaned = re.sub(r'[^\w\s\u0600-\u06FF\uFB8A\u067E\u0686\u0698\u06AF\u06A9\u06BE\u06CC]', '', str(name))
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else "کاربر"


class PetHandler:
    def __init__(self):
        self.pending_feed = {}
        self.client = None
    
    def set_client(self, client):
        self.client = client
    
    # ============================================================
    # ✅ هندلر اصلی با سطح مورد نیاز ۳
    # ============================================================
    
    async def handle(self, user_id, chat_id, text, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        level = safe_int(user[4], 1)
        text_normalized = text.strip()
        
        # ============================================================
        # ✅ چک کردن سطح برای دستور "پیشی"
        # ============================================================
        if text_normalized == "پیشی":
            if level < 3:
                await send_func(
                    chat_id,
                    f"🐱 **تو هنوز یک پیشی نوب و تازه‌کاری!**\n\n"
                    f"📊 سطح فعلی تو: {level}\n"
                    f"🎯 سطح مورد نیاز برای خرید پیشی: 3\n"
                    f"💪 {3 - level} سطح دیگه باید میو کنی!\n\n"
                    f"🌸 پیشی‌ها فقط به پیشی‌های با تجربه اعتماد میکنن!\n"
                    f"💡 بیشتر میو کن تا به سطح ۳ برسی و یه پیشی بامزه داشته باشی! 🐱",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            await self._handle_pet_panel(user_id, chat_id, message, send_func)
            return
        
        # ============================================================
        # ✅ چک کردن اسم پیشی (با فیلتر)
        # ============================================================
        pet_name = user[8]
        if pet_name:
            pet_name = clean_name(pet_name)
        
        if pet_name and text_normalized == pet_name:
            if level < 3:
                await send_func(
                    chat_id,
                    f"🐱 **تو هنوز یک پیشی نوب و تازه‌کاری!**\n\n"
                    f"📊 سطح فعلی تو: {level}\n"
                    f"🎯 سطح مورد نیاز برای داشتن پیشی: 3\n\n"
                    f"🌸 اول به سطح ۳ برس، بعد بیا پیشیت رو صدا کن! 🐱",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            await self._handle_pet_panel(user_id, chat_id, message, send_func)
            return
        
        # ============================================================
        # ✅ بقیه دستورات پیشی با سطح ۳
        # ============================================================
        if text_normalized in ["غذا", "جمع‌آوری", "جمع آوری", "برداشت", "ارتقا سطح", "ارتقا مقام"]:
            if level < 3:
                await send_func(
                    chat_id,
                    f"😿 **تو هنوز یک پیشی نوب و تازه‌کاری!**\n\n"
                    f"📊 سطح فعلی تو: {level}\n"
                    f"🎯 سطح مورد نیاز: 3\n\n"
                    f"💡 اول `پیشی` بخر تا بتونی از این دستورات استفاده کنی!\n"
                    f"🌸 پیشی‌ها فقط به پیشی‌های با تجربه اعتماد میکنن! 🐱",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            
            if text_normalized == "غذا":
                await self._handle_feed_smart(user_id, chat_id, message, send_func)
            elif text_normalized in ["جمع‌آوری", "جمع آوری", "برداشت"]:
                await self._handle_collect(user_id, chat_id, message, send_func)
            elif text_normalized == "ارتقا سطح":
                await self._handle_upgrade_level(user_id, chat_id, message, send_func)
            elif text_normalized == "ارتقا مقام":
                await self._handle_promote_rank(user_id, chat_id, message, send_func)
            return
        
        # ============================================================
        # ✅ دستورات تغییر اسم و انتخاب غذا (با سطح ۳)
        # ============================================================
        if text_normalized.startswith("انتخاب غذا"):
            if level < 3:
                await send_func(
                    chat_id,
                    f"😿 **تو هنوز یک پیشی نوب و تازه‌کاری!**\n\n"
                    f"💡 اول `پیشی` بخر تا بتونی بهش غذا بدی! 🐱",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            await self._handle_feed_confirm(user_id, chat_id, text, message, send_func)
            return
        
        if text_normalized.startswith("تغییر اسم پیشی"):
            if level < 3:
                await send_func(
                    chat_id,
                    f"😿 **تو هنوز یک پیشی نوب و تازه‌کاری!**\n\n"
                    f"💡 اول `پیشی` بخر تا بتونی اسمش رو عوض کنی! 🐱",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            await self._handle_rename(user_id, chat_id, text, message, send_func)
            return
    
    # ============================================================
    # پنل پیشی
    # ============================================================
    
    async def _handle_pet_panel(self, user_id, chat_id, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        if not user[8]:
            if user[6] < PET_PRICE:
                await send_func(
                    chat_id,
                    f"😿 کاربر {get_user_name(user)}\n"
                    f"❌ **شما هنوز پیشی ندارید..**\n\n"
                    f"💰 **قیمت خرید پیشی :** {format_number(PET_PRICE)} 🪙\n"
                    f"💰 **میو پوینت هات :** {format_number(user[6])} 🪙\n\n"
                    f"🌸 یه پیشی بامزه منتظر توست! 🐱",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=15
                )
                return
            
            default_name = f"پیشی {user_id}"
            cleaned_name = clean_name(default_name)
            
            if buy_pet(user_id, cleaned_name):
                user = get_user(user_id)
                await send_func(
                    chat_id,
                    f"🎉 **تبریک!**\n\n"
                    f"🐱 شما صاحب یک پیشی شدید!\n"
                    f"💕 نام: {cleaned_name}\n"
                    f"💰 هزینه: {format_number(PET_PRICE)} 🪙\n"
                    f"📊 سطح: 1/5\n"
                    f"🌟 مقام: مینی گربه تازه کار 🐱 (0)\n\n"
                    f"📌 برای دیدن پنل پیشی، دوباره `پیشی` یا اسم پیشی رو بزن!",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=30
                )
            else:
                await send_func(
                    chat_id,
                    "❌ خطا در خرید پیشی.",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
            return
        
        panel = await self._build_pet_panel(user_id)
        await send_func(chat_id, panel, reply_to=message.id, auto_delete=True, delete_after=30)
    
    async def _build_pet_panel(self, user_id):
        user = get_user(user_id)
        if not user:
            return "❌ کاربر پیدا نشد!"
        
        raw_username = get_user_name(user)
        username = clean_name(raw_username)
        
        pet_name = user[8]
        if pet_name:
            pet_name = clean_name(pet_name)
        
        pet_level = safe_int(user[9], 1)
        pet_points = safe_int(user[10])
        pet_rank = safe_int(user[13]) if len(user) > 13 else 0
        pet_max_level = safe_int(user[14]) if len(user) > 14 else 5
        
        rank_info = get_pet_rank_info(pet_rank)
        rank_name = rank_info["name"]
        max_hunger = rank_info["max_hunger"]
        
        current_pet_points = get_pet_points(user_id)
        capacity = get_pet_capacity(pet_rank, pet_level)
        
        is_hungry = is_pet_hungry(user_id)
        hunger_remaining_hours = get_hunger_remaining(user_id)
        hunger_status = get_hunger_status(user_id)
        
        if is_hungry or hunger_remaining_hours <= 0:
            hunger_units = 0
        else:
            hunger_units = math.ceil(hunger_remaining_hours / 2)
            if hunger_units > max_hunger:
                hunger_units = max_hunger
        
        hunger_display = f"{hunger_units} / {max_hunger}"
        production = get_pet_production(pet_rank, pet_level)
        upgrade_cost = get_pet_upgrade_cost(pet_level) if pet_level < pet_max_level else 0
        promote_cost = get_pet_promote_cost(pet_rank) if pet_rank < 5 else 0
        rank_display = f"{rank_name} ({pet_rank})"
        
        panel = (
            f"🐱 پت {username} 🐈\n\n"
            f"💕 نام : {pet_name}\n"
            f"🍖 شکم : {hunger_status} ({hunger_display})\n\n"
            f"🌟 مقام : {rank_display}\n"
            f"⭐️ سطح : {pet_level} / {pet_max_level}\n\n"
            f"💰 پوینت‌های تولید شده : {format_number(current_pet_points)} 🪙\n"
            f"💫 تولید در ثانیه : {production:.2f} 🪙\n"
            f"📦 ظرفیت : {format_number(capacity)}\n\n"
        )
        
        if pet_level < pet_max_level:
            panel += f"💰 **هزینه ارتقا سطح :** {format_number(upgrade_cost)} 🪙\n"
            panel += f"📌 `ارتقا سطح` - ارتقا سطح\n"
        else:
            panel += f"⭐ به حداکثر سطح رسیدی! برای ارتقا مقام اقدام کن.\n"
        
        if pet_rank < 5 and pet_level >= pet_max_level:
            panel += f"💰 **هزینه ارتقا مقام :** {format_number(promote_cost)} 🪙\n"
            panel += f"📌 `ارتقا مقام` - ارتقا مقام ({pet_rank} → {pet_rank + 1})\n"
        elif pet_rank < 5:
            panel += f"🔒 **برای ارتقا مقام، ابتدا سطح را به {pet_max_level} برسان!**\n"
        else:
            panel += f"👑 **به بالاترین مقام رسیدی! (مقام {pet_rank})**\n"
        
        panel += f"\n📌 **دستورات:**\n"
        panel += f"`جمع‌آوری` / `برداشت` - برداشت پوینت‌ها\n"
        panel += f"`غذا` - غذا دادن\n"
        panel += f"`تغییر اسم پیشی` - تغییر اسم"
        
        return panel
    
    async def _edit_message(self, chat_id, msg_id, new_text):
        try:
            if self.client:
                await self.client.edit_message(chat_id, msg_id, new_text)
                print(f"✅ پیام {msg_id} ویرایش شد!")
        except Exception as e:
            print(f"❌ خطا در ویرایش: {e}")
    
    # ============================================================
    # ارتقا سطح
    # ============================================================
    
    async def _handle_upgrade_level(self, user_id, chat_id, message, send_func):
        user = get_user(user_id)
        if not user[8]:
            await send_func(
                chat_id,
                "❌ تو هنوز پیشی نداری! اول `پیشی` بخر.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        pet_level = safe_int(user[9], 1)
        pet_rank = safe_int(user[13]) if len(user) > 13 else 0
        pet_max_level = safe_int(user[14]) if len(user) > 14 else 5
        
        if pet_level >= pet_max_level:
            await send_func(
                chat_id,
                f"❌ **پیشی {user[8]} به حداکثر سطح رسیده!**\n\n"
                f"⭐ سطح فعلی: {pet_level} / {pet_max_level}\n"
                f"📌 برای ادامه، باید `ارتقا مقام` کنی.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        cost = get_pet_upgrade_cost(pet_level)
        
        if user[6] < cost:
            await send_func(
                chat_id,
                f"❌ **پوینت کافی نیست!**\n\n"
                f"💰 نیاز: {format_number(cost)} 🪙\n"
                f"💰 موجودی: {format_number(user[6])} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        new_level = pet_level + 1
        
        update_user(
            user_id,
            points=int(user[6] - cost),
            pet_level=int(new_level),
            pet_points=0
        )
        
        user = get_user(user_id)
        new_production = get_pet_production(pet_rank, new_level)
        
        temp_msg = await send_func(
            chat_id,
            f"⭐ **پیشی {user[8]} ارتقا سطح داد!**\n\n"
            f"📊 سطح جدید: {new_level} / {pet_max_level}\n"
            f"💰 هزینه: {format_number(cost)} 🪙\n"
            f"⚡ سرعت تولید جدید: {new_production:.2f} 🪙 در ثانیه",
            reply_to=message.id,
            auto_delete=True,
            delete_after=15
        )
        
        await asyncio.sleep(3)
        panel = await self._build_pet_panel(user_id)
        await self._edit_message(chat_id, temp_msg.id, panel)
    
    # ============================================================
    # ارتقا مقام
    # ============================================================
    
    async def _handle_promote_rank(self, user_id, chat_id, message, send_func):
        user = get_user(user_id)
        if not user[8]:
            await send_func(
                chat_id,
                "❌ تو هنوز پیشی نداری! اول `پیشی` بخر.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        pet_level = safe_int(user[9], 1)
        pet_rank = safe_int(user[13]) if len(user) > 13 else 0
        pet_max_level = safe_int(user[14]) if len(user) > 14 else 5
        
        if pet_rank >= 5:
            await send_func(
                chat_id,
                f"👑 **پیشی {user[8]} به بالاترین مقام رسیده! (مقام ۵)**",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if pet_level < pet_max_level:
            await send_func(
                chat_id,
                f"❌ **برای ارتقا مقام، ابتدا سطح را به {pet_max_level} برسان!**\n"
                f"📊 سطح فعلی: {pet_level} / {pet_max_level}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        cost = get_pet_promote_cost(pet_rank)
        
        if user[6] < cost:
            await send_func(
                chat_id,
                f"❌ **پوینت کافی نیست!**\n\n"
                f"💰 نیاز: {format_number(cost)} 🪙\n"
                f"💰 موجودی: {format_number(user[6])} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        new_rank = pet_rank + 1
        new_max_level = get_pet_max_level(new_rank)
        
        try:
            update_pet_rank(user_id, new_rank, new_max_level, cost)
            
            user = get_user(user_id)
            
            rank_names = {
                0: "مینی گربه تازه کار 🐱",
                1: "گربه کوچولو ماهر 🎀",
                2: "پنجه طلا 🥇",
                3: "سوپر میو ⚡️",
                4: "ابر گوربا ⚡️",
                5: "گربه افسانه ای ✨"
            }
            
            new_capacity = get_pet_capacity(new_rank, 1)
            
            temp_msg = await send_func(
                chat_id,
                f"🌟 **پیشی {user[8]} ارتقا مقام داد!**\n\n"
                f"📊 مقام جدید: {rank_names.get(new_rank, 'نامشخص')} ({new_rank})\n"
                f"💰 هزینه: {format_number(cost)} 🪙\n"
                f"⭐ حداکثر سطح جدید: {new_max_level}\n"
                f"📊 سطح از ۱ شروع شد!\n"
                f"📦 ظرفیت جدید: {new_capacity}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=15
            )
            
            await asyncio.sleep(3)
            panel = await self._build_pet_panel(user_id)
            await self._edit_message(chat_id, temp_msg.id, panel)
            
        except Exception as e:
            await send_func(
                chat_id,
                f"❌ خطا در ارتقا مقام: {str(e)}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
    
    # ============================================================
    # جمع‌آوری پوینت
    # ============================================================
    
    async def _handle_collect(self, user_id, chat_id, message, send_func):
        user = get_user(user_id)
        if not user[8]:
            await send_func(
                chat_id,
                "❌ تو هنوز پیشی نداری!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        if is_pet_hungry(user_id):
            current_points = get_pet_points(user_id)
            if current_points > 0:
                earned = collect_pet_points(user_id)
                if earned > 0:
                    user = get_user(user_id)
                    await send_func(
                        chat_id,
                        f"📦 **از {user[8]} جمع‌آوری شد!**\n\n"
                        f"➕ {format_number(earned)} 🪙 پوینت\n"
                        f"📊 پوینت‌ها به کیف شما اضافه شد!\n"
                        f"😿 پیشی گرسنه است! بهش غذا بده تا دوباره کار کنه.",
                        reply_to=message.id,
                        auto_delete=True,
                        delete_after=30
                    )
                    return
            
            await send_func(
                chat_id,
                f"😿 **پیشی گرسنه است و پوینتی تولید نکرده!**\n\n"
                f"📌 اول بهش `غذا` بده تا بتونه کار کنه.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        earned = collect_pet_points(user_id)
        
        if earned == 0:
            current_points = get_pet_points(user_id)
            if current_points > 0 and current_points < 10:
                await send_func(
                    chat_id,
                    f"🐱 **پوینت کافی برای برداشت نیست!**\n\n"
                    f"📦 پوینت‌های تولید شده: {format_number(current_points)} 🪙\n"
                    f"🔒 حداقل برای برداشت: ۱۰ 🪙\n\n"
                    f"💡 صبر کن تا {10 - current_points} پوینت دیگه تولید بشه!",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=5
                )
            else:
                await send_func(
                    chat_id,
                    f"🐱 **هیچ پوینتی تولید نشده!**\n\n"
                    f"📦 پوینت‌های تولید شده: ۰ 🪙\n"
                    f"💡 صبر کن تا پوینت بیشتری تولید بشه!",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=5
                )
            return
        
        if earned > 0:
            user = get_user(user_id)
            hunger_remaining = get_hunger_remaining(user_id)
            
            temp_msg = await send_func(
                chat_id,
                f"📦 **از {user[8]} جمع‌آوری شد!**\n\n"
                f"➕ {format_number(earned)} 🪙 پوینت\n"
                f"📊 پوینت‌ها به کیف شما اضافه شد!\n"
                f"⏳ زمان سیری باقی‌مونده: {hunger_remaining:.1f} ساعت",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
            
            await asyncio.sleep(3)
            panel = await self._build_pet_panel(user_id)
            await self._edit_message(chat_id, temp_msg.id, panel)
    
    # ============================================================
    # غذا دادن
    # ============================================================
    
    async def _handle_feed_smart(self, user_id, chat_id, message, send_func):
        user = get_user(user_id)
        if not user[8]:
            await send_func(
                chat_id,
                "❌ تو هنوز پیشی نداری! اول `پیشی` بخر.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        from handlers.fridge_handler import FridgeHandler
        fridge_handler = FridgeHandler()
        fish_list = fridge_handler._get_fridge_fish(user_id)
        
        if not fish_list:
            await send_func(
                chat_id,
                f"🍽️ **یخچال شما خالی است!**\n\n"
                f"😿 پیشی {user[8]} گرسنه است!\n\n"
                f"📌 برای تهیه غذا:\n"
                f"1️⃣ `ماهی` بگیرید و `بده پیشی بخوره` کنید\n"
                f"2️⃣ یا `یخچال میویی` رو پر کنید\n\n"
                f"💡 اگه نمی‌تونی ماهی بگیری، پیشی باید گرسنه بمونه... 😢",
                reply_to=message.id,
                auto_delete=True,
                delete_after=15
            )
            return
        
        text = f"🍽️ **انتخاب غذا برای {user[8]}**\n\n"
        text += "📦 ماهی‌های موجود در یخچال:\n\n"
        
        for i, fish in enumerate(fish_list, 1):
            fish_type = fish[1]
            weight = fish[2]
            food_value = fish[4]
            is_cooked = fish[5]
            
            rarity_name = get_rarity_name(fish_type)
            emoji = get_fish_emoji(fish_type)
            cooked_emoji = "🔥" if is_cooked else "🐟"
            
            text += f"{i}️⃣ {emoji} {rarity_name} {cooked_emoji}\n"
            try:
                weight_float = float(weight)
            except:
                weight_float = 0.0
            text += f"   - وزن: {weight_float:.2f} کیلو\n"
            text += f"   - ارزش غذایی: {food_value}\n\n"
        
        text += f"📌 برای غذا دادن، شماره ماهی رو انتخاب کن:\n"
        text += f"`انتخاب غذا 1` - برای انتخاب ماهی شماره ۱"
        
        await send_func(chat_id, text, reply_to=message.id, auto_delete=True, delete_after=30)
    
    async def _handle_feed_confirm(self, user_id, chat_id, text, message, send_func):
        parts = text.split()
        if len(parts) < 2:
            await send_func(
                chat_id,
                "❌ شماره ماهی رو مشخص کن!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        try:
            fish_index = int(parts[1]) - 1
        except ValueError:
            await send_func(
                chat_id,
                "❌ شماره نامعتبر!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        from handlers.fridge_handler import FridgeHandler
        fridge_handler = FridgeHandler()
        fish_list = fridge_handler._get_fridge_fish(user_id)
        
        if fish_index < 0 or fish_index >= len(fish_list):
            await send_func(
                chat_id,
                f"❌ ماهی شماره {fish_index + 1} در یخچال وجود ندارد!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        fish = fish_list[fish_index]
        user = get_user(user_id)
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM fridge_fish WHERE id = ?", (fish[0],))
        conn.commit()
        conn.close()
        
        food_value = fish[4]
        if fish[5] == 1:
            food_value = food_value * 2
        
        feed_pet(user_id, food_value)
        
        fish_type = fish[1]
        weight = fish[2]
        rarity_name = get_rarity_name(fish_type)
        emoji = get_fish_emoji(fish_type)
        cooked_text = "پخته 🔥" if fish[5] == 1 else "خام 🐟"
        
        await send_func(
            chat_id,
            f"🍖 **{user[8]} ماهی رو یام یام کرد!** 😺\n\n"
            f"{emoji} **نوع:** {rarity_name} ({cooked_text})\n"
            f"⚖️ **وزن:** {float(weight):.2f} کیلو\n"
            f"🍖 **ارزش غذایی:** {food_value}\n\n"
            f"⏳ پیشی تا {food_value * 2} ساعت سیر می‌مونه!",
            reply_to=message.id,
            auto_delete=True,
            delete_after=30
        )
    
    # ============================================================
    # تغییر اسم پیشی
    # ============================================================
    
    async def _handle_rename(self, user_id, chat_id, text, message, send_func):
        """تغییر اسم پیشی با فیلتر کردن کاراکترهای خاص"""
        user = get_user(user_id)
        if not user:
            await send_func(
                chat_id,
                "❌ کاربر پیدا نشد!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        if not user[8]:
            await send_func(
                chat_id,
                "❌ تو هنوز پیشی نداری! اول `پیشی` بخر.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        new_name = text.replace("تغییر اسم پیشی", "").strip()
        if not new_name:
            await send_func(
                chat_id,
                "❌ **لطفاً اسم جدید رو بنویس:**\n"
                "مثال: `تغییر اسم پیشی بامزی`",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        cleaned_name = clean_name(new_name)
        
        if len(cleaned_name) > 20:
            await send_func(
                chat_id,
                f"❌ اسم نباید بیشتر از ۲۰ کاراکتر باشه.\n"
                f"اسم بعد از پاکسازی: {cleaned_name[:20]}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        if cleaned_name != new_name:
            await send_func(
                chat_id,
                f"⚠️ کاراکترهای خاص از اسم حذف شدن.\n"
                f"اسم جدید: `{cleaned_name}`",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
        
        update_user(user_id, pet_name=cleaned_name[:20])
        await send_func(
            chat_id,
            f"✅ **اسم پیشی به `{cleaned_name}` تغییر کرد!** 🐱\n\n"
            f"📌 حالا با نوشتن `{cleaned_name}` می‌تونی پنل پیشی رو باز کنی!",
            reply_to=message.id,
            auto_delete=True,
            delete_after=30
        )