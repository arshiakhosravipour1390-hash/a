# handlers/bank_handler.py
import re
import sqlite3
import random
from datetime import datetime, timedelta
from database import *
from utils import *
from config import *

class BankHandler:
    def __init__(self):
        self.client = None
        self.change_cooldowns = {}
    
    def set_client(self, client):
        self.client = client
    
    async def handle_main(self, user_id, chat_id, message, send_func):
        try:
            user = get_user(user_id)
            if not user:
                create_user(user_id, "", "")
                user = get_user(user_id)
                if not user:
                    await send_func(chat_id, "❌ خطا در ایجاد کاربر!")
                    return
            
            level = safe_int(user[4], 1)
            bank = get_bank(user_id)
            username = get_user_name(user)
            
            if not bank:
                intro_text = (
                    f"🌘 در قلب پر هیاهوی شهر پیشی، ساختمانی باشکوه با درهای طلایی وجود داره…\n"
                    f"جایی که ثروتت رو میتونی از خطرها دور نگه داری و حتی بذاری خودش رشد کنه!\n\n"
                    f"🏦 **به «بانک میویی» خوش اومدی.**\n\n"
                )
                
                if level < 4:
                    await send_func(
                        chat_id,
                        intro_text +
                        f"✨ اگر میخوای وارد دنیای حرفه‌ای‌های شهر بشی، کافیه بگی: `بانک میویی`\n\n"
                        f"- ❗️ **برای افتتاح حساب، باید حداقل سطح ۴ باشی.**\n"
                        f"- فقط پیشی‌های با تجربه اجازه ورود به سیستم بانکی رو دارن!\n"
                        f"- 📊 سطح فعلی تو: **{level}**\n"
                        f"- 📈 {4 - level} سطح دیگه باید میو کنی!\n\n"
                        f"💡 بیشتر میو کن تا به سطح ۴ برسی! 🐱",
                        reply_to=message.id,
                        auto_delete=True,
                        delete_after=10
                    )
                    return
                
                if user[6] < BANK_OPEN_PRICE:
                    await send_func(
                        chat_id,
                        intro_text +
                        f"💰 **پوینت کافی نیست!**\n\n"
                        f"- 💰 هزینه افتتاح حساب: **{format_number(BANK_OPEN_PRICE)} 🪙**\n"
                        f"- 💰 موجودی شما: **{format_number(user[6])} 🪙**\n"
                        f"- 📊 کمبود: **{format_number(BANK_OPEN_PRICE - user[6])} 🪙**\n\n"
                        f"💡 بیشتر میو کن تا پوینت جمع کنی! 🐱",
                        reply_to=message.id,
                        auto_delete=True,
                        delete_after=15
                    )
                    return
                
                success = open_bank(user_id)
                if success:
                    bank = get_bank(user_id)
                    if bank and len(bank) > 2 and bank[2]:
                        await send_func(
                            chat_id,
                            f"🎉 **حساب بانکی افتتاح شد!** 🏦\n\n"
                            f"🌘 در قلب پر هیاهوی شهر پیشی، ساختمانی باشکوه با درهای طلایی وجود داره…\n"
                            f"جایی که ثروتت رو میتونی از خطرها دور نگه داری و حتی بذاری خودش رشد کنه!\n\n"
                            f"👤 **به نام:** {username}\n"
                            f"💳 **شماره حساب:** `{bank[2]}`\n"
                            f"💰 **هزینه:** {format_number(BANK_OPEN_PRICE)} 🪙\n"
                            f"📈 **سود روزانه:** {BANK_INTEREST_RATE*100}%\n\n"
                            f"📌 دوباره `بانک میویی` بزن تا پنل رو ببینی.",
                            reply_to=message.id,
                            auto_delete=True,
                            delete_after=30
                        )
                    else:
                        await send_func(chat_id, "❌ خطا در افتتاح حساب! دوباره تلاش کن.")
                else:
                    await send_func(chat_id, "❌ خطا در افتتاح حساب! دوباره تلاش کن.")
                return
            
            if can_get_interest(user_id):
                interest = calculate_interest(user_id)
                if interest > 0:
                    await send_func(
                        chat_id,
                        f"🏦 سود بانکی تعلق گرفت!\n"
                        f"➕ {format_number(interest)} 🪙 به حسابت اضافه شد.",
                        reply_to=message.id,
                        auto_delete=True,
                        delete_after=10
                    )
                    bank = get_bank(user_id)
            
            account_number = bank[2] if bank and len(bank) > 2 and bank[2] else "ندارد"
            balance = safe_int(bank[3]) if bank and len(bank) > 3 else 0
            
            interest_amount = int(balance * BANK_INTEREST_RATE)
            if interest_amount > BANK_MAX_INTEREST:
                interest_amount = BANK_MAX_INTEREST
            
            panel = (
                f"🏦 **بانک میویی** 🏦\n\n"
                f"👤 **به نام :** {username}\n"
                f"💳 **شماره حساب :** `{account_number}`\n\n"
                f"💰 **موجودی حساب :** {format_number(balance)} 🪙\n\n"
                f"🤑 **سود بانکی**\n"
                f"- 🛍 درصد سود : {BANK_INTEREST_RATE*100}%\n"
                f"- 📥 مبلغ واریزی : {format_number(interest_amount)} 🪙\n\n"
                f"❗️ **برای مدیریت حساب بانکی از گزینه های زیر استفاده کنید** ⬇️\n\n"
                f"📌 **دستورات:**\n"
                f"`واریز 1000` - واریز به بانک\n"
                f"`برداشت 1000` - برداشت از بانک\n"
                f"`کارت به کارت 1000` - انتقال بانکی (با ریپلای روی کاربر)\n"
                f"`تغییر شماره حساب` - تغییر شماره حساب (هزینه: ۱,۲۵۰ 🪙)"
            )
            
            await send_func(chat_id, panel, reply_to=message.id, auto_delete=True, delete_after=30)
            
        except Exception as e:
            print(f"❌ خطا در handle_main: {e}")
            import traceback
            traceback.print_exc()
            await send_func(chat_id, f"❌ خطا: {str(e)}")
    
    async def handle_deposit(self, user_id, chat_id, text, message, send_func):
        bank = get_bank(user_id)
        if not bank:
            await send_func(
                chat_id,
                "❌ اول باید `بانک میویی` رو باز کنی!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        amount = self._extract_amount(text)
        if not amount or amount <= 0:
            await send_func(
                chat_id,
                "❌ **مبلغ نامعتبر!**\n\n"
                "📌 **مثال‌های درست:**\n"
                "`واریز 1000` - برای واریز ۱,۰۰۰ 🪙\n"
                "`واریز 5k` - برای واریز ۵,۰۰۰ 🪙\n"
                "`واریز ۱۰۰۰` - برای واریز ۱,۰۰۰ 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        user = get_user(user_id)
        if safe_int(user[6]) < amount:
            await send_func(
                chat_id,
                f"❌ **پوینت کافی نیست!**\n\n"
                f"💰 نیاز: {format_number(amount)} 🪙\n"
                f"💰 موجودی کیف: {format_number(user[6])} 🪙\n"
                f"📊 کمبود: {format_number(amount - user[6])} 🪙\n\n"
                f"💡 بیشتر میو کن تا پوینت جمع کنی!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if deposit_bank(user_id, amount):
            bank = get_bank(user_id)
            await send_func(
                chat_id,
                f"✅ **واریز موفق!** 🏦\n\n"
                f"💰 مبلغ: {format_number(amount)} 🪙\n"
                f"📊 موجودی بانک: {format_number(bank[3])} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
        else:
            await send_func(
                chat_id,
                "❌ خطا در واریز.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
    
    async def handle_withdraw(self, user_id, chat_id, text, message, send_func):
        bank = get_bank(user_id)
        if not bank:
            await send_func(
                chat_id,
                "❌ اول باید `بانک میویی` رو باز کنی!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        amount = self._extract_amount(text)
        if not amount or amount <= 0:
            await send_func(
                chat_id,
                "❌ **مبلغ نامعتبر!**\n\n"
                "📌 **مثال‌های درست:**\n"
                "`برداشت 1000` - برای برداشت ۱,۰۰۰ 🪙\n"
                "`برداشت 5k` - برای برداشت ۵,۰۰۰ 🪙\n"
                "`برداشت ۱۰۰۰` - برای برداشت ۱,۰۰۰ 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if safe_int(bank[3]) < amount:
            await send_func(
                chat_id,
                f"❌ **موجودی بانک کافی نیست!**\n\n"
                f"💰 نیاز: {format_number(amount)} 🪙\n"
                f"💰 موجودی بانک: {format_number(bank[3])} 🪙\n"
                f"📊 کمبود: {format_number(amount - bank[3])} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if withdraw_bank(user_id, amount):
            user = get_user(user_id)
            await send_func(
                chat_id,
                f"✅ **برداشت موفق!** 🏦\n\n"
                f"💰 مبلغ: {format_number(amount)} 🪙\n"
                f"📊 موجودی کیف: {format_number(user[6])} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=30
            )
        else:
            await send_func(
                chat_id,
                "❌ خطا در برداشت.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
    
    async def handle_transfer(self, user_id, chat_id, text, message, send_func):
        bank = get_bank(user_id)
        if not bank:
            await send_func(
                chat_id,
                f"❌ **شما حساب بانکی ندارید!**\n\n"
                f"💡 برای استفاده از کارت به کارت، اول باید حساب بانکی باز کنی:\n"
                f"📌 دستور `بانک میویی` رو بزن و حساب باز کن.\n"
                f"💰 هزینه افتتاح حساب: {format_number(BANK_OPEN_PRICE)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        parts = text.split()
        if len(parts) < 3:
            await send_func(
                chat_id,
                "❌ **فرمت دستور اشتباه!**\n\n"
                "📌 **فرمت صحیح:**\n"
                "`کارت به کارت 1000` (با ریپلای روی کاربر)\n\n"
                "💡 **مثال:**\n"
                "روی پیام کاربر ریپلای کن و بنویس: `کارت به کارت 1000`",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        amount = self._extract_amount(text)
        
        if not amount or amount <= 0:
            await send_func(
                chat_id,
                "❌ **مبلغ نامعتبر!**\n\n"
                "📌 **مثال‌های درست:**\n"
                "`کارت به کارت 1000` - برای انتقال ۱,۰۰۰ 🪙\n"
                "`کارت به کارت 5k` - برای انتقال ۵,۰۰۰ 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        target_id = None
        
        if hasattr(message, 'reply_to_msg_id') and message.reply_to_msg_id:
            try:
                replied = await self.client.get_messages(message.peer_id, ids=message.reply_to_msg_id)
                if replied:
                    if isinstance(replied, list) and len(replied) > 0:
                        target_id = replied[0].sender_id
                    else:
                        target_id = replied.sender_id
            except Exception as e:
                print(f"⚠️ خطا در دریافت ریپلای: {e}")
        
        if not target_id:
            await send_func(
                chat_id,
                "❌ **روی پیام کاربر ریپلای نکردی!**\n\n"
                "📌 **مراحل درست:**\n"
                "1️⃣ روی پیام کاربری که میخوای بهش پول بدی **ریپلای** کن\n"
                "2️⃣ سپس بنویس: `کارت به کارت 1000`",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        if target_id == user_id:
            await send_func(
                chat_id,
                "❌ **نمی‌تونی به خودت انتقال بدی!**\n\n"
                "💡 برای انتقال به خودت، نیازی به کارت به کارت نیست.\n"
                "📌 می‌تونی از `واریز` استفاده کنی.",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        target_bank = get_bank(target_id)
        if not target_bank:
            target_user = get_user(target_id)
            target_name = get_user_name(target_user) if target_user else "کاربر ناشناس"
            await send_func(
                chat_id,
                f"❌ **{target_name} حساب بانکی ندارد!**\n\n"
                f"💡 به {target_name} بگو `بانک میویی` رو بزنه تا حساب باز کنه.\n"
                f"💰 هزینه افتتاح حساب: {format_number(BANK_OPEN_PRICE)} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        fee = int(amount * BANK_TRANSFER_FEE)
        if fee < BANK_MIN_FEE:
            fee = BANK_MIN_FEE
        elif fee > BANK_MAX_FEE:
            fee = BANK_MAX_FEE
        
        total = amount + fee
        
        if safe_int(bank[3]) < total:
            await send_func(
                chat_id,
                f"❌ **موجودی حساب کافی نیست!**\n\n"
                f"💰 موجودی شما: {format_number(bank[3])} 🪙\n"
                f"💰 مبلغ انتقال: {format_number(amount)} 🪙\n"
                f"🧾 کارمزد (۲%): {format_number(fee)} 🪙\n"
                f"📊 مجموع نیاز: {format_number(total)} 🪙\n\n"
                f"🔴 **کمبود:** {format_number(total - bank[3])} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=15
            )
            return
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        c.execute(
            "UPDATE bank SET balance = balance - ? WHERE user_id = ?",
            (int(total), user_id)
        )
        c.execute(
            "UPDATE bank SET balance = balance + ? WHERE user_id = ?",
            (int(amount), target_id)
        )
        conn.commit()
        conn.close()
        
        target_user = get_user(target_id)
        target_name = get_user_name(target_user) if target_user else "کاربر ناشناس"
        
        sender_user = get_user(user_id)
        sender_name = get_user_name(sender_user) if sender_user else "کاربر ناشناس"
        
        updated_bank = get_bank(user_id)
        new_balance = safe_int(updated_bank[3]) if updated_bank else 0
        
        await send_func(
            chat_id,
            f"✅ **انتقال بانکی انجام شد!** 🎉\n\n"
            f"💰 **مبلغ:** {format_number(amount)} 🪙\n"
            f"🧾 **کارمزد (۲%):** {format_number(fee)} 🪙\n"
            f"📊 **مجموع:** {format_number(total)} 🪙\n"
            f"👤 **گیرنده:** {target_name}\n"
            f"📊 **موجودی جدید شما:** {format_number(new_balance)} 🪙",
            reply_to=message.id,
            auto_delete=True,
            delete_after=30
        )
        
        try:
            await send_func(
                target_id,
                f"💰 **انتقال بانکی دریافت شد!** 💰\n\n"
                f"👤 **از:** {sender_name}\n"
                f"💰 **مبلغ:** {format_number(amount)} 🪙\n"
                f"📊 **موجودی جدید:** {format_number(safe_int(target_bank[3]) + amount)} 🪙",
                auto_delete=True,
                delete_after=30
            )
        except:
            pass
    
    async def handle_change_account(self, user_id, chat_id, message, send_func):
        bank = get_bank(user_id)
        if not bank:
            await send_func(
                chat_id,
                "❌ اول باید `بانک میویی` رو باز کنی!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            return
        
        if user_id in self.change_cooldowns:
            last_change = self.change_cooldowns[user_id]
            elapsed = (datetime.now() - last_change).total_seconds()
            if elapsed < 72 * 3600:
                remaining_hours = int((72 * 3600 - elapsed) / 3600)
                remaining_minutes = int(((72 * 3600 - elapsed) % 3600) / 60)
                await send_func(
                    chat_id,
                    f"⏳ **صبر کن!**\n\n"
                    f"تغییر شماره حساب فقط هر ۷۲ ساعت یک‌بار امکان‌پذیره.\n"
                    f"⏱️ {remaining_hours} ساعت و {remaining_minutes} دقیقه دیگه می‌تونی دوباره تغییر بدی.",
                    reply_to=message.id,
                    auto_delete=True,
                    delete_after=10
                )
                return
        
        user = get_user(user_id)
        cost = 1250
        
        if safe_int(user[6]) < cost:
            await send_func(
                chat_id,
                f"❌ **پوینت کافی نیست!**\n"
                f"💰 نیاز: {format_number(cost)} 🪙\n"
                f"💰 موجودی: {format_number(user[6])} 🪙",
                reply_to=message.id,
                auto_delete=True,
                delete_after=10
            )
            return
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        max_attempts = 100
        new_account = None
        
        for _ in range(max_attempts):
            new_account = str(random.randint(100000000000, 999999999999))
            c.execute("SELECT id FROM bank WHERE account_number = ?", (new_account,))
            if not c.fetchone():
                break
            new_account = None
        
        if not new_account:
            await send_func(
                chat_id,
                "❌ خطا در تولید شماره حساب جدید!",
                reply_to=message.id,
                auto_delete=True,
                delete_after=5
            )
            conn.close()
            return
        
        c.execute(
            "UPDATE bank SET account_number = ? WHERE user_id = ?",
            (new_account, user_id)
        )
        c.execute(
            "UPDATE users SET points = ? WHERE user_id = ?",
            (int(user[6] - cost), user_id)
        )
        conn.commit()
        conn.close()
        
        self.change_cooldowns[user_id] = datetime.now()
        
        await send_func(
            chat_id,
            f"✅ **شماره حساب تغییر کرد!**\n\n"
            f"💳 شماره حساب جدید: `{new_account}`\n"
            f"💰 هزینه: {format_number(cost)} 🪙\n"
            f"⏳ تا ۷۲ ساعت دیگه نمی‌تونی تغییر بدی.",
            reply_to=message.id,
            auto_delete=True,
            delete_after=30
        )
    
    def _extract_amount(self, text):
        if not text:
            return None
        
        persian_to_english = {
            '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
            '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9'
        }
        
        normalized_text = text
        for persian, english in persian_to_english.items():
            normalized_text = normalized_text.replace(persian, english)
        
        normalized_text = normalized_text.replace(',', '').lower()
        
        match = re.search(r'(\d+)\s*(k|m|هزار|میلیون|کی|میل)?', normalized_text)
        
        if not match:
            return None
        
        amount = int(match.group(1))
        suffix = (match.group(2) or '').lower()
        
        if suffix in ['k', 'کی', 'هزار']:
            amount *= 1000
        elif suffix in ['m', 'میل', 'میلیون']:
            amount *= 1000000
        
        if amount < 50:
            return None
        
        return amount