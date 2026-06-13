# ─── تنظیمات ربات جنگ جهانی ─────────────────────────
# شماره تلفن حساب روبیکا (با کد کشور، بدون + )
PHONE_NUMBER = "09150936583"

# مسیر دیتابیس
DB_PATH = "ww_game.db"

# نام فایل سشن
SESSION_NAME = "wwbot_session"

# آیدی روبیکای مالک ربات (برای اطلاع‌رسانی خریدهای پولی)
OWNER_RUBIKA_ID = "@mohammad20251404"

# کد مخفی ثبت مالک (اولین بار که ربات روشن میشه)
SECRET_OWNER_CODE = "mohammad1390z2011"

# آیدی کانال اطلاع‌رسانی (object_guid کانال روبیکا)
CHANNEL_ID = "@wordwar32567"

# وضعیت بازی: "waiting" = قبل شروع (رزرو)، "running" = در حال بازی، "ended" = پایان
GAME_STATUS = "waiting"

# Google Gemini API Keys (از https://aistudio.google.com/app/apikey بگیر — رایگانه)
# هر کلید روزی 1500 درخواست داره — ربات خودکار بین اونا سوئیچ می‌کنه
GEMINI_API_KEYS = [
    "YOUR_GEMINI_API_KEY_1",
    "YOUR_GEMINI_API_KEY_2",
    "YOUR_GEMINI_API_KEY_3",
    "YOUR_GEMINI_API_KEY_4",
]
# حداکثر پیام روزانه کل (6000 = 4 کلید × 1500)
GEMINI_DAILY_LIMIT = 6000

# پروکسی برای دور زدن فیلتر Gemini (اختیاری)
# اگه پروکسی داری اینجا بذار، وگرنه None بذار
# مثال: "socks5://127.0.0.1:1080" یا "http://user:pass@host:port"
GEMINI_PROXY = None
