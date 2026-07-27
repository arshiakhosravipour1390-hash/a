# config.py
import os

# ================== سشن ربات ==================
BOT_SESSION = "1AwASaW0tc2VydmVyLnNwbHVzLmlyAbuWmOga0shPQSrvzLD9hD20XnI8PfzVA6ZGOOv_KicxvPeewFEUtv2bhjdA9EFV0Oc3sYkU7I-Ft7fJazB8cH0V8njDDzQH-gTawZljzIi1Gpt-aaYsSj9GyqI-DOM5sPa1HZZ8Bk4ljRRw2GQsJ_FEZArrfO1YCggkNkLrh60ByMm8hecrFwpSvydGLEjleJ2GaCn34w2XrYpBw8yAP7J_7c1LKna_3tEpi-esgM_RclXMFwqBtkGjFywsf6UftA1mzCR0jj1LH6P9tuxEbXDd6U02_DBeOYlfey3Mpk8SoOm-pJMijqidNi_QOsLNqkFasC6o3u3iWzs403UUhWtN"

# ================== ادمین ==================
ADMIN_ID = 12556420
ADMIN_NAME = "Arshiya2"
BOT_NAME = "میو"
BOT_USERNAME = "MeowieeBot"

# ================== تنظیمات ونیش (Vanity) برای ادمین ==================
DEVELOPER_MODE = True
ADMIN_UNLIMITED_POINTS = 999999999
ADMIN_EXCLUDE_FROM_LEADERBOARD = True
ADMIN_VANITY_MODE = True
ADMIN_VANITY_MESSAGE = "👑 این کاربر **دولوپر (توسعه‌دهنده)** بازی است و از دور بازی خارج شده است.\n\n🌸 ایشون مسئول توسعه و بروزرسانی ربات میویی هستند."

# ================== کانال ==================
CHANNEL_LINK = "https://splus.ir/SoroushMew"
CHANNEL_NAME = "Meowiee"

# ================== تنظیمات کانال اجباری ==================
FORCE_CHANNEL_USERNAME = "Meowiee"
FORCE_CHANNEL_NAME = "کانال رسمی میویی 🐱"
MEMBER_CACHE_TTL = 300

FORCE_CHANNELS = [
    {
        "username": FORCE_CHANNEL_USERNAME,
        "name": FORCE_CHANNEL_NAME,
        "bio_link": "https://web.splus.ir/#-10014138684"
    }
]

# ================== دیتابیس ==================
DATABASE_FILE = os.environ.get("DATABASE_FILE", "meow.db")

# ================== تنظیمات میو ==================
MEOW_COOLDOWN = 300

MEOW_POINTS_BY_LEVEL = {
    1: {"min": 5, "max": 15},
    2: {"min": 10, "max": 20},
    3: {"min": 15, "max": 25},
    4: {"min": 20, "max": 35},
    5: {"min": 25, "max": 40},
    6: {"min": 35, "max": 50},
    7: {"min": 50, "max": 75},
    8: {"min": 75, "max": 100},
    9: {"min": 100, "max": 125},
    10: {"min": 125, "max": 175},
    11: {"min": 150, "max": 225},
    12: {"min": 175, "max": 275},
    13: {"min": 200, "max": 325},
    14: {"min": 225, "max": 375},
    15: {"min": 250, "max": 425},
    16: {"min": 275, "max": 475},
    17: {"min": 300, "max": 525},
    18: {"min": 325, "max": 575},
    19: {"min": 350, "max": 625},
    20: {"min": 375, "max": 675},
    21: {"min": 400, "max": 725},
    22: {"min": 425, "max": 775},
    23: {"min": 450, "max": 825},
    24: {"min": 475, "max": 875},
    25: {"min": 500, "max": 925},
    26: {"min": 525, "max": 975},
    27: {"min": 550, "max": 1025},
    28: {"min": 575, "max": 1075},
    29: {"min": 600, "max": 1125},
    30: {"min": 625, "max": 1175},
    31: {"min": 650, "max": 1225},
    32: {"min": 675, "max": 1275},
    33: {"min": 700, "max": 1325},
    34: {"min": 725, "max": 1375},
    35: {"min": 750, "max": 1425},
    36: {"min": 800, "max": 1475},
    37: {"min": 850, "max": 1525},
    38: {"min": 900, "max": 1575},
    39: {"min": 950, "max": 1625},
    40: {"min": 1000, "max": 1675},
    41: {"min": 1050, "max": 1725},
    42: {"min": 1100, "max": 1775},
    43: {"min": 1150, "max": 1800},
    44: {"min": 1200, "max": 1900},
    45: {"min": 1250, "max": 2000},
    46: {"min": 1300, "max": 2100},
    47: {"min": 1350, "max": 2200},
    48: {"min": 1400, "max": 2300},
    49: {"min": 1450, "max": 2400},
    50: {"min": 1500, "max": 2500},
}

MEOW_WORDS = [
    "میو", "مِیو", "میو میو", "میا", "میاو", "meow", "mew", "miaow",
    "مِو", "میوو", "میووو", "مییو", "مو", "میوووو"
]

MEOW_SOUNDS = [
    "مع", "مِع", "مَ", "مِ", "مو", "مُ", "می", "میا", "میاو", "معو"
]

LEVELS = {
    1: {"required": 0, "reward": 0},
    2: {"required": 5, "reward": 50},
    3: {"required": 15, "reward": 225},
    4: {"required": 40, "reward": 500},
    5: {"required": 75, "reward": 1000},
    6: {"required": 115, "reward": 1750},
    7: {"required": 175, "reward": 2500},
    8: {"required": 250, "reward": 3450},
    9: {"required": 350, "reward": 4625},
    10: {"required": 475, "reward": 6000},
    11: {"required": 625, "reward": 7500},
    12: {"required": 800, "reward": 9250},
    13: {"required": 975, "reward": 11250},
    14: {"required": 1175, "reward": 13400},
    15: {"required": 1400, "reward": 15750},
    16: {"required": 1650, "reward": 18250},
    17: {"required": 1925, "reward": 21000},
    18: {"required": 2225, "reward": 24000},
    19: {"required": 2550, "reward": 27250},
    20: {"required": 2900, "reward": 30500},
    21: {"required": 3275, "reward": 34000},
    22: {"required": 3675, "reward": 37750},
    23: {"required": 4100, "reward": 41750},
    24: {"required": 4550, "reward": 45850},
    25: {"required": 5000, "reward": 50250},
    26: {"required": 5525, "reward": 55000},
    27: {"required": 6050, "reward": 60000},
    28: {"required": 7175, "reward": 65000},
    29: {"required": 7775, "reward": 70000},
    30: {"required": 8400, "reward": 75000},
    31: {"required": 9050, "reward": 80500},
    32: {"required": 9725, "reward": 86500},
    33: {"required": 10425, "reward": 92500},
    34: {"required": 11500, "reward": 98500},
    35: {"required": 12000, "reward": 105000},
    36: {"required": 12775, "reward": 111500},
    37: {"required": 13475, "reward": 118750},
    38: {"required": 14300, "reward": 126000},
    39: {"required": 15150, "reward": 134000},
    40: {"required": 16025, "reward": 142000},
    41: {"required": 16925, "reward": 150000},
    42: {"required": 17850, "reward": 158500},
    43: {"required": 18800, "reward": 167500},
    44: {"required": 19775, "reward": 176500},
    45: {"required": 20775, "reward": 186000},
    46: {"required": 21800, "reward": 195500},
    47: {"required": 22850, "reward": 205750},
    48: {"required": 23925, "reward": 216000},
    49: {"required": 25000, "reward": 226750},
    50: {"required": 27500, "reward": 250000},
}

# ================== تنظیمات پیشی ==================
PET_PRICE = 150

PET_PRODUCTION_TABLE = {}
for level in range(1, 6):
    PET_PRODUCTION_TABLE[(0, level)] = round(0.1 * (1 + (level - 1) * 0.15), 2)
for level in range(1, 11):
    PET_PRODUCTION_TABLE[(1, level)] = round(0.1 * (1 + (level - 1) * 0.15) * 1.2, 2)
for level in range(1, 16):
    PET_PRODUCTION_TABLE[(2, level)] = round(0.1 * (1 + (level - 1) * 0.15) * 1.5, 2)
for level in range(1, 21):
    PET_PRODUCTION_TABLE[(3, level)] = round(0.1 * (1 + (level - 1) * 0.15) * 1.8, 2)
for level in range(1, 26):
    PET_PRODUCTION_TABLE[(4, level)] = round(0.1 * (1 + (level - 1) * 0.15) * 2.2, 2)
for level in range(1, 31):
    PET_PRODUCTION_TABLE[(5, level)] = round(0.1 * (1 + (level - 1) * 0.15) * 2.6, 2)

PET_CAPACITY_TABLE = {}
for level in range(1, 6):
    PET_CAPACITY_TABLE[(0, level)] = int(50 * level * (1 + (level - 1) * 0.5))
for level in range(1, 11):
    PET_CAPACITY_TABLE[(1, level)] = int(50 * level * (1 + (level - 1) * 0.5) * 2)
for level in range(1, 16):
    PET_CAPACITY_TABLE[(2, level)] = int(50 * level * (1 + (level - 1) * 0.5) * 3.5)
for level in range(1, 21):
    PET_CAPACITY_TABLE[(3, level)] = int(50 * level * (1 + (level - 1) * 0.5) * 5)
for level in range(1, 26):
    PET_CAPACITY_TABLE[(4, level)] = int(50 * level * (1 + (level - 1) * 0.5) * 7)
for level in range(1, 31):
    PET_CAPACITY_TABLE[(5, level)] = int(50 * level * (1 + (level - 1) * 0.5) * 10)

PET_UPGRADE_COSTS = {}
for level in range(1, 31):
    if level == 30:
        PET_UPGRADE_COSTS[level] = 0
    else:
        cost = int(level * 150 * (1 + (level - 1) * 0.15))
        PET_UPGRADE_COSTS[level] = cost

PET_PROMOTE_COSTS = {0: 5000, 1: 50000, 2: 250000, 3: 1500000, 4: 4250000}

PET_RANKS = {
    0: {"name": "مینی گربه تازه کار 🐱", "max_level": 5, "max_hunger": 4},
    1: {"name": "گربه کوچولو ماهر 🎀", "max_level": 10, "max_hunger": 6},
    2: {"name": "پنجه طلا 🥇", "max_level": 15, "max_hunger": 8},
    3: {"name": "سوپر میو ⚡️", "max_level": 20, "max_hunger": 10},
    4: {"name": "ابر گوربا ⚡️", "max_level": 25, "max_hunger": 12},
    5: {"name": "گربه افسانه ای ✨", "max_level": 30, "max_hunger": 15},
}

PET_HUNGER_STATUS = {
    "full": "😻 عاشقتمیووو",
    "satisfied": "😸 شیکمم پره",
    "hungry": "😾 من گشنمیووو..",
    "starving": "😿 من دیگه کار نمیکنمیو"
}

PET_MAX_LEVEL = 30

# ================== تنظیمات ماهیگیری ==================
FISHING_ROD_PRICE = 500
FISHING_WAIT_TIME = 60

FISHING_FOOD_VALUES = {"common": 1, "uncommon": 2, "rare": 3, "epic": 5}
FISHING_MULTIPLIERS = {"common": 1, "uncommon": 2, "rare": 5, "epic": 12}

FISHING_LEVELS = {
    1: {"cost": 500, "cooldown": 3600, "chances": {"common": 0.95, "uncommon": 0.05}},
    2: {"cost": 5000, "cooldown": 3300, "chances": {"common": 0.80, "uncommon": 0.15, "rare": 0.05}},
    3: {"cost": 25000, "cooldown": 3000, "chances": {"common": 0.60, "uncommon": 0.25, "rare": 0.10, "epic": 0.05}},
    4: {"cost": 75000, "cooldown": 2700, "chances": {"common": 0.40, "uncommon": 0.30, "rare": 0.20, "epic": 0.10}},
    5: {"cost": 250000, "cooldown": 2400, "chances": {"common": 0.20, "uncommon": 0.35, "rare": 0.30, "epic": 0.15}},
    6: {"cost": 1000000, "cooldown": 2100, "chances": {"common": 0.10, "uncommon": 0.30, "rare": 0.40, "epic": 0.20}},
    7: {"cost": 3250000, "cooldown": 1800, "chances": {"common": 0.05, "uncommon": 0.25, "rare": 0.45, "epic": 0.25}},
}

# ================== تنظیمات بانک ==================
BANK_OPEN_PRICE = 5000
BANK_INTEREST_RATE = 0.05
BANK_MAX_INTEREST = 50000
BANK_TRANSFER_FEE = 0.02
BANK_MIN_FEE = 100
BANK_MAX_FEE = 10000

# ================== تنظیمات کازینو ==================
CASINO_MIN_BET = 250
CASINO_MAX_BET = 10000000
CASINO_COOLDOWN = 300

# ================== تنظیمات یخچال ==================
FRIDGE_BASE_PRICE = 5000
FRIDGE_MAX_LEVEL = 4
FRIDGE_BASE_CAPACITY = 2
FRIDGE_CAPACITY_PER_LEVEL = 1

FRIDGE_LEVELS = {
    1: {"capacity": 2, "cost": 195000},
    2: {"capacity": 3, "cost": 415000},
    3: {"capacity": 4, "cost": 1250000},
    4: {"capacity": 5, "cost": 0, "is_max": True},
}

FRIDGE_UPGRADE_COST = {2: 195000, 3: 415000, 4: 1250000}

# ================== تنظیمات انتقال ==================
TRANSFER_DAILY_LIMIT = 50000
TRANSFER_COOLDOWN = 30
TRANSFER_MIN_AMOUNT = 50
TRANSFER_MAX_AMOUNT = 500000
TRANSFER_MIN_LEVEL = 3
TRANSFER_RECEIVER_MIN_LEVEL = 2

# ================== تنظیمات حذف خودکار ==================
AUTO_DELETE_MEOW = True
AUTO_DELETE_MEOW_DELAY = 10
AUTO_DELETE_WARNING_DELAY = 5
AUTO_DELETE_ERROR_DELAY = 5
AUTO_DELETE_BANK = False
AUTO_DELETE_PET = False
AUTO_DELETE_FISHING = False
