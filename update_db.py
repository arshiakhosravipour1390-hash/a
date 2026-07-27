# clean_fridge.py
import sqlite3

def clean_fridge():
    conn = sqlite3.connect("meow.db")
    c = conn.cursor()
    
    # حذف همه ماهی‌های یخچال (برای رفع داده‌های خراب)
    c.execute("DELETE FROM fridge_fish")
    
    conn.commit()
    print("✅ همه ماهی‌های یخچال پاک شدند!")
    conn.close()

if __name__ == "__main__":
    clean_fridge()