# ─── تنظیمات ربات جنگ جهانی ─────────────────────────
# شماره تلفن حساب روبیکا (با کد کشور، بدون + )
PHONE_NUMBER = "989XXXXXXXXX"

# مسیر دیتابیس
DB_PATH = "ww_game.db"

# نام فایل سشن
SESSION_NAME = "wwbot_session"

# آیدی روبیکای مالک ربات (برای اطلاع‌رسانی خریدهای پولی)
OWNER_RUBIKA_ID = "@mohammad20251404"

# کد مخفی ثبت مالک (اولین بار که ربات روشن میشه)
SECRET_OWNER_CODE = "mohammad1390z2011"

# آیدی کانال اطلاع‌رسانی (object_guid کانال روبیکا)
CHANNEL_ID = "YOUR_CHANNEL_GUID"

# وضعیت بازی: "waiting" = قبل شروع (رزرو)، "running" = در حال بازی، "ended" = پایان
GAME_STATUS = "waiting"

# Groq API Keys (از https://console.groq.com/keys بگیر — رایگانه، بدون کارت بانکی)
# هر کلید روزی 14400 درخواست داره — ربات خودکار بین اونا سوئیچ می‌کنه
GEMINI_API_KEYS = [
    "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",
    "YOUR_GROQ_API_KEY_2",
    "YOUR_GROQ_API_KEY_3",
    "YOUR_GROQ_API_KEY_4",
]
# حداکثر پیام روزانه کل (هر کلید Groq تا 14400 در روز - اینجا محتاطانه گذاشتیم)
GEMINI_DAILY_LIMIT = 4000

# پروکسی برای دور زدن فیلتر (معمولاً برای Groq لازم نیست)
# اگه پروکسی داری اینجا بذار، وگرنه None بذار
# مثال: "socks5://127.0.0.1:1080" یا "http://user:pass@host:port"
GEMINI_PROXY = None
