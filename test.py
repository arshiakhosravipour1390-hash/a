# test_force_join.py
import asyncio
import time
from typing import Set
from splusthon import SoroushClient
from splusthon.sessions import StringSession
from splusthon.tl import functions, types
from config import BOT_SESSION, FORCE_CHANNELS

# ============================================================
# ✅ کش اعضای کانال (همون کدی که توی ربات اصلی استفاده میشه)
# ============================================================

_member_cache: dict = {}
_cache_timestamp: dict = {}
_cache_ttl = 300  # ۵ دقیقه

def get_cached_members(channel_id: int) -> Set[int]:
    return _member_cache.get(channel_id, set())

def set_cached_members(channel_id: int, members: Set[int]):
    _member_cache[channel_id] = members
    _cache_timestamp[channel_id] = time.time()

def is_cache_expired(channel_id: int) -> bool:
    if channel_id not in _cache_timestamp:
        return True
    return (time.time() - _cache_timestamp[channel_id]) > _cache_ttl

# ============================================================
# ✅ توابع تست
# ============================================================

async def fetch_channel_members(client, channel_id: int) -> Set[int]:
    """دریافت همه اعضای یک کانال با GetParticipantsRequest"""
    try:
        channel = await client.get_entity(channel_id)
        print(f"   📢 کانال: {channel.title}")
        print(f"   👥 تعداد کل اعضا: {channel.participants_count}")
        print("   ⏳ در حال دریافت لیست اعضا...")
        
        members = set()
        offset = 0
        limit = 200
        total_fetched = 0
        
        while True:
            result = await client(
                functions.channels.GetParticipantsRequest(
                    channel=channel,
                    filter=types.ChannelParticipantsRecent(),
                    offset=offset,
                    limit=limit,
                    hash=0
                )
            )
            
            for participant in result.participants:
                if hasattr(participant, 'user_id'):
                    members.add(participant.user_id)
                elif hasattr(participant, 'id'):
                    members.add(participant.id)
            
            total_fetched += len(result.participants)
            print(f"      ... {total_fetched} عضو دریافت شد")
            
            if len(result.participants) < limit:
                break
            
            offset += len(result.participants)
        
        print(f"   ✅ {len(members)} عضو دریافت شد!")
        return members
        
    except Exception as e:
        print(f"   ❌ خطا: {e}")
        return set()

async def update_member_cache(client):
    """به‌روزرسانی کش اعضای همه کانال‌ها"""
    print("\n🔄 در حال به‌روزرسانی کش اعضای کانال...")
    print("=" * 60)
    
    for channel_config in FORCE_CHANNELS:
        channel_id = channel_config["id"]
        channel_name = channel_config["name"]
        print(f"\n📌 کانال: {channel_name}")
        print("-" * 40)
        
        members = await fetch_channel_members(client, channel_id)
        set_cached_members(channel_id, members)
    
    print("\n" + "=" * 60)
    print("✅ کش اعضای کانال به‌روزرسانی شد!")

def check_membership(user_id: int) -> bool:
    """بررسی اینکه کاربر عضو همه کانال‌های اجباری هست یا نه"""
    print("\n🔍 بررسی عضویت کاربر...")
    print("-" * 40)
    
    for channel_config in FORCE_CHANNELS:
        channel_id = channel_config["id"]
        channel_name = channel_config["name"]
        
        members = get_cached_members(channel_id)
        is_member = user_id in members
        
        status = "✅" if is_member else "❌"
        print(f"   {status} {channel_name}: {'عضو هست' if is_member else 'عضو نیست'}")
        
        if not is_member:
            print(f"\n❌ کاربر در کانال '{channel_name}' عضو نیست!")
            return False
    
    print("\n✅ کاربر در همه کانال‌ها عضو هست!")
    return True

# ============================================================
# ✅ تابع اصلی تست
# ============================================================

async def main():
    print("=" * 60)
    print("🐱 تست سیستم Force Join")
    print("=" * 60)
    
    client = SoroushClient(StringSession(BOT_SESSION))
    await client.start()
    
    me = await client.get_me()
    print(f"✅ ربات متصل شد: @{me.username or me.first_name}")
    print(f"📌 ID ربات: {me.id}")
    print("=" * 60)
    
    # ====== تست ۱: دریافت اعضا ======
    print("\n📥 تست ۱: دریافت اعضای کانال‌ها")
    print("=" * 60)
    await update_member_cache(client)
    
    # ====== تست ۲: بررسی عضویت کاربر ======
    print("\n📥 تست ۲: بررسی عضویت کاربر")
    print("=" * 60)
    
    TEST_USER_ID = 12556420  # ← آیدی خودت
    print(f"👤 کاربر تست: {TEST_USER_ID}")
    
    is_member = check_membership(TEST_USER_ID)
    
    # ====== تست ۳: نمایش آمار ======
    print("\n📥 تست ۳: آمار کش")
    print("=" * 60)
    for channel_config in FORCE_CHANNELS:
        channel_id = channel_config["id"]
        channel_name = channel_config["name"]
        members = get_cached_members(channel_id)
        print(f"   📊 {channel_name}: {len(members)} عضو در کش")
    
    # ====== تست ۴: بررسی سرعت ======
    print("\n📥 تست ۴: بررسی سرعت بررسی عضویت")
    print("=" * 60)
    
    import time
    start = time.time()
    
    for _ in range(100):
        check_membership(TEST_USER_ID)
    
    elapsed = time.time() - start
    print(f"\n⏱️ زمان انجام ۱۰۰ بار بررسی: {elapsed:.3f} ثانیه")
    print(f"⚡ میانگین هر بررسی: {elapsed/100:.4f} ثانیه")
    
    # ====== نتیجه نهایی ======
    print("\n" + "=" * 60)
    print("📋 **نتیجه نهایی تست:**")
    print("-" * 40)
    
    if is_member:
        print("   ✅ کاربر عضو همه کانال‌هاست")
    else:
        print("   ❌ کاربر عضو همه کانال‌ها نیست")
    
    print(f"   📊 تعداد کل اعضای کش شده: {sum(len(get_cached_members(ch['id'])) for ch in FORCE_CHANNELS)}")
    print("=" * 60)
    
    await client.disconnect()
    print("\n🏁 تست به پایان رسید!")

if __name__ == "__main__":
    asyncio.run(main())