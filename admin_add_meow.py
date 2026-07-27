# admin_add_meow.py
import sqlite3
from database import DATABASE_FILE, get_user, update_user
from utils import format_number  # اصلاح: از utils import کنید

def show_user_info(user_id):
    """نمایش اطلاعات کامل کاربر"""
    user = get_user(user_id)
    if not user:
        print("❌ کاربر پیدا نشد!")
        return
    
    print(f"\n📊 **اطلاعات کاربر {user_id}:**")
    print("=" * 40)
    print(f"  👤 نام: {user[3]}")
    print(f"  🆔 آیدی: {user[1]}")
    print(f"  📊 سطح: {user[4]}")
    print(f"  🐾 میوها: {format_number(user[5])}")
    print(f"  💰 پوینت‌ها: {format_number(user[6])}")
    print(f"  🐈 پیشی: {user[8]}")
    print(f"  📦 پوینت‌های پیشی: {format_number(user[10])}")
    print(f"  🌟 مقام: {user[13]}")
    print(f"  📈 حداکثر سطح: {user[14]}")
    print("=" * 40)

def add_points(user_id, amount):
    """اضافه کردن پوینت به کاربر"""
    user = get_user(user_id)
    if not user:
        print("❌ کاربر پیدا نشد!")
        return
    
    new_points = user[6] + amount
    update_user(user_id, points=new_points)
    print(f"✅ {format_number(amount)} 🪙 به کاربر {user_id} اضافه شد!")
    print(f"💰 موجودی جدید: {format_number(new_points)} 🪙")

def remove_points(user_id, amount):
    """کم کردن پوینت از کاربر"""
    user = get_user(user_id)
    if not user:
        print("❌ کاربر پیدا نشد!")
        return
    
    if user[6] < amount:
        print(f"❌ موجودی کاربر ({format_number(user[6])}) کمتر از مبلغ درخواستی است!")
        return
    
    new_points = user[6] - amount
    update_user(user_id, points=new_points)
    print(f"✅ {format_number(amount)} 🪙 از کاربر {user_id} کم شد!")
    print(f"💰 موجودی جدید: {format_number(new_points)} 🪙")

def set_points(user_id, amount):
    """تنظیم پوینت کاربر به مقدار دلخواه"""
    user = get_user(user_id)
    if not user:
        print("❌ کاربر پیدا نشد!")
        return
    
    update_user(user_id, points=amount)
    print(f"✅ پوینت کاربر {user_id} به {format_number(amount)} 🪙 تنظیم شد!")

def reset_user(user_id):
    """ریست کردن کامل کاربر"""
    user = get_user(user_id)
    if not user:
        print("❌ کاربر پیدا نشد!")
        return
    
    confirm = input(f"⚠️ آیا از ریست کردن کامل کاربر {user_id} مطمئن هستید؟ (yes/no): ")
    if confirm.lower() != "yes":
        print("❌ لغو شد!")
        return
    
    update_user(
        user_id,
        meows=0,
        points=0,
        level=1,
        pet_name=None,
        pet_level=1,
        pet_points=0,
        pet_rank=0,
        pet_max_level=5
    )
    print(f"✅ کاربر {user_id} به حالت اولیه برگشت!")

def find_cheaters():
    """پیدا کردن کاربران مشکوک (پوینت‌های غیرعادی)"""
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    
    # کاربرانی که پوینت‌شون خیلی بالاست
    c.execute("SELECT user_id, points, meows FROM users WHERE points > 1000000 ORDER BY points DESC")
    users = c.fetchall()
    conn.close()
    
    if not users:
        print("✅ هیچ کاربر مشکوکی پیدا نشد!")
        return
    
    print("\n🚨 **کاربران با پوینت بالا (مشکوک):**")
    print("=" * 40)
    for user_id, points, meows in users:
        ratio = points // meows if meows > 0 else points
        print(f"  🆔 {user_id}: 💰 {format_number(points)} 🪙 | 🐾 {format_number(meows)} میو")
        print(f"     نسبت پوینت به میو: {format_number(ratio)}")
    print("=" * 40)

def show_top_users(limit=10):
    """نمایش کاربران برتر"""
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT user_id, username, first_name, points, meows FROM users ORDER BY points DESC LIMIT ?",
        (limit,)
    )
    users = c.fetchall()
    conn.close()
    
    print(f"\n🏆 **{limit} کاربر برتر:**")
    print("=" * 40)
    for i, (user_id, username, first_name, points, meows) in enumerate(users, 1):
        name = first_name if first_name else username if username else f"کاربر {user_id}"
        print(f"  {i}. {name}: 💰 {format_number(points)} 🪙 | 🐾 {format_number(meows)} میو")
    print("=" * 40)

def main_menu():
    while True:
        print("\n" + "=" * 50)
        print("👑 **پنل مدیریت ادمین**")
        print("=" * 50)
        print("1. 📊 نمایش اطلاعات کاربر")
        print("2. ➕ اضافه کردن پوینت")
        print("3. ➖ کم کردن پوینت")
        print("4. 🎯 تنظیم پوینت")
        print("5. 🔄 ریست کردن کاربر")
        print("6. 🚨 پیدا کردن کاربران مشکوک")
        print("7. 🏆 نمایش کاربران برتر")
        print("8. 🚪 خروج")
        print("=" * 50)
        
        choice = input("انتخاب کنید: ")
        
        if choice == "1":
            user_id = int(input("🆔 آیدی کاربر: "))
            show_user_info(user_id)
        
        elif choice == "2":
            user_id = int(input("🆔 آیدی کاربر: "))
            amount = int(input("💰 مبلغ (پوینت): "))
            add_points(user_id, amount)
        
        elif choice == "3":
            user_id = int(input("🆔 آیدی کاربر: "))
            amount = int(input("💰 مبلغ (پوینت): "))
            remove_points(user_id, amount)
        
        elif choice == "4":
            user_id = int(input("🆔 آیدی کاربر: "))
            amount = int(input("💰 مبلغ جدید (پوینت): "))
            set_points(user_id, amount)
        
        elif choice == "5":
            user_id = int(input("🆔 آیدی کاربر: "))
            reset_user(user_id)
        
        elif choice == "6":
            find_cheaters()
        
        elif choice == "7":
            limit = input("📊 تعداد (پیش‌فرض 10): ")
            limit = int(limit) if limit else 10
            show_top_users(limit)
        
        elif choice == "8":
            print("👋 خروج!")
            break
        
        else:
            print("❌ انتخاب نامعتبر!")

if __name__ == "__main__":
    main_menu()