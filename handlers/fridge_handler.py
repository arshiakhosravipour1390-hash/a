# handlers/fridge_handler.py
import sqlite3
import asyncio
import math
import re
from datetime import datetime, timedelta
from database import *
from utils import *
from config import *

FRIDGE_PRICE = 32500
FRIDGE_LEVEL_REQUIRED = 5
FRIDGE_MAX_LEVEL = 4
FRIDGE_BASE_CAPACITY = 2
FRIDGE_CAPACITY_PER_LEVEL = 1

FRIDGE_UPGRADE_COST = {
    2: 195000,
    3: 415000,
    4: 1250000,
}


def persian_to_english_numbers(text):
    persian_to_english = {
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
    }
    result = text
    for persian, english in persian_to_english.items():
        result = result.replace(persian, english)
    return result


def extract_number_from_text(text):
    text = persian_to_english_numbers(text)
    match = re.search(r'(\d+)', text)
    if match:
        return int(match.group(1))
    return None


class FridgeHandler:
    def __init__(self):
        self.client = None
        self._column_names = None
        self.cooking_tasks = {}
    
    def set_client(self, client):
        self.client = client
    
    def _get_columns(self):
        if self._column_names is not None:
            return self._column_names
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("PRAGMA table_info(fridge_fish)")
        cols = c.fetchall()
        conn.close()
        self._column_names = [col[1] for col in cols]
        return self._column_names
    
    def _fish_to_dict(self, fish_tuple):
        columns = self._get_columns()
        return {columns[i]: fish_tuple[i] for i in range(len(fish_tuple))}
    
    def _has_fridge(self, user_id):
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM fridge WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result is not None
    
    def _get_fridge(self, user_id):
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("SELECT level, capacity FROM fridge WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        return result
    
    def _create_fridge(self, user_id):
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute(
            "INSERT INTO fridge (user_id, level, capacity, created_at) VALUES (?, ?, ?, ?)",
            (user_id, 1, FRIDGE_BASE_CAPACITY, datetime.now().isoformat())
        )
        conn.commit()
        conn.close()
        return True
    
    def _get_fridge_fish(self, user_id):
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute(
            "SELECT * FROM fridge_fish WHERE user_id = ? ORDER BY stored_at ASC",
            (user_id,)
        )
        result = c.fetchall()
        conn.close()
        return result
    
    async def handle(self, user_id, chat_id, text, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        level = safe_int(user[4], 1)
        
        if text == "یخچال میویی":
            if self._has_fridge(user_id):
                await self._show_fridge(user_id, chat_id, message, send_func)
                return
            
            if level < FRIDGE_LEVEL_REQUIRED:
                await send_func(
                    chat_id,
                    f"❌ **نیاز به سطح {FRIDGE_LEVEL_REQUIRED} داری!**\n"
                    f"📊 سطح فعلی: {level}\n"
                    f"🎯 سطح مورد نیاز: {FRIDGE_LEVEL_REQUIRED}\n\n"
                    f"💡 برای خرید یخچال میویی باید به سطح {FRIDGE_LEVEL_REQUIRED} برسی!",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            
            if user[6] < FRIDGE_PRICE:
                await send_func(
                    chat_id,
                    f"😿 هنوز یخچال میویی نداری..\n\n"
                    f"💰 قیمت یخچال میویی : {format_number(FRIDGE_PRICE)} 🪙\n"
                    f"💰 میو پوینت هات : {format_number(user[6])} 🪙\n\n"
                    f"🔺 آیا از خرید یخچال میویی اطمینان دارید ؟\n"
                    f"📌 برای خرید: `خرید یخچال`",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=15
                )
                return
            
            await send_func(
                chat_id,
                f"😿 هنوز یخچال میویی نداری..\n\n"
                f"💰 قیمت یخچال میویی : {format_number(FRIDGE_PRICE)} 🪙\n"
                f"💰 میو پوینت هات : {format_number(user[6])} 🪙\n\n"
                f"✅ پوینت کافی داری!\n"
                f"📌 برای خرید: `خرید یخچال`",
                reply_to=message.id,
                auto_delete=True,
                delete_after=15
            )
            return
        
        if text == "خرید یخچال":
            if self._has_fridge(user_id):
                await send_func(
                    chat_id,
                    "❌ شما قبلاً یخچال خریداری کرده‌اید!",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=5
                )
                return
            
            if level < FRIDGE_LEVEL_REQUIRED:
                await send_func(
                    chat_id,
                    f"❌ **نیاز به سطح {FRIDGE_LEVEL_REQUIRED} داری!**\n"
                    f"📊 سطح فعلی: {level}",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            
            if user[6] < FRIDGE_PRICE:
                await send_func(
                    chat_id,
                    f"❌ **پوینت کافی نیست!**\n"
                    f"💰 نیاز: {format_number(FRIDGE_PRICE)} 🪙\n"
                    f"💰 موجودی: {format_number(user[6])} 🪙",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            
            update_user(user_id, points=int(user[6] - FRIDGE_PRICE))
            self._create_fridge(user_id)
            
            await send_func(
                chat_id,
                f"🎉 **یخچال میویی خریداری شد!** ❄️\n\n"
                f"💰 هزینه: {format_number(FRIDGE_PRICE)} 🪙\n"
                f"⭐️ سطح یخچال: 1\n"
                f"🐟 ظرفیت: {FRIDGE_BASE_CAPACITY}\n\n"
                f"📌 حالا می‌تونی با `یخچال میویی` پنل رو ببینی!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
            return
        
        if not self._has_fridge(user_id):
            if text in ["بندازش تو یخچال", "ارتقا یخچال", "پختن", "یام یام کردن", "فروش ماهی"]:
                await send_func(
                    chat_id,
                    "❌ **شما یخچال ندارید!**\n\n"
                    "📌 برای خرید یخچال، دستور `یخچال میویی` رو بزن.",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
            return
        
        if text == "یخچال میویی":
            await self._show_fridge(user_id, chat_id, message, send_func)
        elif text == "ارتقا یخچال":
            await self._upgrade_fridge(user_id, chat_id, message, send_func)
        elif text.startswith("پختن"):
            if user_id in self.cooking_tasks and not self.cooking_tasks[user_id].done():
                await send_func(
                    chat_id,
                    "⏳ **شما در حال پخت ماهی هستید!**\n"
                    "📌 لطفاً صبر کنید تا پخت فعلی تمام بشه.",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=5
                )
                return
            await self._cook_fish(user_id, chat_id, text, message, send_func)
        elif text.startswith("یام یام کردن"):
            await self._feed_pet(user_id, chat_id, text, message, send_func)
        elif text.startswith("فروش ماهی"):
            await self._sell_fish(user_id, chat_id, text, message, send_func)
    
    async def _show_fridge(self, user_id, chat_id, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        fridge = self._get_fridge(user_id)
        if not fridge:
            await send_func(
                chat_id,
                "❌ شما یخچال ندارید! اول `یخچال میویی` رو بخرید.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        username = get_user_name(user)
        level = fridge[0]
        capacity = fridge[1]
        fish_list = self._get_fridge_fish(user_id)
        
        if level < FRIDGE_MAX_LEVEL:
            upgrade_cost = FRIDGE_UPGRADE_COST.get(level + 1, 0)
        else:
            upgrade_cost = 0
        
        panel = f"❄️ **یخچال میویی {username}**\n"
        panel += "═══════════════════════\n"
        panel += f"⭐️ **سطح یخچال :** {level}\n"
        panel += f"🐟 **ظرفیت یخچال :** {len(fish_list)} / {capacity}\n"
        panel += "═══════════════════════\n\n"
        
        if not fish_list:
            panel += "📭 **یخچال خالی است!**\n"
            panel += "🔹 با `ماهی` بگیر و `بندازش تو یخچال` کن.\n"
        else:
            number_emojis = ["❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽", "❾", "❿"]
            
            for i, fish_tuple in enumerate(fish_list, 1):
                fish = self._fish_to_dict(fish_tuple)
                
                fish_type = fish.get('fish_type', 'common')
                weight = fish.get('weight', 0.0)
                value = fish.get('value', 0)
                food_value = fish.get('food_value', 0)
                is_cooked = fish.get('is_cooked', 0)
                
                if is_cooked == 1:
                    display_value = value * 10
                    display_food = food_value * 2
                    cooked_status = "پخته شده 🔥"
                else:
                    display_value = value
                    display_food = food_value
                    cooked_status = "خام"
                
                rarity_name = get_rarity_name(fish_type)
                emoji = get_fish_emoji(fish_type)
                
                num_emoji = number_emojis[i-1] if i <= len(number_emojis) else f"{i}."
                
                panel += f"{num_emoji} {emoji} {rarity_name} ({cooked_status})\n"
                try:
                    weight_float = float(weight)
                except:
                    weight_float = 0.0
                panel += f"   وزن : {weight_float:.2f} کیلو\n"
                panel += f"   ارزش : {format_number(display_value)} 🪙\n"
                panel += f"   ارزش غذایی : {display_food}\n\n"
        
        panel += "═══════════════════════\n"
        if level < FRIDGE_MAX_LEVEL:
            panel += f"💰 **هزینه ارتقا :** {format_number(upgrade_cost)} 🪙\n"
            panel += f"📌 ارتقا یخچال\n\n"
        
        if fish_list:
            panel += "📌 **دستورات:**\n"
            panel += "`پختن (شماره مدنظر)`\n"
            panel += "`یام یام کردن (شماره مدنظر)`\n"
            panel += "`فروش ماهی (شماره مدنظر)`"
        
        await send_func(chat_id, panel, reply_to=message.id, auto_delete=True, delete_after=30)
    
    async def _upgrade_fridge(self, user_id, chat_id, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        fridge = self._get_fridge(user_id)
        if not fridge:
            await send_func(
                chat_id,
                "❌ شما یخچال ندارید! اول `یخچال میویی` رو بخرید.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        level = fridge[0]
        capacity = fridge[1]
        
        if level >= FRIDGE_MAX_LEVEL:
            await send_func(
                chat_id,
                f"⭐ **یخچال شما در بالاترین سطح است!**\n"
                f"📊 سطح فعلی: {level} / {FRIDGE_MAX_LEVEL}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        cost = FRIDGE_UPGRADE_COST.get(level + 1, 0)
        
        if cost == 0:
            await send_func(
                chat_id,
                "❌ هزینه ارتقا نامشخص است!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
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
        
        new_level = level + 1
        new_capacity = FRIDGE_BASE_CAPACITY + (new_level - 1) * FRIDGE_CAPACITY_PER_LEVEL
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute(
            "UPDATE fridge SET level = ?, capacity = ? WHERE user_id = ?",
            (new_level, new_capacity, user_id)
        )
        c.execute(
            "UPDATE users SET points = ? WHERE user_id = ?",
            (int(user[6] - cost), user_id)
        )
        conn.commit()
        conn.close()
        
        await send_func(
            chat_id,
            f"❄️ **یخچال ارتقا یافت!**\n\n"
            f"⭐️ سطح جدید: {new_level}\n"
            f"🐟 ظرفیت جدید: {new_capacity}\n"
            f"💰 هزینه: {format_number(cost)} 🪙",
            reply_to=message.id,
            auto_delete=True,
            delete_after=30
        )
    
    async def _cook_fish(self, user_id, chat_id, text, message, send_func):
        fish_num = extract_number_from_text(text)
        if fish_num is None:
            await send_func(
                chat_id,
                "❌ شماره ماهی نامعتبر!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        fish_index = fish_num - 1
        fish_list = self._get_fridge_fish(user_id)
        
        if fish_index < 0 or fish_index >= len(fish_list):
            await send_func(
                chat_id,
                f"❌ ماهی شماره {fish_num} در یخچال وجود ندارد!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        fish_tuple = fish_list[fish_index]
        fish = self._fish_to_dict(fish_tuple)
        
        if fish.get('is_cooked', 0) == 1:
            await send_func(
                chat_id,
                "🔥 این ماهی قبلاً پخته شده!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        # شروع پخت در پس‌زمینه
        task = asyncio.create_task(self._cooking_process(user_id, chat_id, fish, message, send_func))
        self.cooking_tasks[user_id] = task
        
        await send_func(
            chat_id,
            f"🔥 **شروع پخت و پز میویی!**\n\n"
            f"⏳ پخت ماهی شما شروع شد...\n"
            f"📌 وقتی پخت کامل شد بهت خبر میدم!",
            reply_to=message.id,
            auto_delete=True,
            delete_after=30
        )
    
    async def _cooking_process(self, user_id, chat_id, fish, message, send_func):
        try:
            weight = fish.get('weight', 0.0)
            cook_time = int(weight / 0.01)
            if cook_time < 10:
                cook_time = 10
            if cook_time > 600:
                cook_time = 600
            
            minutes = cook_time // 60
            seconds = cook_time % 60
            time_str = f"{minutes}:{seconds:02d}" if minutes > 0 else f"{seconds} ثانیه"
            
            user = get_user(user_id)
            username = get_user_name(user)
            fish_type = fish.get('fish_type', 'common')
            rarity_name = get_rarity_name(fish_type)
            emoji = get_fish_emoji(fish_type)
            value = fish.get('value', 0)
            food_value = fish.get('food_value', 0)
            
            start_msg = (
                f"🔥 **پخت و پز میویی**\n\n"
                f"🍳 سرآشپز : {username}\n\n"
                f"‏ماهی : \n\n"
                f"⭐️ سطح : {rarity_name} 🔡\n"
                f"⚖️ وزن : {weight:.2f} کیلو\n"
                f"💰 ارزش : {format_number(value)} 🪙\n\n"
                f"🍖 ارزش غذایی : {food_value}\n\n"
                f"⌛️ زمان مورد نیاز پخت : {time_str}\n"
                f"🔥 در حال پخت..."
            )
            
            cook_msg = await send_func(chat_id, start_msg, reply_to=message.id)
            
            await asyncio.sleep(cook_time)
            
            conn = sqlite3.connect(DATABASE_FILE)
            c = conn.cursor()
            c.execute("UPDATE fridge_fish SET is_cooked = 1 WHERE id = ?", (fish.get('id'),))
            conn.commit()
            conn.close()
            
            new_value = value * 10
            new_food_value = food_value * 2
            
            done_msg = (
                f"🔥 **پخت و پز میویی**\n\n"
                f"🍳 سرآشپز : {username}\n\n"
                f"‏ماهی : \n\n"
                f"⭐️ سطح : {rarity_name} 🔡\n"
                f"⚖️ وزن : {weight:.2f} کیلو\n"
                f"💰 ارزش جدید : {format_number(new_value)} 🪙\n\n"
                f"🍖 ارزش غذایی جدید : {new_food_value}\n\n"
                f"✅ **پخت کامل شد!** 🎉"
            )
            
            await self._edit_message(chat_id, cook_msg.id, done_msg)
            
        except Exception as e:
            print(f"❌ خطا در پخت ماهی: {e}")
        finally:
            if user_id in self.cooking_tasks:
                del self.cooking_tasks[user_id]
    
    async def _feed_pet(self, user_id, chat_id, text, message, send_func):
        fish_num = extract_number_from_text(text)
        if fish_num is None:
            await send_func(
                chat_id,
                "❌ **فرمت صحیح:**\n"
                "`یام یام کردن 1` - غذا دادن به پیشی با ماهی شماره ۱",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        fish_index = fish_num - 1
        
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
        
        fish_list = self._get_fridge_fish(user_id)
        
        if fish_index < 0 or fish_index >= len(fish_list):
            await send_func(
                chat_id,
                f"❌ ماهی شماره {fish_num} در یخچال وجود ندارد!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        fish_tuple = fish_list[fish_index]
        fish = self._fish_to_dict(fish_tuple)
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM fridge_fish WHERE id = ?", (fish.get('id'),))
        conn.commit()
        conn.close()
        
        food_value = fish.get('food_value', 0)
        if fish.get('is_cooked', 0) == 1:
            food_value = food_value * 2
        
        feed_pet(user_id, food_value)
        
        fish_type = fish.get('fish_type', 'common')
        weight = fish.get('weight', 0.0)
        rarity_name = get_rarity_name(fish_type)
        emoji = get_fish_emoji(fish_type)
        cooked_text = "پخته 🔥" if fish.get('is_cooked', 0) == 1 else "خام 🐟"
        
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
    
    async def _sell_fish(self, user_id, chat_id, text, message, send_func):
        fish_num = extract_number_from_text(text)
        if fish_num is None:
            await send_func(
                chat_id,
                "❌ **فرمت صحیح:**\n"
                "`فروش ماهی 1` - فروش ماهی شماره ۱",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        fish_index = fish_num - 1
        
        fish_list = self._get_fridge_fish(user_id)
        
        if fish_index < 0 or fish_index >= len(fish_list):
            await send_func(
                chat_id,
                f"❌ ماهی شماره {fish_num} در یخچال وجود ندارد!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        fish_tuple = fish_list[fish_index]
        fish = self._fish_to_dict(fish_tuple)
        value = fish.get('value', 0)
        
        if fish.get('is_cooked', 0) == 1:
            value = value * 10
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM fridge_fish WHERE id = ?", (fish.get('id'),))
        conn.commit()
        conn.close()
        
        user = get_user(user_id)
        update_user(user_id, points=int(user[6] + value))
        
        fish_type = fish.get('fish_type', 'common')
        weight = fish.get('weight', 0.0)
        rarity_name = get_rarity_name(fish_type)
        emoji = get_fish_emoji(fish_type)
        
        await send_func(
            chat_id,
            f"💰 **ماهی فروخته شد!**\n\n"
            f"{emoji} **نوع:** {rarity_name}\n"
            f"⚖️ **وزن:** {float(weight):.2f} کیلو\n"
            f"💰 **فروخته شد به:** {format_number(value)} 🪙\n"
            f"📊 **موجودی جدید:** {format_number(user[6] + value)} 🪙",
            reply_to=message.id,
            auto_delete=True,
            delete_after=30
        )
    
    def add_fish_to_fridge(self, user_id, fish_data):
        if not self._has_fridge(user_id):
            return False, "❌ **شما یخچال ندارید!**\n\n📌 اول `یخچال میویی` رو بخرید."
        
        fridge = self._get_fridge(user_id)
        if not fridge:
            return False, "❌ **شما یخچال ندارید!**"
        
        capacity = fridge[1]
        current_fish = self._get_fridge_fish(user_id)
        
        if len(current_fish) >= capacity:
            return False, f"❌ **ظرفیت یخچال پر است!**\n\n📊 ظرفیت: {capacity}\n🐟 تعداد ماهی‌ها: {len(current_fish)}"
        
        fish_type = fish_data["type"]
        for fish in current_fish:
            if fish[1] == fish_type:
                rarity_name = get_rarity_name(fish_type)
                return False, f"❌ **شما قبلاً یک ماهی {rarity_name} در یخچال دارید!**\n\n🦀 هر نوع ماهی رو فقط یک بار میتونی ذخیره کنی."
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute(
            """INSERT INTO fridge_fish 
               (user_id, fish_type, weight, value, food_value, is_cooked, stored_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                fish_data["type"],
                float(fish_data["weight"]),
                int(fish_data["value"]),
                int(fish_data.get("food_value", 1)),
                0,
                datetime.now().isoformat()
            )
        )
        conn.commit()
        conn.close()
        
        return True, "✅ **ماهی در یخچال ذخیره شد!** 🐟❄️"
    
    async def _edit_message(self, chat_id, msg_id, new_text):
        try:
            if self.client:
                await self.client.edit_message(chat_id, msg_id, new_text)
                print(f"✅ پیام {msg_id} ویرایش شد!")
        except Exception as e:
            print(f"❌ خطا در ویرایش پیام {msg_id}: {e}")