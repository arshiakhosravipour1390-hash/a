# fix_fridge_final.py
import sqlite3
import os

DB_FILE = "meow.db"

def fix_fridge():
    print("🔧 در حال تعمیر یخچال...")
    
    # اول از همه یک بکاپ بگیر
    if os.path.exists(DB_FILE):
        os.rename(DB_FILE, "meow_backup_before_fix.db")
        print("✅ بکاپ گرفته شد: meow_backup_before_fix.db")
    
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. جدول fridge_fish رو کاملاً پاک کن
    c.execute("DROP TABLE IF EXISTS fridge_fish")
    print("✅ جدول fridge_fish حذف شد")
    
    # 2. جدول fridge رو پاک کن (یخچال‌ها)
    c.execute("DROP TABLE IF EXISTS fridge")
    print("✅ جدول fridge حذف شد")
    
    # 3. دوباره جدول‌ها رو با ساختار درست بساز
    c.execute('''
        CREATE TABLE fridge (
            user_id INTEGER PRIMARY KEY,
            level INTEGER DEFAULT 1,
            capacity INTEGER DEFAULT 2,
            created_at TEXT
        )
    ''')
    print("✅ جدول fridge ساخته شد")
    
    c.execute('''
        CREATE TABLE fridge_fish (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            fish_type TEXT,
            weight REAL,
            value INTEGER,
            food_value INTEGER,
            is_cooked INTEGER DEFAULT 0,
            stored_at TEXT
        )
    ''')
    print("✅ جدول fridge_fish با ساختار درست ساخته شد")
    
    conn.commit()
    conn.close()
    
    print("\n🎉 همه چیز ریست شد! حالا یخچال کاملاً خالی و سالم هست.")
    print("📌 ربات رو ری‌استارت کن و دوباره ماهی بگیر.")

if __name__ == "__main__":
    fix_fridge()