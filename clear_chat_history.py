# clear_chat_history.py
import asyncio
from splusthon import SoroushClient
from splusthon.sessions import StringSession
from config import BOT_SESSION

async def clear_chat():
    print("🧹 شروع پاکسازی تاریخچه گپ...")
    print("=" * 50)
    
    # === اتصال به ربات ===
    client = SoroushClient(StringSession(BOT_SESSION))
    await client.start()
    
    me = await client.get_me()
    print(f"✅ ربات متصل شد: @{me.username or me.first_name}")
    
    # === لینک گپ مورد نظر ===
    # لینکی که دادی: https://splus.ir/tiese
    # یعنی یوزرنیم گپ: tiese
    GROUP_USERNAME = "tiese"
    
    print(f"📢 گپ هدف: @{GROUP_USERNAME}")
    print("=" * 50)
    
    try:
        # === گرفتن اطلاعات گپ ===
        entity = await client.get_entity(f"@{GROUP_USERNAME}")
        print(f"✅ گپ پیدا شد: {entity.title}")
        print(f"🆔 آیدی گپ: {entity.id}")
        
        # === دریافت تأیید ===
        confirm = input("\n⚠️ آیا مطمئنی می‌خوای همه پیام‌های این گپ رو پاک کنی؟ (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ عملیات لغو شد!")
            await client.disconnect()
            return
        
        # === پاکسازی پیام‌ها ===
        total_deleted = 0
        batch_size = 100
        
        print("\n⏳ در حال پاکسازی پیام‌ها...")
        
        while True:
            # دریافت پیام‌ها
            messages = await client.get_messages(entity, limit=batch_size)
            
            if not messages:
                break
            
            # استخراج آیدی پیام‌ها
            message_ids = [msg.id for msg in messages if msg]
            
            if not message_ids:
                break
            
            # حذف پیام‌ها
            try:
                await client.delete_messages(entity, message_ids)
                total_deleted += len(message_ids)
                print(f"   🗑️ {total_deleted} پیام حذف شد...")
            except Exception as e:
                print(f"⚠️ خطا در حذف دسته‌ای: {e}")
                # اگر خطا خورد، تک‌تک حذف کن
                for msg_id in message_ids[:10]:
                    try:
                        await client.delete_messages(entity, [msg_id])
                        total_deleted += 1
                    except:
                        pass
                print(f"   🗑️ {total_deleted} پیام حذف شد (تک‌تک)...")
            
            # تاخیر برای جلوگیری از محدودیت
            await asyncio.sleep(1)
        
        print("\n" + "=" * 50)
        print(f"✅ **پاکسازی کامل شد!**")
        print(f"🗑️ تعداد کل پیام‌های حذف شده: {total_deleted}")
        print("🌸 تاریخچه گپ کاملاً پاکسازی شد!")
        
    except Exception as e:
        print(f"❌ خطا: {e}")
        print("\n💡 نکات:")
        print("1. مطمئن شو ربات در گپ عضو هست")
        print("2. ربات باید ادمین گپ باشه")
        print("3. یوزرنیم گپ رو درست وارد کردی")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(clear_chat())