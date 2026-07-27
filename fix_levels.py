# clear_old_fish.py
import sqlite3

DB_FILE = "meow.db"

def clear_old_fish():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # حذف همه ماهی‌های قدیمی یخچال
    c.execute("DELETE FROM fridge_fish")
    
    conn.commit()
    conn.close()
    print("✅ همه ماهی‌های قدیمی یخچال پاک شدن!")
    print("📌 حالا دوباره یه ماهی جدید بگیر و بنداز تو یخچال.")

if __name__ == "__main__":
    clear_old_fish()