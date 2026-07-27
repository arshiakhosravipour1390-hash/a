# database.py
import sqlite3
import random
import math
from datetime import datetime, timedelta
from config import DATABASE_FILE

def safe_int(value, default=0):
    if value is None:
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value) if value.strip() else default
        except ValueError:
            return default
    return default

def safe_str(value, default=""):
    if value is None:
        return default
    return str(value)

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            level INTEGER DEFAULT 1,
            meows INTEGER DEFAULT 0,
            points INTEGER DEFAULT 0,
            last_meow TEXT,
            pet_name TEXT,
            pet_level INTEGER DEFAULT 1,
            pet_points INTEGER DEFAULT 0,
            pet_hunger TEXT,
            street_pets INTEGER DEFAULT 0,
            pet_rank INTEGER DEFAULT 0,
            pet_max_level INTEGER DEFAULT 5,
            has_fridge INTEGER DEFAULT 0,
            fridge_level INTEGER DEFAULT 1,
            is_private INTEGER DEFAULT 0,
            created_at TEXT,
            last_collect TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY,
            group_id INTEGER UNIQUE,
            name TEXT,
            level INTEGER DEFAULT 1,
            treasury INTEGER DEFAULT 0,
            total_meows INTEGER DEFAULT 0,
            population INTEGER DEFAULT 0,
            fish_stock INTEGER DEFAULT 0,
            created_at TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS fishing (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            rod_level INTEGER DEFAULT 1,
            last_fish TEXT,
            total_fish INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS bank (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            account_number TEXT UNIQUE,
            balance INTEGER DEFAULT 0,
            last_interest TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS casino (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            game_type TEXT,
            bet_amount INTEGER,
            result TEXT,
            played_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS fridge (
            id INTEGER PRIMARY KEY,
            user_id INTEGER UNIQUE,
            level INTEGER DEFAULT 1,
            capacity INTEGER DEFAULT 2,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS fridge_fish (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            fish_type TEXT,
            weight REAL,
            value INTEGER,
            food_value INTEGER,
            is_cooked INTEGER DEFAULT 0,
            stored_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    try:
        c.execute("ALTER TABLE users ADD COLUMN last_collect TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE bank ADD COLUMN account_number TEXT")
    except:
        pass
    
    try:
        c.execute("ALTER TABLE bank ADD COLUMN last_interest TEXT")
    except:
        pass
    
    conn.commit()
    conn.close()

# ============================================================
# فقط این بخش رو در database.py جایگزین کن
# ============================================================

def get_user(user_id):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    
    if 'pet_rank' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN pet_rank INTEGER DEFAULT 0")
    if 'pet_max_level' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN pet_max_level INTEGER DEFAULT 5")
    if 'last_collect' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN last_collect TEXT")
    
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    
    if not result:
        return None
    
    data = {}
    for i, col in enumerate(columns):
        if i < len(result):
            data[col] = result[i]
        else:
            data[col] = None
    
    result_list = [
        data.get('id', 0),
        data.get('user_id', 0),
        data.get('username', ''),
        data.get('first_name', ''),
        data.get('level', 1),
        data.get('meows', 0),
        data.get('points', 0),
        data.get('last_meow', ''),
        data.get('pet_name', ''),
        data.get('pet_level', 1),
        data.get('pet_points', 0),
        data.get('pet_hunger', ''),
        data.get('street_pets', 0),
        data.get('pet_rank', 0),
        data.get('pet_max_level', 5),
        data.get('has_fridge', 0),
        data.get('fridge_level', 1),
        data.get('is_private', 0),
        data.get('created_at', ''),
        data.get('last_collect', '')
    ]
    
    numeric_indices = [0, 1, 4, 5, 6, 9, 10, 12, 13, 14, 15, 16, 17]
    for i in numeric_indices:
        if i < len(result_list):
            result_list[i] = safe_int(result_list[i])
    
    string_indices = [2, 3, 7, 8, 11, 18, 19]
    for i in string_indices:
        if i < len(result_list):
            result_list[i] = safe_str(result_list[i])
    
    result_list[4] = max(1, result_list[4])
    
    # ✅ حالت ونیش برای ادمین
    from config import ADMIN_ID, ADMIN_UNLIMITED_POINTS, DEVELOPER_MODE
    
    if DEVELOPER_MODE and int(user_id) == int(ADMIN_ID):
        result_list = list(result_list)
        result_list[4] = 50
        result_list[5] = 999999
        result_list[6] = ADMIN_UNLIMITED_POINTS
        return tuple(result_list)
    
    return tuple(result_list)

def create_user(user_id, username="", first_name=""):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if c.fetchone():
            conn.close()
            return True
        
        c.execute(
            """INSERT INTO users 
               (user_id, username, first_name, pet_rank, pet_max_level, created_at, last_collect) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, username[:50] if username else "", first_name[:50] if first_name else "", 0, 5, now, now)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ خطا در create_user: {e}")
        return False

def update_user(user_id, **kwargs):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    
    numeric_fields = ['level', 'meows', 'points', 'pet_level', 'pet_points', 
                     'street_pets', 'pet_rank', 'pet_max_level', 'has_fridge', 
                     'fridge_level', 'is_private']
    
    for key, value in kwargs.items():
        if key in numeric_fields:
            value = int(value) if value is not None else 0
        else:
            value = str(value) if value is not None else ''
        
        if key in ['pet_rank', 'pet_max_level', 'last_collect']:
            c.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in c.fetchall()]
            if key not in columns:
                c.execute(f"ALTER TABLE users ADD COLUMN {key} TEXT")
        
        c.execute(f"UPDATE users SET {key} = ? WHERE user_id = ?", (value, user_id))
    
    conn.commit()
    conn.close()

def update_pet_rank(user_id, new_rank, new_max_level, cost):
    """ارتقا مقام پیشی - زمان گرسنگی رو به‌روز کن"""
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    
    user_id = int(user_id)
    new_rank = int(new_rank)
    new_max_level = int(new_max_level)
    cost = int(cost)
    
    c.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in c.fetchall()]
    if 'pet_rank' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN pet_rank INTEGER DEFAULT 0")
    if 'pet_max_level' not in columns:
        c.execute("ALTER TABLE users ADD COLUMN pet_max_level INTEGER DEFAULT 5")
    
    now = datetime.now().isoformat()
    
    c.execute("""
        UPDATE users 
        SET points = points - ?,
            pet_rank = ?,
            pet_max_level = ?,
            pet_level = 1,
            pet_points = 0,
            pet_hunger = ?,
            last_collect = ?
        WHERE user_id = ?
    """, (cost, new_rank, new_max_level, now, now, user_id))
    
    conn.commit()
    conn.close()

def update_user_info(user_id, username="", first_name=""):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE users SET username = ?, first_name = ? WHERE user_id = ?",
        (username[:50] if username else "", first_name[:50] if first_name else "", user_id)
    )
    conn.commit()
    conn.close()

def get_level_info(level):
    from config import LEVELS
    return LEVELS.get(level, LEVELS[1])

def calculate_level(meows):
    from config import LEVELS
    level = 1
    for lvl, data in LEVELS.items():
        if meows >= data["required"]:
            level = lvl
    return level

def get_rank(user_id, sort_by="meows"):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        f"SELECT COUNT(*) + 1 FROM users WHERE {sort_by} > (SELECT {sort_by} FROM users WHERE user_id = ?)",
        (user_id,)
    )
    result = c.fetchone()
    conn.close()
    return result[0] if result else 1

def get_top_users(limit=5, sort_by="points"):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        f"SELECT user_id, username, first_name, meows, points, level FROM users WHERE is_private = 0 ORDER BY {sort_by} DESC LIMIT ?",
        (limit,)
    )
    result = c.fetchall()
    conn.close()
    return result

def get_group(group_id):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM groups WHERE group_id = ?", (group_id,))
    result = c.fetchone()
    conn.close()
    return result

def create_group(group_id, name=""):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO groups (group_id, name, created_at) VALUES (?, ?, ?)",
        (group_id, name[:50], datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def update_group(group_id, **kwargs):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    for key, value in kwargs.items():
        if key in ['level', 'treasury', 'total_meows', 'population', 'fish_stock']:
            value = int(value) if value is not None else 0
        c.execute(f"UPDATE groups SET {key} = ? WHERE group_id = ?", (value, group_id))
    conn.commit()
    conn.close()

# ============================================================
# ✅ تابع add_meow - نسخه اصلاح شده (با level_up)
# ============================================================

def add_meow(user_id):
    import random
    from config import MEOW_POINTS_BY_LEVEL
    
    user = get_user(user_id)
    if not user:
        create_user(user_id, "", "")
        user = get_user(user_id)
        if not user:
            return None
    
    current_level = safe_int(user[4], 1)
    meows = safe_int(user[5]) + 1
    
    level_points = MEOW_POINTS_BY_LEVEL.get(current_level, {"min": 1, "max": 3})
    points_earned = random.randint(level_points["min"], level_points["max"])
    
    points = safe_int(user[6]) + points_earned
    
    new_level = calculate_level(meows)
    reward = 0
    level_up = False
    old_level = current_level
    
    if new_level > current_level:
        level_up = True
        level_data = get_level_info(new_level)
        reward = level_data["reward"]
        points += reward
    
    update_user(
        user_id,
        meows=int(meows),
        points=int(points),
        level=int(new_level),
        last_meow=datetime.now().isoformat()
    )
    
    return {
        "meows": meows,
        "points_earned": points_earned,
        "points": points,
        "level": new_level,
        "reward": reward,
        "old_level": old_level,
        "level_up": level_up  # ✅ این کلید اضافه شد
    }

def can_meow(user_id):
    from config import MEOW_COOLDOWN
    user = get_user(user_id)
    if not user or not user[7]:
        return True
    try:
        last = datetime.fromisoformat(user[7])
        return (datetime.now() - last).seconds >= MEOW_COOLDOWN
    except:
        return True

# ============================================================
# ✅ سیستم کامل پیشی - نسخه نهایی (۶ مقام، ۳۰ سطح)
# ============================================================

# ====== توابع کمکی ======

def get_pet_rank_info(rank):
    """دریافت اطلاعات مقام پیشی"""
    from config import PET_RANKS
    return PET_RANKS.get(rank, PET_RANKS[0])

def get_pet_max_level(rank):
    """دریافت حداکثر سطح برای مقام"""
    info = get_pet_rank_info(rank)
    return info["max_level"]

def get_pet_max_hunger(rank):
    """دریافت حداکثر شکم برای مقام"""
    info = get_pet_rank_info(rank)
    return info["max_hunger"]

def get_pet_rank_name(rank):
    """دریافت نام مقام پیشی"""
    info = get_pet_rank_info(rank)
    return info["name"]

def get_pet_production(rank, level):
    """دریافت تولید در ثانیه - با fallback به فرمول"""
    from config import PET_PRODUCTION_TABLE
    
    result = PET_PRODUCTION_TABLE.get((rank, level))
    if result is not None:
        return result
    
    base_pps = {0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1, 5: 0.1}
    growth = 1 + (level - 1) * 0.15
    rank_bonus = 1 + rank * 0.2
    return round(base_pps.get(rank, 0.1) * growth * rank_bonus, 2)

def get_pet_capacity(rank, level):
    """دریافت ظرفیت - با fallback به فرمول"""
    from config import PET_CAPACITY_TABLE, PET_RANKS
    
    result = PET_CAPACITY_TABLE.get((rank, level))
    if result is not None:
        return result
    
    max_level = PET_RANKS.get(rank, {"max_level": 5})["max_level"]
    base_capacity = 50 * (1 + rank * 2)
    growth_factor = 1 + (level - 1) * 0.3
    return int(base_capacity * growth_factor * (level / max(1, max_level)))

def get_pet_upgrade_cost(level):
    """دریافت هزینه ارتقا سطح"""
    from config import PET_UPGRADE_COSTS
    return PET_UPGRADE_COSTS.get(level, int(level * 150 * (1 + (level - 1) * 0.15)))

def get_pet_promote_cost(rank):
    """دریافت هزینه ارتقا مقام"""
    from config import PET_PROMOTE_COSTS
    return PET_PROMOTE_COSTS.get(rank, 0)

# ====== توابع اصلی پیشی ======

def buy_pet(user_id, name):
    from config import PET_PRICE
    user = get_user(user_id)
    if not user or safe_int(user[6]) < PET_PRICE:
        return False
    points = safe_int(user[6]) - PET_PRICE
    now = datetime.now().isoformat()
    update_user(
        user_id,
        points=int(points),
        pet_name=name[:20],
        pet_level=1,
        pet_points=0,
        pet_rank=0,
        pet_max_level=get_pet_max_level(0),
        pet_hunger=now,
        last_collect=now
    )
    return True

def get_pet_points(user_id):
    """محاسبه پوینت‌های تولید شده پیشی در لحظه"""
    user = get_user(user_id)
    if not user or not user[8]:
        return 0
    
    if is_pet_hungry(user_id):
        return safe_int(user[10], 0)
    
    last_collect = user[19] if len(user) > 19 and user[19] else None
    
    if not last_collect:
        return 0
    
    try:
        last_time = datetime.fromisoformat(last_collect)
    except:
        return 0
    
    seconds_passed = (datetime.now() - last_time).seconds
    pet_level = safe_int(user[9], 1)
    pet_rank = safe_int(user[13]) if len(user) > 13 else 0
    
    production = get_pet_production(pet_rank, pet_level)
    earned = int(seconds_passed * production)
    
    capacity = get_pet_capacity(pet_rank, pet_level)
    if earned > capacity:
        earned = capacity
    
    total_points = safe_int(user[10], 0) + earned
    if total_points > capacity:
        total_points = capacity
    
    return total_points

def collect_pet_points(user_id):
    user = get_user(user_id)
    if not user or not user[8]:
        return 0
    
    earned = get_pet_points(user_id)
    
    if earned < 10:
        return 0
    
    if earned > 0:
        now = datetime.now().isoformat()
        current_points = safe_int(user[6])
        
        update_user(
            user_id,
            points=int(current_points + earned),
            pet_points=0,
            last_collect=now
        )
        return earned
    
    return 0

def feed_pet(user_id, food_value=1):
    """غذا دادن به پیشی - زمان سیری جمع میشه"""
    user = get_user(user_id)
    if not user or not user[8]:
        return False
    
    hours = food_value * 2
    
    current_hunger_time = user[11]
    if current_hunger_time:
        try:
            current_hunger = datetime.fromisoformat(current_hunger_time)
            if current_hunger > datetime.now():
                new_hunger_time = current_hunger + timedelta(hours=hours)
            else:
                new_hunger_time = datetime.now() + timedelta(hours=hours)
        except:
            new_hunger_time = datetime.now() + timedelta(hours=hours)
    else:
        new_hunger_time = datetime.now() + timedelta(hours=hours)
    
    update_user(user_id, pet_hunger=new_hunger_time.isoformat())
    return True

def is_pet_hungry(user_id):
    """بررسی گرسنگی پیشی"""
    user = get_user(user_id)
    if not user or not user[8]:
        return True
    
    hunger_time = user[11]
    
    if not hunger_time:
        return False
    
    try:
        hunger_time = datetime.fromisoformat(hunger_time)
        return datetime.now() > hunger_time
    except:
        return False

def get_hunger_remaining(user_id):
    """دریافت زمان باقی‌مونده تا گرسنگی (به ساعت)"""
    user = get_user(user_id)
    if not user or not user[8]:
        return 0
    
    hunger_time = user[11]
    
    if not hunger_time:
        return 999
    
    try:
        hunger_time = datetime.fromisoformat(hunger_time)
        remaining = (hunger_time - datetime.now()).total_seconds()
        if remaining < 0:
            return 0
        return remaining / 3600
    except:
        return 999

def get_hunger_status(user_id):
    """دریافت وضعیت گرسنگی پیشی با متن مناسب بر اساس درصد سیری"""
    user = get_user(user_id)
    if not user or not user[8]:
        return "😿 من دیگه کار نمیکنمیو"
    
    hunger_time = user[11]
    pet_rank = safe_int(user[13]) if len(user) > 13 else 0
    max_hunger = get_pet_max_hunger(pet_rank)
    
    if not hunger_time:
        return "😻 عاشقتمیووو"
    
    try:
        hunger_time = datetime.fromisoformat(hunger_time)
        remaining = (hunger_time - datetime.now()).total_seconds()
        
        if remaining <= 0:
            return "😿 من دیگه کار نمیکنمیو"
        
        hunger_units = remaining / 3600 / 2
        if hunger_units > max_hunger:
            hunger_units = max_hunger
        
        if hunger_units <= 0:
            return "😿 من دیگه کار نمیکنمیو"
        
        percentage = (hunger_units / max_hunger) * 100
        
        if percentage >= 75:
            return "😻 عاشقتمیووو"
        elif percentage >= 40:
            return "😸 شیکمم پره"
        elif percentage >= 10:
            return "😾 من گشنمیووو.."
        elif percentage >= 1:
            return "😾 دارم غش میکنمیووو"
        else:
            return "😿 من دیگه کار نمیکنمیو"
            
    except Exception as e:
        print(f"❌ خطا در get_hunger_status: {e}")
        return "😿 من دیگه کار نمیکنمیو"

# ============================================================
# توابع بانک
# ============================================================

def get_bank(user_id):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute("SELECT * FROM bank WHERE user_id = ?", (user_id,))
        result = c.fetchone()
        conn.close()
        
        if result:
            result = list(result)
            while len(result) < 5:
                result.append(None)
            
            account_number = result[2] if len(result) > 2 else None
            if not account_number or str(account_number).strip() == "" or str(account_number) == "ندارد":
                new_account = str(random.randint(100000000000, 999999999999))
                conn = sqlite3.connect(DATABASE_FILE)
                c = conn.cursor()
                c.execute("UPDATE bank SET account_number = ? WHERE user_id = ?", (new_account, user_id))
                conn.commit()
                conn.close()
                result[2] = new_account
            
            return tuple(result)
        return None
    except Exception as e:
        print(f"❌ خطا در get_bank: {e}")
        return None

def open_bank(user_id):
    from config import BANK_OPEN_PRICE
    
    try:
        user = get_user(user_id)
        if not user:
            create_user(user_id, "", "")
            user = get_user(user_id)
            if not user:
                return False
        
        if safe_int(user[6]) < BANK_OPEN_PRICE:
            return False
        
        if get_bank(user_id):
            return False
        
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        
        max_attempts = 100
        account_number = None
        
        for _ in range(max_attempts):
            account_number = str(random.randint(100000000000, 999999999999))
            c.execute("SELECT id FROM bank WHERE account_number = ?", (account_number,))
            if not c.fetchone():
                break
            account_number = None
        
        if not account_number:
            conn.close()
            return False
        
        now = datetime.now().isoformat()
        
        c.execute("""
            INSERT INTO bank (user_id, account_number, balance, last_interest)
            VALUES (?, ?, ?, ?)
        """, (user_id, account_number, 0, now))
        
        conn.commit()
        conn.close()
        
        update_user(user_id, points=int(safe_int(user[6]) - BANK_OPEN_PRICE))
        return True
        
    except Exception as e:
        print(f"❌ خطا در open_bank: {e}")
        return False

def deposit_bank(user_id, amount):
    bank = get_bank(user_id)
    if not bank:
        return False
    user = get_user(user_id)
    if safe_int(user[6]) < amount:
        return False
    update_user(user_id, points=int(safe_int(user[6]) - amount))
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("UPDATE bank SET balance = balance + ? WHERE user_id = ?", (int(amount), user_id))
    conn.commit()
    conn.close()
    return True

def withdraw_bank(user_id, amount):
    bank = get_bank(user_id)
    if not bank or safe_int(bank[3]) < amount:
        return False
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("UPDATE bank SET balance = balance - ? WHERE user_id = ?", (int(amount), user_id))
    conn.commit()
    conn.close()
    user = get_user(user_id)
    update_user(user_id, points=int(safe_int(user[6]) + amount))
    return True

def calculate_interest(user_id):
    from config import BANK_INTEREST_RATE, BANK_MAX_INTEREST
    bank = get_bank(user_id)
    if not bank:
        return 0
    balance = safe_int(bank[3])
    interest = int(balance * BANK_INTEREST_RATE)
    if interest > BANK_MAX_INTEREST:
        interest = BANK_MAX_INTEREST
    if interest > 0:
        conn = sqlite3.connect(DATABASE_FILE)
        c = conn.cursor()
        c.execute(
            "UPDATE bank SET balance = balance + ?, last_interest = ? WHERE user_id = ?",
            (int(interest), datetime.now().isoformat(), user_id)
        )
        conn.commit()
        conn.close()
    return interest

def can_get_interest(user_id):
    bank = get_bank(user_id)
    if not bank:
        return False
    last = bank[4]
    if not last:
        return True
    try:
        last = datetime.fromisoformat(last)
        return (datetime.now() - last).days >= 1
    except:
        return True

# ============================================================
# توابع ماهیگیری
# ============================================================

def get_fishing(user_id):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM fishing WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result

def create_fishing(user_id):
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO fishing (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def upgrade_rod(user_id):
    from config import FISHING_LEVELS
    fishing = get_fishing(user_id)
    if not fishing:
        create_fishing(user_id)
        fishing = get_fishing(user_id)
    
    current_level = safe_int(fishing[2], 1)
    if current_level >= 7:
        return False
    
    next_level = current_level + 1
    cost = FISHING_LEVELS[next_level]["cost"]
    
    user = get_user(user_id)
    if safe_int(user[6]) < cost:
        return False
    
    update_user(user_id, points=int(safe_int(user[6]) - cost))
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute("UPDATE fishing SET rod_level = ? WHERE user_id = ?", (next_level, user_id))
    conn.commit()
    conn.close()
    return True

def can_fish(user_id):
    fishing = get_fishing(user_id)
    if not fishing or not fishing[3]:
        return True
    from config import FISHING_LEVELS
    level = safe_int(fishing[2], 1)
    cooldown = FISHING_LEVELS[level]["cooldown"]
    try:
        last = datetime.fromisoformat(fishing[3])
        return (datetime.now() - last).seconds >= cooldown
    except:
        return True

def fish(user_id, ignore_cooldown=False):
    import random
    from config import FISHING_LEVELS, FISHING_MULTIPLIERS, FISHING_FOOD_VALUES
    
    if not ignore_cooldown:
        if not can_fish(user_id):
            return None
    
    fishing = get_fishing(user_id)
    if not fishing:
        create_fishing(user_id)
        fishing = get_fishing(user_id)
        if not fishing:
            return None
    
    level = safe_int(fishing[2], 1)
    chances = FISHING_LEVELS[level]["chances"]
    
    roll = random.random()
    cumulative = 0
    fish_type = "common"
    for ftype, prob in chances.items():
        cumulative += prob
        if roll <= cumulative:
            fish_type = ftype
            break
    
    weight = round(random.uniform(0.5, 5.0), 2)
    base_value = int(weight * 100)
    value = base_value * FISHING_MULTIPLIERS.get(fish_type, 1)
    food_value = FISHING_FOOD_VALUES.get(fish_type, 1)
    
    conn = sqlite3.connect(DATABASE_FILE)
    c = conn.cursor()
    c.execute(
        "UPDATE fishing SET last_fish = ?, total_fish = total_fish + 1 WHERE user_id = ?",
        (datetime.now().isoformat(), user_id)
    )
    conn.commit()
    conn.close()
    
    return {"type": fish_type, "weight": weight, "value": value, "food_value": food_value}