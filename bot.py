import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rubpy import Client
from config import PHONE_NUMBER, SESSION_NAME, SECRET_OWNER_CODE, CHANNEL_ID
from database import setup_db, get_conn, seed_all
from game import *
from game import cmd_full_profile, cmd_ai_help, admin_ai_stats, cmd_reserve, cmd_reservations_list, get_game_status, admin_start_game, admin_end_game, admin_restart_game, admin_set_game_timer, admin_cancel_reserve
# توابع فروشگاه بخش‌بخش از game ایمپورت میشن با *

# ─── راه‌اندازی دیتابیس ──────────────────────────────
setup_db()
seed_all()


def handle(chat_id, user_id, username, text):
    if not text or not chat_id:
        return None

    # ─── ثبت مالک با کد مخفی ─────────────────────────
    if text.strip() == SECRET_OWNER_CODE:
        conn = get_conn()
        existing = conn.execute("SELECT id FROM admins WHERE is_owner=1").fetchone()
        if existing:
            conn.close()
            return "❌ مالک قبلاً ثبت شده."
        conn.execute(
            "INSERT OR IGNORE INTO admins (user_id, name, is_owner) VALUES (?,?,1)",
            (str(user_id), str(username))
        )
        conn.commit()
        conn.close()
        return f"👑 تبریک! شما به عنوان مالک ربات ثبت شدید.\nآیدی شما: {user_id}"

    parts = text.strip().split()
    cmd = parts[0].lower()

    # ════════════════════════════════════════════
    #  دستورات اصلی
    # ════════════════════════════════════════════

    # ── میانبرهای عددی ──────────────────────────────
    if text.strip() == "1": return get_countries_list()
    if text.strip() == "2": return cmd_profile(user_id)
    if text.strip() == "3": return cmd_economy(user_id)
    if text.strip() == "4": return cmd_army(user_id)
    if text.strip() == "5": return cmd_buildings(user_id)
    if text.strip() == "6": return cmd_shop(user_id)
    if text.strip() == "7": return cmd_daily(user_id)
    if text.strip() == "8": return cmd_leaderboard()
    if text.strip() == "9": return cmd_alliance_info(user_id)
    if text.strip() == "10": return cmd_groups_list()

    # بلاک دستورات بازیکن برای ادمین
    PLAYER_ONLY_CMDS = ["/کشور","/country","/قاره_امریکا","/قاره_آمریکا",
        "/قاره_آسیا","/قاره_اروپا","/قاره_آفریقا","/پروفایل","/profile",
        "/اقتصاد","/economy","/ارتش","/army","/ساختمانها","/buildings",
        "/روزانه","/daily","/اتحاد","/alliance","/ثبت_گروهک",
        "/خرید_تجهیز","/buy_equip","/خرید_ساختمان","/buy_building",
        "/خرید_نیرو","/buy_troop","/خرید_نفتکش","/buy_tanker",
        "/رتبه_بندی","/leaderboard",
        "/فروشگاه_موشک","/فروشگاه_جنگنده","/فروشگاه_بمب_افکن",
        "/فروشگاه_دریایی","/فروشگاه_پدافند","/فروشگاه_زمینی",
        "/فروشگاه_پرتاب","/فروشگاه_بمب","/فروشگاه_پایگاه",
        "/فروشگاه_ترابری","/فروشگاه_ساختمان","/فروشگاه_نیرو",
        "/فروشگاه_نفتکش",
    ]
    if cmd in PLAYER_ONLY_CMDS and is_admin(user_id):
        return "👮 شما ادمین هستید.\n\nبرای پنل مدیریت:\n/ادمین"

    if cmd in ("/شروع", "/start"):
        # ادمین و اونر: فقط پنل مدیریتی
        if is_admin(user_id):
            return admin_panel_main(user_id)
        # بازیکن عادی: منوی بازی
        return """🌍 *به ربات جنگ جهانی خوش آمدید!*

━━━━━━━━━━━━━━

📋 *منوی اصلی:*

1️⃣ /کشور — انتخاب کشور
2️⃣ /پروفایل — پروفایل کشور
3️⃣ /اقتصاد — وضعیت اقتصادی
4️⃣ /ارتش — ارتش و تجهیزات
5️⃣ /ساختمانها — ساختمان‌ها
6️⃣ /فروشگاه — فروشگاه نظامی
7️⃣ /روزانه — پاداش روزانه 🎁
8️⃣ /رتبه_بندی — لیدربورد 🏆
9️⃣ /اتحاد — وضعیت اتحاد
🔟 /گروهکها — لیست گروهک‌ها

━━━━━━━━━━━━━━

🛍 *فروشگاه‌ها:*
/فروشگاه_موشک | /فروشگاه_جنگنده
/فروشگاه_دریایی | /فروشگاه_پدافند
/فروشگاه_زمینی | /فروشگاه_ساختمان
/فروشگاه_نیرو | /فروشگاه_نفتکش
/فروشگاه_ویژه — آیتم‌های پولی 💎

━━━━━━━━━━━━━━

☠ *گروهک‌ها:*
/ثبت_گروهک [نام] — عضویت
/پروفایل_گروهک — پروفایل
/گروهک_فروشگاه — فروشگاه

━━━━━━━━━━━━━━

📖 /قوانین | /راهنما
💡 برای شروع عدد *1* بفرست!"""

    elif cmd in ("/راهنما", "/help"):
        return HELP

    elif cmd in ("/قوانین", "/rules"):
        return RULES

    elif cmd in ("/قوانین_تنگه", "/rules_strait"):
        return """🌊 *قوانین تنگه‌های جهانی*
━━━━━━━━━━━━━━━

❤️ تنگه هرمز | 🇮🇷 ایران
اهمیت: ۴۵٪ | نفت: ۲۰٪ جهان
🚨 بسته = قیمت نفت و تجهیزات ۲.۵ برابر
کشورهای بدون اجازه: روزانه ۵٪ رضایت کم می‌شود

❤️ باب‌المندب | 🇾🇪 یمن
اهمیت: ۳۰٪ | نفت: ۶-۷M بشکه/روز
🚨 بسته = تجهیزات غیرمتحدان ۲ برابر

❤️ کانال سوئز | 🇪🇬 مصر
اهمیت: ۱۰٪ | تجارت: ۱۲٪ جهان
🚨 بسته = هزینه تجارت +۳۰٪

❤️ بسفر و داردانل | 🇹🇷 ترکیه
اهمیت: ۲۰٪
🚨 بسته = تجهیزات غیرمتحدان ۱.۵ برابر

❤️ تنگه مالاکا | 🇲🇾 مالزی
اهمیت: ۳۰-۴۰٪ تجارت جهانی
🚨 بسته = بحران انرژی شرق آسیا

❤️ جبل‌الطارق | 🇪🇸🇬🇧
🚨 بسته = تجارت اروپا-آمریکا ۶۰٪ کاهش

❤️ کانال پاناما | 🇺🇸
🚨 بسته = تجارت آمریکا-آسیا ۵۰٪ کاهش"""

    elif cmd in ("/قوانین_تحریم", "/rules_sanction"):
        return """📉 *قوانین تحریم بین‌المللی*
━━━━━━━━━━━━━━━

📌 شرایط اجرا:
• حداقل ۵ کشور موافقت کنند
• پس از تأیید ادمین اعمال می‌شود

⚠️ اثرات تحریم:
• ۱۵٪ کاهش رضایت مردمی
• عدم امکان خرید از کشورهای تحریم‌کننده
• کاهش ۲۰٪ درآمد صادرات نفت

⏳ مدت: ۷ روز

🚨 لغو: پایان مدت تحریم"""


    elif cmd in ("/پروفایل", "/profile"):
        return cmd_profile(user_id)

    elif cmd in ("/پروفایل_کامل", "/full_profile", "/fp"):
        return cmd_full_profile(user_id)

    elif cmd in ("/کشور", "/country"):
        if len(parts) == 1:
            return get_countries_list()
        try:
            cid = int(parts[1])
        except:
            return "❌ شماره کشور باید عدد باشه.\nمثال: /کشور 3"
        result = select_country(user_id, cid, username)
        if isinstance(result, dict):
            return result["msg"]
        return result

    elif cmd in ("/قاره_امریکا", "/قاره_آمریکا", "/continent_america"):
        return get_countries_by_continent("آمریکا")

    elif cmd in ("/قاره_آسیا", "/continent_asia"):
        return get_countries_by_continent("آسیا")

    elif cmd in ("/قاره_اروپا", "/continent_europe"):
        return get_countries_by_continent("اروپا")

    elif cmd in ("/قاره_آفریقا", "/continent_africa"):
        return get_countries_by_continent("آفریقا")

    elif cmd in ("/اقتصاد", "/economy"):
        return cmd_economy(user_id)

    elif cmd in ("/ارتش", "/army"):
        return cmd_army(user_id)

    elif cmd in ("/ساختمانها", "/buildings"):
        return cmd_buildings(user_id)

    elif cmd in ("/فروشگاه", "/shop"):
        return cmd_shop(user_id)

    elif cmd in ("/فروشگاه_موشک", "/shop_missile"):
        return cmd_shop_missile(user_id)

    elif cmd in ("/فروشگاه_جنگنده", "/shop_fighter"):
        return cmd_shop_fighter(user_id)

    elif cmd in ("/فروشگاه_بمب_افکن", "/shop_bomber"):
        return cmd_shop_bomber(user_id)

    elif cmd in ("/فروشگاه_دریایی", "/shop_navy"):
        return cmd_shop_navy(user_id)

    elif cmd in ("/فروشگاه_پدافند", "/shop_defense"):
        return cmd_shop_defense(user_id)

    elif cmd in ("/فروشگاه_زمینی", "/shop_ground"):
        return cmd_shop_ground(user_id)

    elif cmd in ("/فروشگاه_پرتاب", "/shop_launcher"):
        return cmd_shop_launcher(user_id)

    elif cmd in ("/فروشگاه_بمب", "/shop_bomb"):
        return cmd_shop_bomb(user_id)

    elif cmd in ("/فروشگاه_پایگاه", "/shop_base"):
        return cmd_shop_base(user_id)

    elif cmd in ("/فروشگاه_ترابری", "/shop_transport"):
        return cmd_shop_transport(user_id)

    elif cmd in ("/فروشگاه_ساختمان", "/shop_buildings"):
        return cmd_shop_buildings(user_id)

    elif cmd in ("/فروشگاه_نیرو", "/shop_troops"):
        return cmd_shop_troops(user_id)

    elif cmd in ("/فروشگاه_نفتکش", "/shop_tankers"):
        return cmd_shop_tankers(user_id)

    # ─── فروشگاه ویژه پولی ───
    elif cmd in ("/فروشگاه_ویژه", "/shop_premium"):
        return cmd_shop_premium(user_id)

    elif cmd in ("/خرید_ویژه", "/buy_premium"):
        if len(parts) < 2:
            return "⚠️ /خرید_ویژه [کد_آیتم]\nبرای دیدن کدها: /فروشگاه_ویژه"
        return cmd_buy_premium(user_id, username, parts[1])

    elif cmd in ("/تایید_سفارش", "/confirm_order"):
        if len(parts) < 2:
            return "⚠️ /تایید_سفارش [کد۵رقمی]"
        return cmd_confirm_order(user_id, parts[1])

    elif cmd in ("/لغو_سفارش", "/cancel_order"):
        return cmd_cancel_order(user_id)

    # ─── خریدها ───
    elif cmd in ("/خرید_تجهیز", "/buy_equip"):
        if len(parts) < 3:
            return "⚠️ /خرید_تجهیز [شناسه] [تعداد]\nمثال: /خرید_تجهیز 5 2"
        try:
            return buy_equipment(user_id, int(parts[1]), int(parts[2]))
        except:
            return "❌ فرمت اشتباه. مثال: /خرید_تجهیز 5 2"

    elif cmd in ("/خرید_ساختمان", "/buy_building"):
        if len(parts) < 3:
            return "⚠️ /خرید_ساختمان [شناسه] [تعداد]"
        try:
            return buy_building(user_id, int(parts[1]), int(parts[2]))
        except:
            return "❌ فرمت اشتباه."

    elif cmd in ("/خرید_نیرو", "/buy_troop"):
        if len(parts) < 3:
            return "⚠️ /خرید_نیرو [شناسه] [تعداد]"
        try:
            return buy_troop(user_id, int(parts[1]), int(parts[2]))
        except:
            return "❌ فرمت اشتباه."

    elif cmd in ("/خرید_نفتکش", "/buy_tanker"):
        if len(parts) < 3:
            return "⚠️ /خرید_نفتکش [شناسه] [تعداد]"
        try:
            return buy_tanker(user_id, int(parts[1]), int(parts[2]))
        except:
            return "❌ فرمت اشتباه."

    # ─── روزانه ───
    elif cmd in ("/روزانه", "/daily"):
        return cmd_daily(user_id)

    # ─── رتبه‌بندی ───
    elif cmd in ("/رتبه_بندی", "/leaderboard"):
        return cmd_leaderboard()

    # ─── انتقال پول ───
    elif cmd in ("/انتقال", "/transfer"):
        if len(parts) < 3:
            return "⚠️ /انتقال [ID_کشور] [مبلغ]\nمثال: /انتقال 5 1000000000"
        try:
            return cmd_transfer_money(user_id, int(parts[1]), int(parts[2]))
        except:
            return "❌ فرمت اشتباه."

    # ─── تنگه‌ها ───
    elif cmd in ("/تنگه_ها", "/straits"):
        return cmd_straits_info()

    # ─── اتحادها ───
    elif cmd in ("/اتحاد", "/alliance"):
        return cmd_alliance_info(user_id)

    elif cmd in ("/ایجاد_اتحاد", "/create_alliance"):
        if len(parts) < 2:
            return "⚠️ /ایجاد_اتحاد [نام اتحاد]"
        return cmd_create_alliance(user_id, " ".join(parts[1:]))

    elif cmd in ("/دعوت_اتحاد", "/alliance_invite"):
        if len(parts) < 2:
            return "⚠️ /دعوت_اتحاد [ID_کشور]"
        try:
            return cmd_alliance_invite(user_id, int(parts[1]))
        except:
            return "❌ فرمت اشتباه."

    elif cmd in ("/خروج_اتحاد", "/leave_alliance"):
        return cmd_leave_alliance(user_id)

    # ─── گروهک‌ها ───
    elif cmd in ("/ثبت_گروهک", "/join_group"):
        if len(parts) < 2:
            t = "⚠️ /ثبت_گروهک [نام گروهک]\n\n"
            t += "☠ گروهک‌های تروریستی:\n"
            t += " | ".join(TERROR_GROUPS) + "\n\n"
            t += "💻 گروهک‌های هکری:\n"
            t += " | ".join(HACKER_GROUPS)
            return t
        return cmd_join_group(user_id, username, " ".join(parts[1:]))

    elif cmd in ("/پروفایل_گروهک", "/group_profile"):
        return cmd_group_profile(user_id)

    elif cmd in ("/گروهک_فروشگاه", "/group_shop"):
        return cmd_group_shop(user_id)

    elif cmd in ("/گروهک_خرید", "/group_buy"):
        if len(parts) < 2:
            return "⚠️ /گروهک_خرید [شماره]\nبرای دیدن لیست: /گروهک_فروشگاه"
        try:
            return cmd_group_buy(user_id, int(parts[1]))
        except:
            return "❌ فرمت اشتباه. مثال: /گروهک_خرید 3"

    elif cmd in ("/گروهک_عملیات", "/group_ops"):
        return cmd_group_ops(user_id)

    elif cmd in ("/گروهک_مستقر", "/group_host"):
        if len(parts) < 2:
            return "⚠️ /گروهک_مستقر [نام کشور]\nمثال: /گروهک_مستقر ایران"
        return cmd_group_set_host(user_id, " ".join(parts[1:]))

    elif cmd in ("/گروهکها", "/groups"):
        txt, _ = cmd_groups_numbered()
        return txt

    elif cmd in ("/vip_کشورها", "/vip_countries"):
        return cmd_vip_countries()

    elif cmd in ("/vip_گروهکها", "/vip_groups"):
        return cmd_vip_groups()

    # ─── بیانیه و تگ‌ها ───
    elif cmd in ("/بیانیه", "/declaration"):
        return cmd_declaration_form(user_id)

    elif cmd in ("/تگها", "/tags"):
        return cmd_tags(user_id)

    # ════════════════════════════════════════════
    #  دستورات ادمین
    # ════════════════════════════════════════════

    elif cmd in ("/ادمین", "/admin", "/پنل"):
        return admin_panel_main(user_id)

    elif cmd in ("/پنل_کشورها",):
        return admin_panel_countries(user_id)

    elif cmd in ("/پنل_بازیکنان",):
        return admin_panel_players(user_id)

    elif cmd in ("/پنل_اقتصاد",):
        return admin_panel_economy(user_id)

    elif cmd in ("/پنل_تجهیزات",):
        return admin_panel_equip(user_id)

    elif cmd in ("/پنل_vip",):
        return admin_panel_vip(user_id)

    elif cmd in ("/پنل_ادمینها",):
        return admin_panel_admins(user_id)

    elif cmd in ("/اطلاعات_کشور", "/country_info"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /اطلاعات_کشور [ID]"
        try: return admin_country_full_info(user_id, int(parts[1]))
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/اعطای_نیرو", "/give_troop"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 4: return "⚠️ /اعطای_نیرو [country_id] [troop_id] [تعداد]"
        try: return admin_give_troop(int(parts[1]), int(parts[2]), int(parts[3]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/تنظیم_رضایت", "/set_satisfaction"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 3: return "⚠️ /تنظیم_رضایت [country_id] [درصد]"
        try: return admin_set_satisfaction(int(parts[1]), int(parts[2]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/اعطای_vip", "/give_vip"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 4: return "⚠️ /اعطای_vip [country_id] [نوع] [روز]"
        try: return admin_give_vip(int(parts[1]), parts[2], int(parts[3]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/حذف_تجهیز", "/remove_equip"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 4: return "⚠️ /حذف_تجهیز [country_id] [eq_id] [تعداد]"
        try: return admin_remove_equip(int(parts[1]), int(parts[2]), int(parts[3]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/اخراج_بازیکن", "/kick_player"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /اخراج_بازیکن [user_id]"
        return admin_kick_player(parts[1], user_id)

    elif cmd in ("/اطلاعات_بازیکن", "/player_info"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /اطلاعات_بازیکن [user_id]"
        return admin_player_info(parts[1], user_id)

    elif cmd in ("/ادمین_قدیمی",):
        if not is_admin(user_id):
            return "❌ دسترسی ندارید."
        return """👮 *پنل ادمین:*

🏳 کشور:
/افزودن_کشور [نام] [پرچم] [قاره]
/حذف_کشور [شناسه]
/ویرایش_کشور [شناسه] [فیلد] [مقدار]

💰 اقتصاد:
/افزودن_پول [country_id] [مبلغ]
/افزودن_همه [پول] [نفت] [رضایت]
/تنظیم_روزانه [پول] [نفت] [رضایت]
/تیک_روزانه - اجرای tick روزانه

🎁 تجهیزات:
/اعطای_تجهیز [country_id] [eq_id] [تعداد]

💎 سفارشات پولی:
/سفارشات - لیست سفارشات در انتظار
/کد_تایید [ID_سفارش] [کد|auto]

🚫 تحریم:
/تحریم [country_id]
/رفع_تحریم [country_id]

🌊 تنگه:
/تنگه [نام] [close|open]

💾 بکاپ:
/بکاپ | /لیست_بکاپ | /بازگردانی [شناسه]

👑 اونر:
/افزودن_ادمین [user_id] [نام]
/حذف_ادمین [user_id] | /ادمینها"""

    elif cmd in ("/افزودن_کشور", "/add_country"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 4: return "⚠️ /افزودن_کشور [نام] [پرچم] [قاره]"
        return add_country(parts[1], parts[2], " ".join(parts[3:]), user_id)

    elif cmd in ("/حذف_کشور", "/del_country"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /حذف_کشور [شناسه]"
        return del_country(int(parts[1]), user_id)

    elif cmd in ("/ویرایش_کشور", "/edit_country"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 4: return "⚠️ /ویرایش_کشور [شناسه] [فیلد] [مقدار]"
        numeric = {"money", "oil", "satisfaction", "max_players", "daily_oil"}
        val = int(parts[3]) if parts[2] in numeric else parts[3]
        return edit_country(int(parts[1]), parts[2], val, user_id)

    elif cmd in ("/افزودن_پول", "/add_money"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 3: return "⚠️ /افزودن_پول [country_id] [مبلغ]"
        try: return admin_add_money(int(parts[1]), int(parts[2]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/افزودن_همه", "/add_all"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 4: return "⚠️ /افزودن_همه [پول] [نفت] [رضایت]"
        return admin_add_all(int(parts[1]), int(parts[2]), int(parts[3]), user_id)

    elif cmd in ("/تنظیم_روزانه", "/set_daily"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 4: return "⚠️ /تنظیم_روزانه [پول] [نفت] [رضایت]"
        return admin_set_daily(int(parts[1]), int(parts[2]), int(parts[3]), user_id)

    elif cmd in ("/تیک_روزانه", "/daily_tick"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        return admin_daily_tick(user_id)

    elif cmd in ("/اعطای_تجهیز", "/give_equip"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 4: return "⚠️ /اعطای_تجهیز [country_id] [eq_id] [تعداد]"
        try: return admin_give_equip(int(parts[1]), int(parts[2]), int(parts[3]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/تحریم", "/sanction"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /تحریم [country_id]"
        return admin_set_sanction(int(parts[1]), True, user_id)

    elif cmd in ("/رفع_تحریم", "/unsanction"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /رفع_تحریم [country_id]"
        return admin_set_sanction(int(parts[1]), False, user_id)

    # ─── سفارشات پولی (ادمین) ───
    elif cmd in ("/سفارشات", "/admin_orders"):
        return admin_list_orders(user_id)

    elif cmd in ("/کد_تایید", "/issue_code"):
        if len(parts) < 3:
            return "⚠️ /کد_تایید [ID_سفارش] [کد۵رقمی|auto]"
        try:
            return admin_issue_code(int(parts[1]), parts[2], user_id)
        except:
            return "❌ فرمت اشتباه."

    # ─── کنترل تنگه‌ها (ادمین) ───
    elif cmd in ("/تنگه", "/toggle_strait"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 3: return "⚠️ /تنگه [نام_تنگه] [close|open]"
        strait_name = " ".join(parts[1:-1])
        action = parts[-1].lower()
        if action not in ("close", "open"):
            return "❌ عملیات باید close یا open باشد."
        return admin_toggle_strait(strait_name, action == "close", user_id, strait_name)

    # ─── بکاپ ───
    elif cmd in ("/بکاپ", "/backup"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        return create_backup(user_id)

    elif cmd in ("/لیست_بکاپ", "/backups"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        return list_backups()

    elif cmd in ("/بازگردانی", "/rollback"):
        if not is_owner(user_id): return "❌ فقط اونر."
        if len(parts) < 2: return "⚠️ /بازگردانی [شناسه]"
        return do_rollback(int(parts[1]), user_id)

    # ─── مدیریت ادمین ───
    elif cmd in ("/افزودن_ادمین", "/add_admin"):
        if not is_owner(user_id): return "❌ فقط اونر."
        if len(parts) < 3: return "⚠️ /افزودن_ادمین [user_id] [نام]"
        return add_admin(parts[1], " ".join(parts[2:]), user_id)

    elif cmd in ("/حذف_ادمین", "/del_admin"):
        if not is_owner(user_id): return "❌ فقط اونر."
        if len(parts) < 2: return "⚠️ /حذف_ادمین [user_id]"
        return del_admin(parts[1], user_id)

    elif cmd in ("/ادمینها", "/admins"):
        if not is_owner(user_id): return "❌ فقط اونر."
        return list_admins()

    # ─── آمار و ابزارهای ادمین ───
    elif cmd in ("/آمار", "/stats"):
        return admin_stats(user_id)

    elif cmd in ("/آمار_ai", "/ai_stats"):
        return admin_ai_stats(user_id)

    elif cmd in ("/لیست_گروهکها", "/all_groups"):
        return admin_group_info_all(user_id)

    elif cmd in ("/بودجه_گروهک", "/set_group_budget"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 3: return "⚠️ /بودجه_گروهک [user_id] [مبلغ]"
        try: return admin_set_group_budget(parts[1], int(parts[2]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/نتیجه_عملیات", "/op_result"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 3: return "⚠️ /نتیجه_عملیات [user_id] [success|fail] [توضیح]"
        success = parts[2].lower() in ("success", "yes", "1", "موفق")
        note = " ".join(parts[3:]) if len(parts) > 3 else ""
        return admin_op_result(parts[1], success, note, user_id)

    elif cmd in ("/حذف_گروهک", "/del_group"):
        if not is_owner(user_id): return "❌ فقط اونر."
        if len(parts) < 2: return "⚠️ /حذف_گروهک [user_id]"
        return admin_delete_group(parts[1], user_id)

    elif cmd in ("/حذف_کشور", "/del_country"):
        if not is_owner(user_id): return "❌ فقط مالک."
        if len(parts) < 2: return "⚠️ /حذف_کشور [ID]\nمثال: /حذف_کشور 5"
        try: return del_country(int(parts[1]), user_id)
        except: return "❌ فرمت اشتباه. مثال: /حذف_کشور 5"

    elif cmd in ("/لیست_اتحادها", "/all_alliances"):
        return admin_alliance_info_all(user_id)

    elif cmd in ("/انحلال_اتحاد", "/disband_alliance"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /انحلال_اتحاد [ID]"
        try: return admin_disband_alliance(int(parts[1]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/افزودن_نفت", "/add_oil"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 3: return "⚠️ /افزودن_نفت [country_id] [مقدار]"
        try: return admin_add_oil(int(parts[1]), int(parts[2]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/تنظیم_بودجه", "/set_money"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 3: return "⚠️ /تنظیم_بودجه [country_id] [مبلغ]"
        try: return admin_set_money(int(parts[1]), int(parts[2]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/نتیجه_جنگ", "/war_result"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 4: return "⚠️ /نتیجه_جنگ [attacker_id] [defender_id] [attacker|defender]"
        try: return admin_war_result(int(parts[1]), int(parts[2]), parts[3], user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/ریست_روزانه", "/reset_daily"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        cid = int(parts[1]) if len(parts) > 1 else 0
        return admin_reset_daily(cid, user_id)

    elif cmd in ("/اعلام_همگانی", "/broadcast"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /اعلام_همگانی [پیام]"
        msg = "📢 *اطلاعیه ادمین:*\n\n" + " ".join(parts[1:])
        result, uids = admin_broadcast(msg, user_id)
        # ذخیره پیام در context برای ارسال
        return f"{result}\n\nپیام:\n{msg}"

    # ─── دستیار هوشمند ─────────────────────────────────
    elif cmd in ("/ai", "/هوش", "/دستیار", "/help_ai"):
        from config import GEMINI_PROXY, GEMINI_API_KEYS
        keys = [k for k in GEMINI_API_KEYS if k and not k.startswith("YOUR_")]
        if not keys or not any(k.strip() for k in keys):
            return ("🤖 *دستیار هوشمند*\n\n"
                    "⏳ این قابلیت به زودی فعال می‌شود!\n\n"
                    "در نسخه‌های بعدی:\n"
                    "• پاسخ به سوالات بازی\n"
                    "• راهنمایی خرید تجهیزات\n"
                    "• تحلیل وضعیت کشور\n\n"
                    "📌 تا آن زمان از /راهنما و /قوانین استفاده کن.")
        question = " ".join(parts[1:]) if len(parts) > 1 else ""
        return "__AI__" + question

    # ─── رزرو و مدیریت بازی ───────────────────────────

    elif cmd in ("/رزرو", "/reserve"):
        if len(parts) < 2:
            gs = get_game_status()
            if gs["status"] != "waiting":
                return "❌ بازی شروع شده، رزرو امکان‌پذیر نیست."
            return ("📋 *برای رزرو کشور یا گروهک:*\n\n"
                    "/رزرو [نام کشور یا گروهک]\n\n"
                    "مثال:\n`/رزرو ایران`\n`/رزرو واگنر`\n\n"
                    "/رزروها — لیست رزروهای فعلی\n"
                    "/کشور — لیست کشورها\n"
                    "/گروهکها — لیست گروهک‌ها")
        target = " ".join(parts[1:])
        return "__RESERVE__" + target

    elif cmd in ("/رزروها", "/reservations"):
        return cmd_reservations_list()

    elif cmd in ("/وضعیت_بازی", "/game_status"):
        gs = get_game_status()
        status_map = {"waiting": "⏳ در انتظار شروع", "running": "🟢 در حال بازی", "ended": "🔴 پایان یافته"}
        t = f"🎮 *وضعیت بازی:* {status_map.get(gs['status'], gs['status'])}\n"
        if gs.get("start_time"):
            t += f"▶️ شروع: `{gs['start_time'][:16]}`\n"
        if gs.get("end_time"):
            t += f"🏁 پایان: `{gs['end_time'][:16]}`\n"
        return t

    # ─── دستورات ادمین — بازی ─────────────────────────

    elif cmd in ("/شروع_بازی", "/start_game"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        return "__START_GAME__"

    elif cmd in ("/پایان_بازی", "/end_game"):
        if not is_owner(user_id): return "❌ فقط اونر."
        return "__END_GAME__"

    elif cmd in ("/ری_استارت", "/restart_game"):
        if not is_owner(user_id): return "❌ فقط اونر."
        return "__RESTART_CONFIRM__"

    elif cmd in ("/تایید_ری_استارت", "/confirm_restart"):
        if not is_owner(user_id): return "❌ فقط اونر."
        return "__RESTART__"

    elif cmd in ("/تایمر_بازی", "/game_timer"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /تایمر_بازی [ساعت]\nمثال: /تایمر_بازی 48"
        try: return admin_set_game_timer(int(parts[1]), user_id)
        except: return "❌ فرمت اشتباه."

    elif cmd in ("/لغو_رزرو", "/cancel_reserve"):
        if not is_admin(user_id): return "❌ دسترسی ندارید."
        if len(parts) < 2: return "⚠️ /لغو_رزرو [نام کشور یا گروهک]"
        return admin_cancel_reserve(" ".join(parts[1:]), user_id)

    return None


# ════════════════════════════════════════════════
#  اجرای ربات
# ════════════════════════════════════════════════

print("🚀 ربات جنگ جهانی v4 شروع به کار کرد...")
app = Client(SESSION_NAME, phone_number=PHONE_NUMBER)


async def send_to_channel(msg):
    """ارسال پیام به کانال اطلاع‌رسانی"""
    try:
        if CHANNEL_ID and CHANNEL_ID != "YOUR_CHANNEL_GUID":
            await app.send_message(CHANNEL_ID, msg)
            print(f"📢 پیام به کانال ارسال شد")
    except Exception as e:
        print(f"⚠️ خطا در ارسال به کانال: {e}")

@app.on_message_updates()
async def on_message(update):
    try:
        text = getattr(update, "text", None) or getattr(update, "caption", None) or ""
        text = text.strip() if text else ""
        if not text:
            return

        chat_id = (
            getattr(update, "object_guid", None)
            or getattr(update, "chat_id", None)
        )
        user_id = getattr(update, "author_object_guid", None)
        if not user_id:
            user_id = chat_id

        username = (
            getattr(update, "author_title", None)
            or getattr(update, "title", None)
            or str(user_id)
        )

        print(f"📨 [{chat_id}] {user_id}: {text[:60]}")
        if not chat_id:
            return

        response = handle(str(chat_id), str(user_id), str(username), text)

        # اگه دستور نبود و سوال بود، به AI بفرست
        if not response and not text.startswith("/") and len(text) > 5:
            if "؟" in text or "?" in text or text.endswith("چیه") or text.endswith("چیست") or text.endswith("چطور") or text.endswith("چگونه"):
                await update.reply("⏳ در حال پردازش...")
                import asyncio
                answer = await asyncio.get_event_loop().run_in_executor(
                    None, cmd_ai_help, str(user_id), text
                )
                await update.reply(answer)
                return

        if not response:
            return

        # ─── پردازش دستورات خاص ───────────────────────

        # رزرو
        if response.startswith("__RESERVE__"):
            target = response[len("__RESERVE__"):]
            channel_msg, user_msg = cmd_reserve(str(user_id), str(username), target)
            await update.reply(user_msg)
            if channel_msg:
                await send_to_channel(channel_msg)
            return

        # شروع بازی
        if response == "__START_GAME__":
            await update.reply("⏳ در حال شروع بازی...")
            summary, channel_msgs = admin_start_game(str(user_id))
            await update.reply(summary)
            # ارسال تک‌تک به کانال با تاخیر
            import asyncio
            start_announce = "🚀 *بازی جنگ جهانی آغاز شد!*\n━━━━━━━━━━━━━━\n\n🌍 بازیکنان وارد می‌شوند..."
            await send_to_channel(start_announce)
            await asyncio.sleep(2)
            for msg in channel_msgs:
                await send_to_channel(msg)
                await asyncio.sleep(1.5)
            await send_to_channel("━━━━━━━━━━━━━━\n⚔️ *بازی شروع شد! موفق باشید!*")
            return

        # پایان بازی
        if response == "__END_GAME__":
            result, channel_msg = admin_end_game(str(user_id))
            await update.reply(result)
            if channel_msg:
                await send_to_channel(channel_msg)
            return

        # تأیید ری‌استارت
        if response == "__RESTART_CONFIRM__":
            await update.reply(
                "⚠️ *آیا مطمئنی؟*\n\n"
                "این عمل *همه داده‌ها* رو ریست می‌کنه:\n"
                "• همه تجهیزات کشورها\n"
                "• همه گروهک‌ها\n"
                "• همه اتحادها\n"
                "• همه رزروها\n\n"
                "برای تأیید: /تایید_ری_استارت"
            )
            return

        # ری‌استارت
        if response == "__RESTART__":
            result = admin_restart_game(str(user_id))
            await update.reply(result)
            await send_to_channel(
                "🔄 *بازی ری‌استارت شد!*\n\n"
                "📋 رزروها باز شدند.\n"
                "⏳ برای رزرو کشور یا گروهک پیام دهید:\n"
                "/رزرو [نام کشور یا گروهک]"
            )
            return

        # AI
        if response.startswith("__AI__"):
            question = response[len("__AI__"):]
            await update.reply("⏳ در حال پردازش...")
            import asyncio
            answer = await asyncio.get_event_loop().run_in_executor(
                None, cmd_ai_help, str(user_id), question
            )
            await update.reply(answer)
            return

        # پیام عادی
        await update.reply(response)
        print("✅ جواب ارسال شد")

    except Exception as e:
        import traceback
        print(f"⚠️ خطا: {e}")
        traceback.print_exc()


print("👂 منتظر پیام...")
app.run()
