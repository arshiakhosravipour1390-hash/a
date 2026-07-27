# handlers/casino_handler.py
import random
import re
import asyncio
from datetime import datetime, timedelta
from database import *
from utils import *
from config import CASINO_MIN_BET, CASINO_MAX_BET, CASINO_COOLDOWN

class CasinoHandler:
    def __init__(self):
        self.cooldowns = {}
        self.client = None
        self.active_games = {}
    
    def set_client(self, client):
        self.client = client
    
    # ============================================================
    # منوی اصلی کازینو
    # ============================================================
    
    async def handle_main(self, user_id, chat_id, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        level = safe_int(user[4], 1)
        
        text = "🎰 **کازینو میویی** 🎰\n\n"
        
        if level >= 4:
            text += "🎲 **تاس** (سطح ۴)\n"
            text += "`تاس زوج` - شرط روی زوج\n"
            text += "`تاس فرد` - شرط روی فرد\n"
            text += "`تاس عدد` - شرط روی عدد دقیق\n"
            text += "مثال: `تاس زوج 1000`\n\n"
        else:
            text += f"🎲 **تاس** 🔒 سطح {4 - level} دیگه\n"
            text += "🐣 تو هنوز جوجه‌ای! برو میو کن!\n\n"
        
        if level >= 5:
            text += "🎡 **گردونه شانس** (سطح ۵)\n"
            text += "`گردونه` - چرخاندن گردونه\n"
            text += "مثال: `گردونه 1000`\n\n"
        else:
            text += f"🎡 **گردونه شانس** 🔒 سطح {5 - level} دیگه\n"
            text += "😾 هنوز که چیزی نشدی!\n\n"
        
        if level >= 6:
            text += "💎 **معدن الماس** (سطح ۶)\n"
            text += "`معدن` - ماجراجویی در معدن\n"
            text += "مثال: `معدن 1000`\n\n"
        else:
            text += f"💎 **معدن الماس** 🔒 سطح {6 - level} دیگه\n"
            text += "🐱 بیا بزرگ شو بعد بیا تو معدن!\n\n"
        
        text += f"💰 حداقل شرط: {format_number(CASINO_MIN_BET)} 🪙\n"
        text += f"💰 حداکثر شرط: {format_number(CASINO_MAX_BET)} 🪙\n"
        text += f"⏳ کولداون: {CASINO_COOLDOWN//60} دقیقه\n\n"
        text += "💡 شانس خودت رو امتحان کن!"
        
        await send_func(chat_id, text, reply_to=message.id, auto_delete=True, delete_after=30)
    
    # ============================================================
    # بازی تاس - سطح ۴
    # ============================================================
    
    async def handle_dice(self, user_id, chat_id, text, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        level = safe_int(user[4], 1)
        
        if level < 4:
            await send_func(
                chat_id,
                "🐣 **تو هنوز یه جوجه پیشی نوبی!**\n"
                f"🎯 سطح مورد نیاز: ۴\n"
                f"💪 {4 - level} سطح دیگه باید میو کنی!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if not self._check_cooldown(user_id):
            remaining = self._get_remaining_time(user_id)
            cooldown_messages = [
                f"😿 **یکم به جیبت استراحت بده!**\n⏳ {remaining} دیگه می‌تونی بازی کنی.",
                f"🐱 **صبر کن میویی!** جیبت هنوز خنک نشده!\n⏳ {remaining} دیگه فرصت داری.",
                f"💸 **همینقدر قمار؟** برو یه چایی بخور!\n⏳ {remaining} دیگه می‌تونی برگردی.",
                f"😾 **نذار کیفیت خالی بشه!**\n⏳ {remaining} صبر کن تا دوباره پر بشه.",
                f"🐈 **بیا یه نفسی تازه کن!**\n⏳ {remaining} دیگه شانست رو امتحان کن."
            ]
            await send_func(
                chat_id,
                random.choice(cooldown_messages),
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        parts = text.split()
        if len(parts) < 3:
            await send_func(
                chat_id,
                "❌ **فرمت صحیح:**\n`تاس زوج 1000`\n`تاس فرد 1000`\n`تاس 3 1000`",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        prediction = parts[1].lower()
        amount = self._extract_amount(parts[2])
        
        if not amount or amount < CASINO_MIN_BET or amount > CASINO_MAX_BET:
            await send_func(
                chat_id,
                f"❌ **مبلغ نامعتبر!**\n"
                f"💰 حداقل: {format_number(CASINO_MIN_BET)} 🪙\n"
                f"💰 حداکثر: {format_number(CASINO_MAX_BET)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        points = safe_int(user[6], 0)
        if points < amount:
            await send_func(
                chat_id,
                f"❌ **پوینت کافی نیست!**\n💰 موجودی: {format_number(points)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        result = self._dice_game(amount, prediction)
        if result is None:
            await send_func(
                chat_id,
                "❌ **پیش‌بینی نامعتبر!**\nگزینه‌ها: `زوج`, `فرد`, `1` تا `6`",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        self._set_cooldown(user_id)
        
        dice_emojis = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]
        
        if result["win"]:
            win_amount = result["result"] - amount
            update_user(user_id, points=int(points + win_amount))
            await send_func(
                chat_id,
                f"🎲 **تاس ریخته شد!** {dice_emojis[result['roll']-1]}\n\n"
                f"🎯 عدد: {result['roll']}\n"
                f"✅ **برد!** +{format_number(win_amount)} 🪙\n"
                f"💰 مجموع: {format_number(result['result'])} 🪙\n"
                f"📊 موجودی جدید: {format_number(points + win_amount)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
        else:
            update_user(user_id, points=int(points - amount))
            await send_func(
                chat_id,
                f"🎲 **تاس ریخته شد!** {dice_emojis[result['roll']-1]}\n\n"
                f"🎯 عدد: {result['roll']}\n"
                f"❌ **باخت!** -{format_number(amount)} 🪙\n"
                f"📊 موجودی جدید: {format_number(points - amount)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
    
    # ============================================================
    # بازی گردونه شانس (اسلات ماشین) - سطح ۵
    # ============================================================
    
    async def handle_spin(self, user_id, chat_id, text, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        level = safe_int(user[4], 1)
        
        if level < 5:
            await send_func(
                chat_id,
                "😾 **تو که هنوز به جایی نرسیدی!**\n"
                f"🎯 سطح مورد نیاز: ۵\n"
                f"💪 {5 - level} سطح دیگه باید میو کنی!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if not self._check_cooldown(user_id):
            remaining = self._get_remaining_time(user_id)
            cooldown_messages = [
                f"😿 **یکم به جیبت استراحت بده!**\n⏳ {remaining} دیگه می‌تونی بازی کنی.",
                f"🐱 **صبر کن میویی!** جیبت هنوز خنک نشده!\n⏳ {remaining} دیگه فرصت داری.",
                f"💸 **همینقدر قمار؟** برو یه چایی بخور!\n⏳ {remaining} دیگه می‌تونی برگردی.",
                f"😾 **نذار کیفیت خالی بشه!**\n⏳ {remaining} صبر کن تا دوباره پر بشه.",
                f"🐈 **بیا یه نفسی تازه کن!**\n⏳ {remaining} دیگه شانست رو امتحان کن."
            ]
            await send_func(
                chat_id,
                random.choice(cooldown_messages),
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        parts = text.split()
        if len(parts) < 2:
            await send_func(
                chat_id,
                "❌ **فرمت صحیح:**\n`گردونه 1000`",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        amount = self._extract_amount(parts[1])
        if not amount or amount < CASINO_MIN_BET or amount > CASINO_MAX_BET:
            await send_func(
                chat_id,
                f"❌ **مبلغ نامعتبر!**\n"
                f"💰 حداقل: {format_number(CASINO_MIN_BET)} 🪙\n"
                f"💰 حداکثر: {format_number(CASINO_MAX_BET)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        points = safe_int(user[6], 0)
        if points < amount:
            await send_func(
                chat_id,
                f"❌ **پوینت کافی نیست!**\n💰 موجودی: {format_number(points)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        # اسلات ماشین
        slot_icons = ["7️⃣", "🍋", "🫐", "🍫"]
        slot_weights = [0.20, 0.25, 0.25, 0.30]
        row = random.choices(slot_icons, weights=slot_weights, k=3)
        
        multiplier = 0
        if "🍫" in row:
            multiplier = 0
        else:
            if row[0] == row[1] == row[2]:
                if row[0] == "7️⃣":
                    multiplier = 3
                elif row[0] in ["🍋", "🫐"]:
                    multiplier = 2
            if multiplier == 0:
                if row[0] == row[1] or row[1] == row[2] or row[0] == row[2]:
                    if "7️⃣" in row:
                        multiplier = 2
                    elif "🍋" in row or "🫐" in row:
                        multiplier = 1.5
        
        result_amount = int(amount * multiplier)
        self._set_cooldown(user_id)
        
        slot_display = (
            f"🎰 **گردونه شانس** 🎰\n\n"
            f"┌──────┬──────┬──────┐\n"
            f"│  {row[0]}   │  {row[1]}   │  {row[2]}   │\n"
            f"└──────┴──────┴──────┘\n\n"
        )
        
        items_desc = {
            "7️⃣": "هفت ⭐",
            "🍋": "لیمو",
            "🫐": "بلوبری",
            "🍫": "شکلات ❌ (بار)"
        }
        
        items_text = f"🎯 **ایتم‌ها:** {items_desc.get(row[0], row[0])} | {items_desc.get(row[1], row[1])} | {items_desc.get(row[2], row[2])}\n"
        
        if "🍫" in row:
            update_user(user_id, points=int(points - amount))
            bache_msg = "💀 **سه تا شکلات!** بدترین حالت ممکن! کل پولتو باختی!" if row[0] == row[1] == row[2] == "🍫" else "😿 **شکلات اومد!** باخت کامل! کل پولتو باختی!"
            await send_func(
                chat_id,
                f"{slot_display}{items_text}🎯 **ضریب: ۰x**\n❌ **باخت!** -{format_number(amount)} 🪙\n📊 موجودی جدید: {format_number(points - amount)} 🪙\n\n{bache_msg}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
            return
        
        if multiplier > 0:
            win_amount = result_amount - amount
            update_user(user_id, points=int(points + win_amount))
            
            if multiplier >= 3:
                result_msg = "🎉 **جکپات!** سه تا هفت! بهترین حالت ممکن!"
            elif multiplier >= 2:
                result_msg = "😍 **برد خوب!** سه تا لیمو یا بلوبری!"
            elif multiplier >= 1.5:
                result_msg = "🙂 **برد معمولی!** دو تا یکسان!"
            else:
                result_msg = "😊 **برد کوچک!**"
            
            await send_func(
                chat_id,
                f"{slot_display}{items_text}🎯 **ضریب: {multiplier}x**\n✅ **برد!** +{format_number(win_amount)} 🪙\n💰 مجموع: {format_number(result_amount)} 🪙\n📊 موجودی جدید: {format_number(points + win_amount)} 🪙\n\n{result_msg}",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
        else:
            update_user(user_id, points=int(points - amount))
            await send_func(
                chat_id,
                f"{slot_display}{items_text}🎯 **ضریب: ۰x**\n❌ **باخت!** -{format_number(amount)} 🪙\n📊 موجودی جدید: {format_number(points - amount)} 🪙\n\n😿 هیچ ترکیبی نیومد! دفعه بعد شانس بیشتر!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
    
    # ============================================================
    # ✅ بازی معدن الماس - سطح ۶ (با حذف خودکار بعد از پایان)
    # ============================================================
    
    async def handle_mine(self, user_id, chat_id, text, message, send_func):
        user = get_user(user_id)
        if not user:
            return
        
        level = safe_int(user[4], 1)
        
        if level < 6:
            await send_func(
                chat_id,
                "🐱 **بیا بزرگ شو بعد بیا تو معدن!**\n"
                f"🎯 سطح مورد نیاز: ۶\n"
                f"💪 {6 - level} سطح دیگه باید میو کنی!\n"
                f"💎 اینجا جای بچه‌ها نیست!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if not self._check_cooldown(user_id):
            remaining = self._get_remaining_time(user_id)
            cooldown_messages = [
                f"😿 **یکم به جیبت استراحت بده!**\n⏳ {remaining} دیگه می‌تونی بازی کنی.",
                f"🐱 **صبر کن میویی!** جیبت هنوز خنک نشده!\n⏳ {remaining} دیگه فرصت داری.",
                f"💸 **همینقدر قمار؟** برو یه چایی بخور!\n⏳ {remaining} دیگه می‌تونی برگردی.",
                f"😾 **نذار کیفیت خالی بشه!**\n⏳ {remaining} صبر کن تا دوباره پر بشه.",
                f"🐈 **بیا یه نفسی تازه کن!**\n⏳ {remaining} دیگه شانست رو امتحان کن."
            ]
            await send_func(
                chat_id,
                random.choice(cooldown_messages),
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        parts = text.split()
        if len(parts) < 2:
            await send_func(
                chat_id,
                "❌ **فرمت صحیح:**\n`معدن 1000` - شروع بازی\n\n"
                "📌 بعد از شروع، با شماره خونه‌ها رو انتخاب کن:\n"
                "`1` تا `9` - انتخاب خونه\n"
                "`بس کن` - پایان بازی و دریافت پول",
                reply_to=message.id,
                auto_delete=True,
                delete_after=15
            )
            return
        
        amount = self._extract_amount(parts[1])
        if not amount or amount < CASINO_MIN_BET or amount > CASINO_MAX_BET:
            await send_func(
                chat_id,
                f"❌ **مبلغ نامعتبر!**\n"
                f"💰 حداقل: {format_number(CASINO_MIN_BET)} 🪙\n"
                f"💰 حداکثر: {format_number(CASINO_MAX_BET)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        points = safe_int(user[6], 0)
        if points < amount:
            await send_func(
                chat_id,
                f"❌ **پوینت کافی نیست!**\n💰 موجودی: {format_number(points)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        cells = ["💎"] * 8 + ["💣"] * 1
        random.shuffle(cells)
        
        self.active_games[user_id] = {
            "cells": cells,
            "amount": amount,
            "diamonds": 0,
            "bomb_found": False,
            "finished": False,
            "opened": [],
            "msg_id": None,
            "chat_id": chat_id
        }
        
        msg = await send_func(
            chat_id,
            self._build_mine_message(user_id),
            reply_to=message.id
        )
        
        if msg:
            self.active_games[user_id]["msg_id"] = msg.id
    
    async def handle_mine_action(self, user_id, chat_id, text, message, send_func):
        if user_id not in self.active_games:
            await send_func(
                chat_id,
                "❌ بازی فعالی نداری! اول `معدن` رو شروع کن.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        game = self.active_games[user_id]
        
        if game["finished"]:
            del self.active_games[user_id]
            await send_func(
                chat_id,
                "❌ این بازی تموم شده! برای بازی جدید `معدن` رو بزن.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if text == "بس کن":
            game["finished"] = True
            diamonds = game["diamonds"]
            
            percentage = diamonds * 25
            win_amount = int(game["amount"] * percentage / 100)
            
            user = get_user(user_id)
            points = safe_int(user[6], 0)
            
            del self.active_games[user_id]
            self._set_cooldown(user_id)
            
            if win_amount > game["amount"]:
                profit = win_amount - game["amount"]
                update_user(user_id, points=int(points + profit))
                result_text = f"✅ **برد!** +{format_number(profit)} 🪙"
                status_emoji = "🌟"
            elif win_amount == game["amount"]:
                result_text = f"🔄 **برگشت پول!** پولت برگشت."
                status_emoji = "🤝"
            else:
                loss = game["amount"] - win_amount
                update_user(user_id, points=int(points - loss))
                result_text = f"❌ **ضرر!** -{format_number(loss)} 🪙"
                status_emoji = "😿"
            
            await self._edit_message(
                chat_id,
                game["msg_id"],
                f"💎 **معدن الماس - پایان بازی!** 💎\n\n"
                f"⛏️ الماس‌های پیدا شده: {diamonds}\n"
                f"💰 درصد برگشتی: {percentage}%\n"
                f"💰 مبلغ برگشتی: {format_number(win_amount)} 🪙\n"
                f"{result_text}\n"
                f"📊 موجودی جدید: {format_number(points + (win_amount - game['amount']))} 🪙\n\n"
                f"{status_emoji} بازی تموم شد!"
            )
            
            # ✅ بعد از 15 ثانیه پیام معدن رو حذف کن
            await asyncio.sleep(15)
            try:
                await self.client.delete_messages(chat_id, [game["msg_id"]])
                print(f"🗑️ پیام معدن {game['msg_id']} حذف شد!")
            except Exception as e:
                print(f"❌ خطا در حذف پیام معدن: {e}")
            return
        
        try:
            cell_index = int(text) - 1
        except ValueError:
            await send_func(
                chat_id,
                "❌ عدد معتبر وارد کن (۱ تا ۹) یا `بس کن` بزن!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        if cell_index < 0 or cell_index >= 9:
            await send_func(
                chat_id,
                "❌ عدد باید بین ۱ تا ۹ باشه!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        if cell_index in game["opened"]:
            await send_func(
                chat_id,
                f"❌ خونه {text} قبلاً باز شده! عدد دیگه‌ای انتخاب کن.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        game["opened"].append(cell_index)
        cell = game["cells"][cell_index]
        
        if cell == "💣":
            game["finished"] = True
            game["bomb_found"] = True
            
            user = get_user(user_id)
            points = safe_int(user[6], 0)
            loss = game["amount"]
            update_user(user_id, points=int(points - loss))
            
            del self.active_games[user_id]
            self._set_cooldown(user_id)
            
            await self._edit_message(
                chat_id,
                game["msg_id"],
                f"💥 **به بمب خوردی!** 💥\n\n"
                f"⛏️ الماس‌های پیدا شده: {game['diamonds']}\n"
                f"💣 **بوم!**\n"
                f"❌ **باخت کامل!** -{format_number(loss)} 🪙\n"
                f"📊 موجودی جدید: {format_number(points - loss)} 🪙\n\n"
                f"😿 معدن امروز امن نبود!"
            )
            
            # ✅ بعد از 15 ثانیه پیام معدن رو حذف کن
            await asyncio.sleep(15)
            try:
                await self.client.delete_messages(chat_id, [game["msg_id"]])
                print(f"🗑️ پیام معدن {game['msg_id']} حذف شد!")
            except Exception as e:
                print(f"❌ خطا در حذف پیام معدن: {e}")
            return
        
        game["diamonds"] += 1
        
        if game["diamonds"] == 8:
            game["finished"] = True
            
            win_amount = int(game["amount"] * 2)
            user = get_user(user_id)
            points = safe_int(user[6], 0)
            profit = win_amount - game["amount"]
            update_user(user_id, points=int(points + profit))
            
            del self.active_games[user_id]
            self._set_cooldown(user_id)
            
            await self._edit_message(
                chat_id,
                game["msg_id"],
                f"💎 **همه الماس‌ها رو پیدا کردی!** 💎\n\n"
                f"⛏️ الماس‌های پیدا شده: ۸\n"
                f"💰 درصد برگشتی: ۲۰۰%\n"
                f"✅ **برد بزرگ!** +{format_number(profit)} 🪙\n"
                f"💰 مجموع: {format_number(win_amount)} 🪙\n"
                f"📊 موجودی جدید: {format_number(points + profit)} 🪙\n\n"
                f"🌟 تو یک معدنچی افسانه‌ای هستی!"
            )
            
            # ✅ بعد از 15 ثانیه پیام معدن رو حذف کن
            await asyncio.sleep(15)
            try:
                await self.client.delete_messages(chat_id, [game["msg_id"]])
                print(f"🗑️ پیام معدن {game['msg_id']} حذف شد!")
            except Exception as e:
                print(f"❌ خطا در حذف پیام معدن: {e}")
            return
        
        await self._edit_message(chat_id, game["msg_id"], self._build_mine_message(user_id))
    
    def _build_mine_message(self, user_id):
        game = self.active_games[user_id]
        cells = game["cells"]
        opened = game["opened"]
        diamonds = game["diamonds"]
        
        display = []
        for i in range(9):
            if i in opened:
                display.append(cells[i])
            else:
                display.append("❓")
        
        percentage = diamonds * 25
        current_win = int(game["amount"] * percentage / 100)
        
        return (
            f"💎 **معدن الماس!** 💎\n\n"
            f"💰 مبلغ شرط: {format_number(game['amount'])} 🪙\n"
            f"⛏️ الماس‌های پیدا شده: {diamonds}\n"
            f"💎 هر الماس = ۲۵% پول برگشتی\n\n"
            f"┌─────┬─────┬─────┐\n"
            f"│  {display[0]}  │  {display[1]}  │  {display[2]}  │\n"
            f"├─────┼─────┼─────┤\n"
            f"│  {display[3]}  │  {display[4]}  │  {display[5]}  │\n"
            f"├─────┼─────┼─────┤\n"
            f"│  {display[6]}  │  {display[7]}  │  {display[8]}  │\n"
            f"└─────┴─────┴─────┘\n\n"
            f"💰 مبلغ فعلی: {format_number(current_win)} 🪙 ({percentage}%)\n"
            f"📌 {4 - diamonds if diamonds < 4 else 0} الماس دیگه تا برگشت پول!\n\n"
            f"📌 شماره خونه رو انتخاب کن (۱ تا ۹):\n"
            f"`1` `2` `3` `4` `5` `6` `7` `8` `9`\n"
            f"📌 یا `بس کن` برای پایان بازی"
        )
    
    # ============================================================
    # توابع بازی
    # ============================================================
    
    def _dice_game(self, bet_amount, prediction):
        roll = random.randint(1, 6)
        win = False
        
        if prediction == "زوج":
            win = roll % 2 == 0
            multiplier = 1.5
        elif prediction == "فرد":
            win = roll % 2 != 0
            multiplier = 1.5
        else:
            try:
                num = int(prediction)
                if 1 <= num <= 6:
                    win = roll == num
                    multiplier = 2.5
                else:
                    return None
            except:
                return None
        
        if win:
            result = int(bet_amount * multiplier)
        else:
            result = 0
        
        return {"roll": roll, "win": win, "result": result}
    
    # ============================================================
    # توابع کمکی
    # ============================================================
    
    def _extract_amount(self, text):
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
        return (datetime.now() - self.cooldowns[user_id]).seconds >= CASINO_COOLDOWN
    
    def _set_cooldown(self, user_id):
        self.cooldowns[user_id] = datetime.now()
    
    def _get_remaining_time(self, user_id):
        if user_id not in self.cooldowns:
            return "اکنون"
        remaining = CASINO_COOLDOWN - (datetime.now() - self.cooldowns[user_id]).seconds
        if remaining <= 0:
            return "اکنون"
        minutes = remaining // 60
        seconds = remaining % 60
        if minutes > 0:
            return f"{minutes} دقیقه و {seconds} ثانیه"
        return f"{seconds} ثانیه"
    
    async def _edit_message(self, chat_id, msg_id, new_text):
        try:
            if self.client:
                await self.client.edit_message(chat_id, msg_id, new_text)
                print(f"✅ پیام معدن {msg_id} ویرایش شد!")
        except Exception as e:
            print(f"❌ خطا در ویرایش پیام معدن: {e}")