# utils.py
import re
from datetime import datetime

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

def to_persian_numbers(num):
    """تبدیل اعداد انگلیسی به فارسی"""
    persian = {
        '0': '۰', '1': '۱', '2': '۲', '3': '۳', '4': '۴',
        '5': '۵', '6': '۶', '7': '۷', '8': '۸', '9': '۹'
    }
    if isinstance(num, str):
        return ''.join(persian.get(c, c) for c in num)
    return ''.join(persian.get(c, c) for c in str(num))

def extract_username(text):
    match = re.search(r'@(\w+)', text)
    return match.group(1) if match else None

def extract_amount(text):
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

def format_number(num):
    try:
        num = int(num) if num is not None else 0
    except (ValueError, TypeError):
        num = 0
    return f"{num:,}"

def get_time_remaining(timestamp):
    if not timestamp:
        return "اکنون"
    if isinstance(timestamp, str):
        try:
            timestamp = datetime.fromisoformat(timestamp)
        except:
            return "نامشخص"
    diff = timestamp - datetime.now()
    if diff.total_seconds() <= 0:
        return "اکنون"
    hours = int(diff.total_seconds() // 3600)
    minutes = int((diff.total_seconds() % 3600) // 60)
    seconds = int(diff.total_seconds() % 60)
    if hours > 0:
        return f"{hours} ساعت {minutes} دقیقه"
    elif minutes > 0:
        return f"{minutes} دقیقه {seconds} ثانیه"
    else:
        return f"{seconds} ثانیه"

def get_level_emoji(level):
    try:
        level = int(level) if level is not None else 1
    except (ValueError, TypeError):
        level = 1
    
    if level >= 50:
        return "👑"
    elif level >= 40:
        return "🌟"
    elif level >= 30:
        return "⭐"
    elif level >= 20:
        return "✨"
    elif level >= 10:
        return "💫"
    else:
        return "🐾"

def get_fish_emoji(fish_type):
    emojis = {
        "common": "🐟",
        "uncommon": "🐠",
        "rare": "🐡",
        "epic": "🐙",
        "legendary": "🐉"
    }
    return emojis.get(fish_type, "🐟")

def get_rarity_name(fish_type):
    names = {
        "common": "معمولی",
        "uncommon": "کمیاب",
        "rare": "حماسی",
        "epic": "افسانه‌ای",
        "legendary": "اسطوره‌ای"
    }
    return names.get(fish_type, "معمولی")

def get_progress_bar(current, required, length=10):
    if required <= 0:
        return "▰" * length
    percent = min(100, int((current / required) * 100))
    filled = int((percent / 100) * length)
    return "▰" * filled + "▱" * (length - filled)

def is_meow_word(text):
    from config import MEOW_WORDS, MEOW_SOUNDS
    text = text.strip().lower()
    
    exclude_words = ["میوهام", "میوهاش", "میو پوینت", "میو بانک", "میو میو"]
    if text in exclude_words:
        return False
    
    if text in MEOW_WORDS:
        return True
    if text in MEOW_SOUNDS:
        return True
    if text in ["میو میو", "مِیو مِیو", "meow meow", "mew mew"]:
        return True
    return False

def get_random_meow_response():
    import random
    responses = [
        "🐱 میووو! خرخری خرخری... 😺",
        "🐱 معـعـعـعـع! 🐾",
        "🐱 میو میو... چه روز خوبی! ✨",
        "🐱 میـیـیـیـووو! 😻",
        "🐱 مع! مو! میووو! 🐈",
        "🐱 خخخ... میووو! 💕",
        "🐱 میو میو میووو! 🎵",
        "🐱 عـعـعـعـعـعـع! 😼",
        "🐱 میو... پشمالوها قدرت! 🐾",
        "🐱 معـعـعـع! چه میو قشنگی! ✨",
        "🐱 مِیـوووو! خوش اومدی! 😺",
        "🐱 موووووووو! 🐱"
    ]
    return random.choice(responses)

def get_user_name(user):
    if not user:
        return "کاربر ناشناس"
    
    if isinstance(user, tuple):
        if len(user) > 3 and user[3]:
            return str(user[3])
        elif len(user) > 2 and user[2]:
            return str(user[2])
        else:
            return f"کاربر {user[1] if len(user) > 1 else 'ناشناس'}"
    else:
        first_name = user.get('first_name', '')
        username = user.get('username', '')
        user_id = user.get('user_id', '')
        if first_name:
            return str(first_name)
        if username:
            return str(username)
        return f"کاربر {user_id}"

def get_user_display(user):
    if not user:
        return "کاربر ناشناس"
    return get_user_name(user)

def get_user_display_by_id(user_id):
    from database import get_user
    user = get_user(user_id)
    if user:
        return get_user_display(user)
    return f"کاربر {user_id}"