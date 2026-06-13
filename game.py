import sqlite3
import json
from datetime import datetime, date
from database import get_conn

# ═══════════════════════════════════════════════════════
#  ادمین
# ═══════════════════════════════════════════════════════

def is_admin(uid):
    conn = get_conn()
    r = conn.execute("SELECT id FROM admins WHERE user_id=?", (str(uid),)).fetchone()
    conn.close()
    return r is not None

def is_owner(uid):
    conn = get_conn()
    r = conn.execute("SELECT id FROM admins WHERE user_id=? AND is_owner=1", (str(uid),)).fetchone()
    conn.close()
    return r is not None

def add_admin(uid, name, by):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO admins (user_id,name) VALUES (?,?)", (str(uid), name))
        conn.commit()
        return f"✅ ادمین «{name}» اضافه شد."
    except:
        return "❌ این کاربر قبلاً ادمینه."
    finally:
        conn.close()

def del_admin(uid, by):
    conn = get_conn()
    r = conn.execute("SELECT * FROM admins WHERE user_id=?", (str(uid),)).fetchone()
    if not r:
        conn.close(); return "❌ ادمین پیدا نشد."
    if r["is_owner"]:
        conn.close(); return "❌ اونر رو نمیشه حذف کرد."
    conn.execute("DELETE FROM admins WHERE user_id=?", (str(uid),))
    conn.commit(); conn.close()
    return "✅ ادمین حذف شد."

def list_admins():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM admins ORDER BY is_owner DESC").fetchall()
    conn.close()
    if not rows: return "❌ ادمینی نیست."
    t = "👮 *ادمین‌ها:*\n\n"
    for a in rows:
        t += f"{'👑' if a['is_owner'] else '🛡'} {a['name']} | `{a['user_id']}`\n"
    return t

# ═══════════════════════════════════════════════════════
#  کشورها
# ═══════════════════════════════════════════════════════

def add_country(name, flag, continent, by):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO countries (name,flag,continent) VALUES (?,?,?)", (name, flag, continent))
        conn.commit()
        return f"✅ کشور {flag} {name} ({continent}) اضافه شد."
    except:
        return "❌ این کشور قبلاً وجود داره."
    finally:
        conn.close()

def del_country(cid, by):
    if not is_owner(by):
        return "❌ فقط مالک می‌تواند کشور حذف کند."
    conn = get_conn()
    r = conn.execute("SELECT * FROM countries WHERE id=?", (cid,)).fetchone()
    if not r:
        conn.close(); return "❌ کشور پیدا نشد."
    # حذف همه داده‌های مرتبط
    conn.execute("DELETE FROM country_equipment WHERE country_id=?", (cid,))
    conn.execute("DELETE FROM country_troops WHERE country_id=?", (cid,))
    conn.execute("DELETE FROM buildings WHERE country_id=?", (cid,))
    conn.execute("DELETE FROM country_vip WHERE country_id=?", (cid,))
    conn.execute("DELETE FROM reservations WHERE target_name=?", (r["name"],))
    conn.execute("UPDATE players SET country_id=NULL WHERE country_id=?", (cid,))
    conn.execute("DELETE FROM countries WHERE id=?", (cid,))
    conn.commit(); conn.close()
    return f"✅ کشور {r['flag']} *{r['name']}* و تمام داده‌هایش حذف شد."

def edit_country(cid, field, value, by):
    ok = {"name","flag","continent","money","oil","satisfaction","max_players","daily_oil"}
    if field not in ok:
        return f"❌ فیلد نامعتبر.\nفیلدهای مجاز: {', '.join(ok)}"
    conn = get_conn()
    conn.execute(f"UPDATE countries SET {field}=? WHERE id=?", (value, cid))
    conn.commit(); conn.close()
    return f"✅ {field} = {value}"

def get_countries_list():
    """منوی اصلی - انتخاب قاره"""
    return """🌍 *انتخاب قاره*
━━━━━━━━━━━━━━━

یک قاره انتخاب کنید:

🌎 /قاره_امریکا - آمریکا
🌏 /قاره_آسیا - آسیا
🌍 /قاره_اروپا - اروپا
🌍 /قاره_آفریقا - آفریقا"""

def get_countries_by_continent(continent):
    """نمایش کشورهای یک قاره"""
    cont_map = {
        "امریکا": "آمریکا", "آمریکا": "آمریکا",
        "آسیا": "آسیا", "اروپا": "اروپا", "آفریقا": "آفریقا"
    }
    cont = cont_map.get(continent, continent)
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM countries WHERE is_active=1 AND continent=? ORDER BY name",
        (cont,)
    ).fetchall()
    conn.close()
    if not rows:
        return f"❌ کشوری در قاره {cont} تعریف نشده."
    cont_emoji = {"آمریکا":"🌎","آسیا":"🌏","اروپا":"🌍","آفریقا":"🌍"}.get(cont,"🌍")
    t = f"{cont_emoji} *کشورهای {cont}:*\n"
    t += "━━━━━━━━━━━━━━━\n\n"
    for c in rows:
        full = c["current_players"] >= c["max_players"]
        status = "🔴 پر" if full else "🟢 باز"
        vip = "👑" if c["is_vip"] else ""
        oil = f"🛢{c['daily_oil']:,}" if c["daily_oil"] > 0 else ""
        t += f"{status} {c['flag']}{vip} *{c['name']}* [{c['id']}]"
        if oil: t += f" {oil}"
        t += f" ({c['current_players']}/{c['max_players']})\n"
    t += f"\n📌 برای انتخاب: /country [ID]"
    return t

def select_country(uid, cid, username):
    conn = get_conn()
    p = conn.execute("SELECT * FROM players WHERE user_id=?", (str(uid),)).fetchone()
    if p and p["country_id"]:
        old = conn.execute("SELECT name,flag FROM countries WHERE id=?", (p["country_id"],)).fetchone()
        old_name = f"{old['flag']} {old['name']}" if old else "?"
        conn.close()
        return f"❌ شما قبلاً {old_name} رو انتخاب کردید.\nبرای تغییر با ادمین تماس بگیرید."

    c = conn.execute("SELECT * FROM countries WHERE id=? AND is_active=1", (cid,)).fetchone()
    if not c:
        conn.close(); return "❌ کشور پیدا نشد یا غیرفعاله."
    if c["current_players"] >= c["max_players"]:
        conn.close(); return f"❌ کشور {c['flag']} {c['name']} پر شده."

    if not p:
        conn.execute("INSERT INTO players (user_id,username,country_id) VALUES (?,?,?)", (str(uid), username, cid))
    else:
        conn.execute("UPDATE players SET country_id=?,username=? WHERE user_id=?", (cid, username, str(uid)))
    conn.execute("UPDATE countries SET current_players=current_players+1 WHERE id=?", (cid,))
    conn.commit()

    is_full = (c["current_players"] + 1) >= c["max_players"]
    conn.close()
    return {
        "msg": f"✅ کشور {c['flag']} *{c['name']}* انتخاب شد!\n\n💵 بودجه اولیه: ۵ میلیارد دلار\n🛢 نفت: {c['oil']} بشکه\n😊 رضایت: {c['satisfaction']}%",
        "is_full": is_full,
        "country_name": c["name"]
    }

def _get_player_country(uid):
    conn = get_conn()
    row = conn.execute(
        "SELECT c.* FROM players p JOIN countries c ON p.country_id=c.id WHERE p.user_id=?",
        (str(uid),)
    ).fetchone()
    conn.close()
    return row

# ═══════════════════════════════════════════════════════
#  پروفایل
# ═══════════════════════════════════════════════════════

def cmd_profile(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ هنوز کشوری انتخاب نکردید.\n/country - لیست کشورها"

    conn = get_conn()
    # نیروها
    troops_total = conn.execute(
        "SELECT COALESCE(SUM(ct.amount),0) as t FROM country_troops ct WHERE ct.country_id=?",
        (c["id"],)
    ).fetchone()["t"]

    # تجهیزات کلیدی
    equip = conn.execute(
        "SELECT SUM(ce.amount) as total FROM country_equipment ce WHERE ce.country_id=?",
        (c["id"],)
    ).fetchone()["total"] or 0

    # انبار تسلیحات
    has_storage = conn.execute(
        "SELECT ce.amount FROM country_equipment ce "
        "JOIN equipment_types et ON ce.equipment_type_id=et.id "
        "WHERE ce.country_id=? AND et.name='انبار تسلیحات'",
        (c["id"],)
    ).fetchone()
    storage_ok = has_storage and has_storage["amount"] > 0
    conn.close()

    oil_status = "🟢" if c["oil"] > 0 else "🔴"
    sat_emoji = "😊" if c["satisfaction"] >= 60 else ("😐" if c["satisfaction"] >= 40 else "😠")

    t = f"""🌍 *پروفایل کشور*

{c['flag']} *{c['name']}*
🗺 قاره: {c['continent']}
{'👑 VIP' if c['is_vip'] else ''}{'🚫 تحریم‌شده' if c['is_sanctioned'] else ''}

━━━━━━━━━━━━━━

💵 بودجه: `{c['money']:,}` دلار
{oil_status} نفت: `{c['oil']:,}` بشکه
{sat_emoji} رضایت مردمی: `{c['satisfaction']}%`

━━━━━━━━━━━━━━

🪖 نیروهای انسانی: `{troops_total:,}`
⚔️ کل تجهیزات: `{equip:,}`
📦 انبار تسلیحات: {'✅' if storage_ok else '❌ (بدون آن حمله ممکن نیست)'}

━━━━━━━━━━━━━━

/economy - اقتصاد
/army - تجهیزات نظامی
/buildings - ساختمان‌ها
/shop - فروشگاه تجهیزات"""
    return t

def cmd_full_profile(uid):
    """پروفایل کامل کشور"""
    c = _get_player_country(uid)
    if not c:
        return "❌ هنوز کشوری انتخاب نکردید.\n/کشور - لیست کشورها"

    conn = get_conn()

    # تجهیزات نظامی
    equips = conn.execute(
        "SELECT et.name,et.emoji,et.category,ce.amount FROM country_equipment ce "
        "JOIN equipment_types et ON ce.equipment_type_id=et.id "
        "WHERE ce.country_id=? AND ce.amount>0 ORDER BY et.category,et.name",
        (c["id"],)
    ).fetchall()

    # نیروها
    troops = conn.execute(
        "SELECT tt.name,tt.emoji,ct.amount FROM country_troops ct "
        "JOIN troop_types tt ON ct.troop_type_id=tt.id "
        "WHERE ct.country_id=? AND ct.amount>0",
        (c["id"],)
    ).fetchall()

    # ساختمان‌ها
    buildings = conn.execute(
        "SELECT bt.name,bt.emoji,bt.effect_type,bt.effect_value,b.amount FROM buildings b "
        "JOIN building_types bt ON b.building_type_id=bt.id "
        "WHERE b.country_id=? AND b.amount>0",
        (c["id"],)
    ).fetchall()

    # نفتکش
    try:
        tankers = conn.execute(
            "SELECT tt.name,tt.emoji,tt.capacity,ct.amount FROM country_tankers ct "
            "JOIN tanker_types tt ON ct.tanker_type_id=tt.id "
            "WHERE ct.country_id=? AND ct.amount>0", (c["id"],)
        ).fetchall()
    except: tankers = []

    # VIP
    vip_info = conn.execute(
        "SELECT vip_type,expire_date,is_active FROM country_vip WHERE country_id=?",
        (c["id"],)
    ).fetchone()

    # ماهواره
    satellite = conn.execute(
        "SELECT level,is_active FROM satellites WHERE country_id=?", (c["id"],)
    ).fetchone()

    # اختراعات
    inventions = conn.execute(
        "SELECT invention_type,name,description,daily_production FROM inventions "
        "WHERE country_id=? AND is_active=1", (c["id"],)
    ).fetchall()

    # اتحاد
    try:
        alliance = conn.execute(
            "SELECT a.name FROM alliances a JOIN alliance_members am ON a.id=am.alliance_id "
            "WHERE am.country_id=?", (c["id"],)
        ).fetchone()
        # اعضای اتحاد
        if alliance:
            members = conn.execute(
                "SELECT c2.name,c2.flag FROM alliance_members am "
                "JOIN countries c2 ON am.country_id=c2.id "
                "JOIN alliances a ON a.id=am.alliance_id "
                "WHERE a.name=? AND am.country_id!=?",
                (alliance["name"], c["id"])
            ).fetchall()
        else:
            members = []
    except:
        alliance = None
        members = []

    # بازیکنان کشور
    players = conn.execute(
        "SELECT username FROM players WHERE country_id=?", (c["id"],)
    ).fetchall()

    # سفارشات VIP فعال
    prem = conn.execute(
        "SELECT item_name,order_type FROM premium_orders "
        "WHERE user_id=? AND status='confirmed' ORDER BY confirmed_at DESC LIMIT 5",
        (str(uid),)
    ).fetchall()

    conn.close()

    # محاسبات
    daily_income = sum(b["effect_value"]*b["amount"] for b in buildings if b["effect_type"]=="money")
    inv_income = sum(i["daily_production"] for i in inventions)
    total_daily = daily_income + inv_income
    total_troops = sum(t["amount"] for t in troops)
    total_tanker_cap = sum(t["capacity"]*t["amount"] for t in tankers)

    # دسته‌بندی تجهیزات
    grouped = {}
    for e in equips:
        grouped.setdefault(e["category"], []).append(
            f"  {e['emoji']} {e['name']}: `{e['amount']:,}`"
        )

    def sec(em, title, lines_list):
        t = f"\n{em} *{title}:*\n"
        t += ("\n".join(lines_list) + "\n") if lines_list else "  〰〰〰〰〰〰〰〰\n"
        return t

    # ── وضعیت VIP ─────────────────────────────────
    vip_lines = []
    if c["is_vip"]:
        vip_lines.append("  👑 کشور VIP")
    if vip_info and vip_info["is_active"]:
        vtype = vip_info["vip_type"] or "VIP"
        exp = vip_info["expire_date"] or "نامحدود"
        vip_lines.append(f"  🎖 نوع: {vtype}")
        vip_lines.append(f"  📅 انقضا: {exp}")
    for p in prem:
        vip_lines.append(f"  ✅ {p['item_name']} [{p['order_type']}]")

    sat_em = "😊" if c["satisfaction"] >= 60 else ("😐" if c["satisfaction"] >= 40 else "😠")
    sanc_str = " 🚫تحریم" if c["is_sanctioned"] else ""
    vip_str = " 👑VIP" if c["is_vip"] else ""

    # ── خروجی ─────────────────────────────────────
    t  = f"🏛『 {c['flag']} *{c['name']}* 』{vip_str}{sanc_str}\n"
    t += f"🗺 قاره: *{c['continent']}*"
    if players:
        names = " | ".join(p["username"] or "?" for p in players)
        t += f" | 👤 {names}"
    t += "\n"
    t += "➖➖➖➖➖➖➖➖➖➖\n\n"

    # بودجه و منابع
    t += f"💸 *بودجه فعلی:*\n  `{c['money']:,}` دلار\n"
    t += f"🛢 *ذخایر نفت:*\n  `{c['oil']:,}` بشکه\n"
    t += f"⛽ *تولید روزانه نفت:*\n  `{c['daily_oil']:,}` بشکه\n"
    t += f"💰 *درآمد روزانه:*\n  `{total_daily:,}` دلار\n"
    if inv_income:
        t += f"  (شامل `{inv_income:,}` از اختراعات)\n"
    t += "➖➖➖➖➖➖➖➖➖➖\n"

    # VIP
    t += sec("💎", "وضعیت VIP و خریدهای ویژه", vip_lines)

    # ماهواره
    sat_lines = []
    if satellite and satellite["is_active"]:
        sat_lines = [f"  🛰 ماهواره جاسوسی — سطح {satellite['level']}",
                     f"  📡 قابلیت‌های سطح {satellite['level']} فعال"]
    t += sec("🛰", "ماهواره‌ها", sat_lines)

    # اختراعات
    inv_lines = []
    for inv in inventions:
        line = f"  🔬 {inv['name']} [{inv['invention_type']}]"
        if inv["daily_production"]: line += f" → `{inv['daily_production']:,}$/روز`"
        if inv["description"]: line += f"\n     📝 {inv['description']}"
        inv_lines.append(line)
    t += sec("🧪", "اختراعات", inv_lines)

    # تجهیزات نظامی
    cat_map = [
        ("missile",  "🚀", "تجهیزات موشکی"),
        ("fighter",  "🛩", "تجهیزات جنگنده‌ای"),
        ("bomber",   "✈️", "تجهیزات هوایی"),
        ("navy",     "🚢", "تجهیزات ناوگان"),
        ("bomb",     "💣", "تجهیزات تخریب‌گر"),
        ("defense",  "🛡", "تجهیزات تدافعی"),
        ("ground",   "🚛", "تجهیزات زمینی"),
        ("launcher", "🎯", "سامانه‌های پرتاب"),
        ("transport","🚙", "تجهیزات ترابری"),
        ("base",     "🏰", "اماکن نظامی"),
    ]
    for cat, em, title in cat_map:
        t += sec(em, title, grouped.get(cat, []))

    # نیروها
    troop_lines = [f"  {r['emoji']} {r['name']}: `{r['amount']:,}`" for r in troops]
    if total_troops:
        troop_lines.append(f"  ─────\n  🪖 جمع کل: `{total_troops:,}` نفر")
    t += sec("🪖", "نیروهای انسانی", troop_lines)

    # درآمدزاها
    eco = [f"  {b['emoji']} {b['name']} ×{b['amount']} → `{b['effect_value']*b['amount']:,}$/دور`"
           for b in buildings if b["effect_type"]=="money"]
    t += sec("📈", "تجهیزات درآمدزا", eco)

    # رفاهی
    welfare = [f"  {b['emoji']} {b['name']} ×{b['amount']} → +`{b['effect_value']*b['amount']}%` رضایت"
               for b in buildings if b["effect_type"]=="satisfaction"]
    t += sec("🏙", "اماکن عمومی", welfare)

    # نفتکش
    tank_lines = [f"  {r['emoji']} {r['name']} ×{r['amount']} | ظرفیت: `{r['capacity']*r['amount']:,}` بشکه"
                  for r in tankers]
    if total_tanker_cap:
        tank_lines.append(f"  ─────\n  ⛵ جمع ظرفیت: `{total_tanker_cap:,}` بشکه")
    t += sec("⛵", "نفتکش‌ها", tank_lines)

    # اتحاد
    if alliance:
        al_lines = [f"  🤝 {alliance['name']}"]
        for m in members:
            al_lines.append(f"  {m['flag']} {m['name']}")
        t += sec("🤝", "اتحاد", al_lines)
    else:
        t += sec("🤝", "متحدان", [])

    # وضعیت نهایی
    t += "\n➖➖➖➖➖➖➖➖➖➖\n"
    t += f"🌇 *جمعیت:*\n  100,000,000 نفر\n"
    t += f"\n{sat_em} *رضایت مردمی:*\n  `{c['satisfaction']}٪`\n"
    if c["is_sanctioned"]:
        t += f"\n🚫 *تحریم:*\n  فعال | {c['sanction_days']} روز باقیمانده\n"
    t += f"\n⚡ *درصد تخریب:*\n  `{c.get('destruction', 0)}٪`\n"
    t += "➖➖➖➖➖➖➖➖➖➖"
    return t

def _table_exists(conn, table):
    r = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return r is not None

# ═══════════════════════════════════════════════════════
#  اقتصاد
# ═══════════════════════════════════════════════════════

def cmd_economy(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."

    conn = get_conn()
    # درآمد از ساختمان‌ها
    income_rows = conn.execute(
        "SELECT bt.name, bt.emoji, bt.effect_value, b.amount "
        "FROM buildings b JOIN building_types bt ON b.building_type_id=bt.id "
        "WHERE b.country_id=? AND bt.effect_type='money' AND b.amount>0",
        (c["id"],)
    ).fetchall()
    conn.close()

    total_income = sum(r["effect_value"] * r["amount"] for r in income_rows)

    t = f"💰 *اقتصاد {c['flag']} {c['name']}*\n\n"
    t += f"💵 بودجه فعلی: `{c['money']:,}` دلار\n"
    t += f"🛢 نفت: `{c['oil']:,}` بشکه\n"
    t += f"⛽ تولید روزانه نفت: `{c['daily_oil']:,}` بشکه\n\n"

    if income_rows:
        t += "📈 *درآمدزاها:*\n"
        for r in income_rows:
            t += f"{r['emoji']} {r['name']} x{r['amount']} → `{r['effect_value'] * r['amount']:,}` دلار/دور\n"
        t += f"\n💹 *کل درآمد هر دور: `{total_income:,}` دلار*\n"
    else:
        t += "📉 هیچ ساختمان درآمدزایی ندارید.\n"

    t += "\n/shop - خرید تجهیزات و پروژه‌ها"
    return t

# ═══════════════════════════════════════════════════════
#  ارتش / تجهیزات
# ═══════════════════════════════════════════════════════

def cmd_army(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."

    conn = get_conn()
    rows = conn.execute(
        "SELECT et.name, et.emoji, et.category, ce.amount "
        "FROM country_equipment ce "
        "JOIN equipment_types et ON ce.equipment_type_id=et.id "
        "WHERE ce.country_id=? AND ce.amount>0 "
        "ORDER BY et.category, et.name",
        (c["id"],)
    ).fetchall()

    troops = conn.execute(
        "SELECT tt.name, tt.emoji, ct.amount "
        "FROM country_troops ct "
        "JOIN troop_types tt ON ct.troop_type_id=tt.id "
        "WHERE ct.country_id=? AND ct.amount>0",
        (c["id"],)
    ).fetchall()
    conn.close()

    if not rows and not troops:
        return f"⚔️ *ارتش {c['flag']} {c['name']}*\n\n❌ هیچ تجهیزاتی ندارید.\n/shop - خرید تجهیزات"

    cat_names = {
        "navy": "🚢 نیروی دریایی",
        "defense": "🛡 پدافند",
        "missile": "🚀 موشک‌ها",
        "bomber": "✈️ بمب‌افکن‌ها",
        "launcher": "🚛 سامانه‌های پرتاب",
        "fighter": "✈️ جنگنده‌ها",
        "transport": "🚢 ترابری",
        "ground": "🚜 زمینی",
        "bomb": "💣 بمب‌های سنگین",
        "base": "🏕 پایگاه‌ها",
    }

    t = f"⚔️ *ارتش {c['flag']} {c['name']}*\n\n"

    if troops:
        t += "🪖 *نیروی انسانی:*\n"
        for r in troops:
            t += f"{r['emoji']} {r['name']}: `{r['amount']:,}`\n"
        t += "\n"

    last_cat = None
    for r in rows:
        if r["category"] != last_cat:
            t += f"\n{cat_names.get(r['category'], r['category'])}:\n"
            last_cat = r["category"]
        t += f"{r['emoji']} {r['name']}: `{r['amount']:,}`\n"

    return t

# ═══════════════════════════════════════════════════════
#  ساختمان‌ها
# ═══════════════════════════════════════════════════════

def cmd_buildings(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."

    conn = get_conn()
    rows = conn.execute(
        "SELECT bt.name, bt.emoji, bt.effect_type, bt.effect_value, b.amount "
        "FROM buildings b "
        "JOIN building_types bt ON b.building_type_id=bt.id "
        "WHERE b.country_id=? AND b.amount>0",
        (c["id"],)
    ).fetchall()
    conn.close()

    if not rows:
        return f"🏛 *ساختمان‌های {c['flag']} {c['name']}*\n\n❌ ساختمانی ندارید.\n/shop - خرید پروژه"

    t = f"🏛 *ساختمان‌های {c['flag']} {c['name']}*\n\n"
    for r in rows:
        if r["effect_type"] == "money":
            effect = f"💵 درآمد: `{r['effect_value'] * r['amount']:,}` دلار/دور"
        elif r["effect_type"] == "satisfaction":
            effect = f"😊 رضایت: +`{r['effect_value'] * r['amount']}%`"
        else:
            effect = f"⚡ {r['effect_type']}: {r['effect_value'] * r['amount']}"
        t += f"{r['emoji']} {r['name']} x{r['amount']}\n   {effect}\n\n"
    return t

# ═══════════════════════════════════════════════════════
#  فروشگاه
# ═══════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════
#  فروشگاه - منوی اصلی
# ═══════════════════════════════════════════════════════

CAT_NAMES = {
    "navy":     "🚢 دریایی",
    "defense":  "💥 پدافند",
    "missile":  "🚀 موشک‌ها",
    "bomber":   "✈️ بمب‌افکن‌ها",
    "launcher": "🚛 سامانه پرتاب",
    "fighter":  "🛩 جنگنده‌ها",
    "transport":"🚁 ترابری",
    "ground":   "🔫 زمینی",
    "bomb":     "💣 بمب‌ها",
    "base":     "🏕 پایگاه‌ها",
}

def cmd_shop(uid, category=None, continent=None):
    """منوی اصلی فروشگاه - نمایش دسته‌بندی‌ها"""
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."

    cont = continent or c["continent"]
    cont_emoji = {"آمریکا":"🌎","آسیا":"🌏","اروپا":"🌍","آفریقا":"🌍"}.get(cont,"🌍")
    t = f"🛒 *فروشگاه نظامی*\n"
    t += f"{cont_emoji} قاره: *{cont}* | {c['flag']} {c['name']}\n"
    t += "━━━━━━━━━━━━━━━\n\n"
    t += "⚔️ *تجهیزات نظامی:*\n"
    t += f"🚀 /فروشگاه_موشک\n"
    t += f"🛩 /فروشگاه_جنگنده\n"
    t += f"✈️ /فروشگاه_بمب_افکن\n"
    t += f"🚢 /فروشگاه_دریایی\n"
    t += f"💥 /فروشگاه_پدافند\n"
    t += f"🔫 /فروشگاه_زمینی\n"
    t += f"🚛 /فروشگاه_پرتاب\n"
    t += f"💣 /فروشگاه_بمب\n"
    t += f"🏕 /فروشگاه_پایگاه\n"
    t += f"🚁 /فروشگاه_ترابری\n\n"
    t += "─────────────────\n"
    t += "🏗 *پروژه و نیرو:*\n"
    t += f"🏛 /فروشگاه_ساختمان\n"
    t += f"🪖 /فروشگاه_نیرو\n"
    t += f"🛢 /فروشگاه_نفتکش\n\n"
    t += f"📌 همه تجهیزات فقط برای قاره {cont} نمایش داده می‌شن"
    return t

def _shop_by_category(uid, category):
    """نمایش تجهیزات یک دسته خاص"""
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    cont = c["continent"]
    conn = get_conn()
    # اگه آیتم اختصاصی قاره هست، فقط اونا رو نشون بده، نه آیتم‌های 'همه'
    specific = conn.execute(
        "SELECT * FROM equipment_types WHERE category=? AND continent=? ORDER BY price",
        (category, cont)
    ).fetchall()
    universal = conn.execute(
        "SELECT * FROM equipment_types WHERE category=? AND continent='همه' ORDER BY price",
        (category,)
    ).fetchall()
    # اگه آیتم اختصاصی داریم، فقط اونا + آیتم‌های 'همه' که اسمشون تکراری نیست
    if specific:
        specific_names = {r["name"] for r in specific}
        extra = [r for r in universal if r["name"] not in specific_names]
        rows = specific + extra
    else:
        rows = universal
    conn.close()
    cat_label = CAT_NAMES.get(category, category)
    if not rows:
        return f"❌ تجهیزی در دسته {cat_label} برای {cont} وجود نداره."
    t = f"{cat_label} *| {cont}*\n"
    t += "━━━━━━━━━━━━━━━\n\n"
    for r in rows:
        owned = _get_owned_equip(c["id"], r["id"])
        price_str = f"{r['price']//1000000}M" if r['price'] >= 1000000 else f"{r['price']:,}"
        t += f"[{r['id']}] {r['emoji']} *{r['name']}*\n"
        t += f"   💰 {price_str}$ | حداکثر: {r['max_buy']}"
        if owned: t += f" | دارید: {owned}"
        if r["description"]: t += f"\n   📝 {r['description']}"
        t += f"\n   ➡️ /خرید_تجهیز {r['id']} [تعداد]\n\n"
    return t

def _get_owned_equip(country_id, eq_id):
    conn = get_conn()
    r = conn.execute(
        "SELECT amount FROM country_equipment WHERE country_id=? AND equipment_type_id=?",
        (country_id, eq_id)
    ).fetchone()
    conn.close()
    return r["amount"] if r and r["amount"] > 0 else 0

# دستورات فروشگاه بخش‌بخش
def cmd_shop_missile(uid):   return _shop_by_category(uid, "missile")
def cmd_shop_fighter(uid):   return _shop_by_category(uid, "fighter")
def cmd_shop_bomber(uid):    return _shop_by_category(uid, "bomber")
def cmd_shop_navy(uid):      return _shop_by_category(uid, "navy")
def cmd_shop_defense(uid):   return _shop_by_category(uid, "defense")
def cmd_shop_ground(uid):    return _shop_by_category(uid, "ground")
def cmd_shop_launcher(uid):  return _shop_by_category(uid, "launcher")
def cmd_shop_bomb(uid):      return _shop_by_category(uid, "bomb")
def cmd_shop_base(uid):      return _shop_by_category(uid, "base")
def cmd_shop_transport(uid): return _shop_by_category(uid, "transport")

def cmd_shop_buildings(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM building_types WHERE continent=? OR continent='همه' ORDER BY effect_type, price",
        (c["continent"],)
    ).fetchall()
    conn.close()
    if not rows:
        return f"❌ پروژه‌ای برای {c['continent']} وجود نداره."
    # درآمدزا
    t = f"🏛 *پروژه‌های اقتصادی - {c['continent']}*\n"
    t += "━━━━━━━━━━━━━━━\n\n"
    t += "💰 *درآمدزا:*\n"
    for r in rows:
        if r["effect_type"] != "money": continue
        price_str = f"{r['price']//1000000}M"
        t += f"[{r['id']}] {r['emoji']} *{r['name']}*\n"
        t += f"   💰 {price_str}$ | درآمد: {r['effect_value']//1000000}M$/دور\n"
        t += f"   ➡️ /خرید_ساختمان {r['id']} 1\n\n"
    t += "\n😊 *رفاهی:*\n"
    for r in rows:
        if r["effect_type"] != "satisfaction": continue
        price_str = f"{r['price']//1000000}M"
        t += f"[{r['id']}] {r['emoji']} *{r['name']}*\n"
        t += f"   💰 {price_str}$ | رضایت: +{r['effect_value']}%\n"
        t += f"   ➡️ /خرید_ساختمان {r['id']} 1\n\n"
    return t

def cmd_shop_troops(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM troop_types WHERE continent=? ORDER BY price",
        (c["continent"],)
    ).fetchall()
    conn.close()
    if not rows:
        return f"❌ نیروی انسانی برای {c['continent']} تعریف نشده."
    t = f"🪖 *نیروی انسانی - {c['continent']}*\n"
    t += "━━━━━━━━━━━━━━━\n\n"
    for r in rows:
        owned = 0
        conn2 = get_conn()
        ow = conn2.execute(
            "SELECT amount FROM country_troops WHERE country_id=? AND troop_type_id=?",
            (c["id"], r["id"])
        ).fetchone()
        conn2.close()
        if ow: owned = ow["amount"]
        t += f"[{r['id']}] {r['emoji']} *{r['name']}*\n"
        t += f"   💰 {r['price']:,}$ هر نفر"
        if owned: t += f" | دارید: {owned:,}"
        t += f"\n   ➡️ /خرید_نیرو {r['id']} [تعداد]\n\n"
    return t

def cmd_shop_tankers(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM tanker_types WHERE continent=? ORDER BY price",
        (c["continent"],)
    ).fetchall()
    conn.close()
    if not rows:
        return f"❌ نفتکشی برای {c['continent']} تعریف نشده."
    t = f"🛢 *نفتکش‌ها - {c['continent']}*\n"
    t += "━━━━━━━━━━━━━━━\n\n"
    for r in rows:
        t += f"[{r['id']}] {r['emoji']} *{r['name']}*\n"
        t += f"   💰 {r['price']//1000000}M$ | ظرفیت: {r['capacity']} بشکه\n"
        t += f"   ➡️ /خرید_نفتکش {r['id']} [تعداد]\n\n"
    return t

# ═══════════════════════════════════════════════════════
#  خرید تجهیزات
# ═══════════════════════════════════════════════════════

def buy_equipment(uid, eq_id, amount):
    if amount <= 0:
        return "❌ تعداد باید بیشتر از صفر باشه."
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."

    conn = get_conn()
    eq = conn.execute("SELECT * FROM equipment_types WHERE id=?", (eq_id,)).fetchone()
    if not eq:
        conn.close(); return "❌ تجهیزات پیدا نشد."

    # بررسی قاره
    if eq["continent"] != "همه" and eq["continent"] != c["continent"]:
        conn.close(); return f"❌ این تجهیزات فقط برای قاره {eq['continent']} هست."

    # بررسی حداکثر خرید
    current = conn.execute(
        "SELECT COALESCE(amount,0) as a FROM country_equipment WHERE country_id=? AND equipment_type_id=?",
        (c["id"], eq_id)
    ).fetchone()
    cur_amount = current["a"] if current else 0
    if cur_amount + amount > eq["max_buy"]:
        conn.close(); return f"❌ حداکثر مجاز: {eq['max_buy']} عدد (دارید: {cur_amount})"

    total_cost = eq["price"] * amount
    if c["money"] < total_cost:
        conn.close(); return f"❌ بودجه کافی نیست.\nنیاز: `{total_cost:,}$`\nدارید: `{c['money']:,}$`"

    # کسر بودجه
    conn.execute("UPDATE countries SET money=money-? WHERE id=?", (total_cost, c["id"]))
    # اضافه کردن تجهیزات
    conn.execute(
        "INSERT INTO country_equipment (country_id,equipment_type_id,amount) VALUES (?,?,?) "
        "ON CONFLICT(country_id,equipment_type_id) DO UPDATE SET amount=amount+?",
        (c["id"], eq_id, amount, amount)
    )
    conn.commit(); conn.close()

    return f"✅ خرید موفق!\n{eq['emoji']} *{eq['name']}* x{amount}\n💰 هزینه: `{total_cost:,}$`"

def buy_building(uid, b_id, amount):
    if amount <= 0:
        return "❌ تعداد باید بیشتر از صفر باشه."
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."

    conn = get_conn()
    bt = conn.execute("SELECT * FROM building_types WHERE id=?", (b_id,)).fetchone()
    if not bt:
        conn.close(); return "❌ ساختمان پیدا نشد."

    if bt["continent"] != "همه" and bt["continent"] != c["continent"]:
        conn.close(); return f"❌ این پروژه فقط برای قاره {bt['continent']} هست."

    current = conn.execute(
        "SELECT COALESCE(amount,0) as a FROM buildings WHERE country_id=? AND building_type_id=?",
        (c["id"], b_id)
    ).fetchone()
    cur_amount = current["a"] if current else 0
    if cur_amount + amount > bt["max_buy"]:
        conn.close(); return f"❌ حداکثر مجاز: {bt['max_buy']} عدد (دارید: {cur_amount})"

    total_cost = bt["price"] * amount
    if c["money"] < total_cost:
        conn.close(); return f"❌ بودجه کافی نیست.\nنیاز: `{total_cost:,}$`\nدارید: `{c['money']:,}$`"

    conn.execute("UPDATE countries SET money=money-? WHERE id=?", (total_cost, c["id"]))
    # اگر رضایت‌زاست، بلافاصله اعمال کن
    if bt["effect_type"] == "satisfaction":
        new_sat = min(100, c["satisfaction"] + bt["effect_value"] * amount)
        conn.execute("UPDATE countries SET satisfaction=? WHERE id=?", (new_sat, c["id"]))

    conn.execute(
        "INSERT INTO buildings (country_id,building_type_id,amount) VALUES (?,?,?) "
        "ON CONFLICT(country_id,building_type_id) DO UPDATE SET amount=amount+?",
        (c["id"], b_id, amount, amount)
    )
    conn.commit(); conn.close()

    if bt["effect_type"] == "satisfaction":
        return f"✅ خرید موفق!\n{bt['emoji']} *{bt['name']}* x{amount}\n😊 رضایت +{bt['effect_value'] * amount}%\n💰 هزینه: `{total_cost:,}$`"
    return f"✅ خرید موفق!\n{bt['emoji']} *{bt['name']}* x{amount}\n📈 درآمد +{bt['effect_value'] * amount:,}$/دور\n💰 هزینه: `{total_cost:,}$`"

def buy_troop(uid, t_id, amount):
    if amount <= 0:
        return "❌ تعداد باید بیشتر از صفر باشه."
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."

    conn = get_conn()
    tt = conn.execute("SELECT * FROM troop_types WHERE id=?", (t_id,)).fetchone()
    if not tt:
        conn.close(); return "❌ نوع نیرو پیدا نشد."

    if tt["continent"] != c["continent"]:
        conn.close(); return f"❌ این نیرو فقط برای قاره {tt['continent']} هست."

    total_cost = tt["price"] * amount
    if c["money"] < total_cost:
        conn.close(); return f"❌ بودجه کافی نیست.\nنیاز: `{total_cost:,}$`"

    conn.execute("UPDATE countries SET money=money-? WHERE id=?", (total_cost, c["id"]))
    conn.execute(
        "INSERT INTO country_troops (country_id,troop_type_id,amount) VALUES (?,?,?) "
        "ON CONFLICT(country_id,troop_type_id) DO UPDATE SET amount=amount+?",
        (c["id"], t_id, amount, amount)
    )
    conn.commit(); conn.close()
    return f"✅ خرید موفق!\n{tt['emoji']} *{tt['name']}* x{amount:,}\n💰 هزینه: `{total_cost:,}$`"

def buy_tanker(uid, t_id, amount):
    if amount <= 0:
        return "❌ تعداد باید بیشتر از صفر باشه."
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."

    conn = get_conn()
    tt = conn.execute("SELECT * FROM tanker_types WHERE id=?", (t_id,)).fetchone()
    if not tt:
        conn.close(); return "❌ نفتکش پیدا نشد."

    total_cost = tt["price"] * amount
    if c["money"] < total_cost:
        conn.close(); return f"❌ بودجه کافی نیست.\nنیاز: `{total_cost:,}$`"

    conn.execute("UPDATE countries SET money=money-? WHERE id=?", (total_cost, c["id"]))
    conn.execute(
        "INSERT INTO country_tankers (country_id,tanker_type_id,amount) VALUES (?,?,?) "
        "ON CONFLICT(country_id,tanker_type_id) DO UPDATE SET amount=amount+?",
        (c["id"], t_id, amount, amount)
    )
    conn.commit(); conn.close()
    return f"✅ خرید موفق!\n{tt['emoji']} *{tt['name']}* x{amount}\n🛢 ظرفیت حمل: {tt['capacity'] * amount:,} بشکه\n💰 هزینه: `{total_cost:,}$`"

# ═══════════════════════════════════════════════════════
#  پاداش روزانه
# ═══════════════════════════════════════════════════════

def cmd_daily(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."

    conn = get_conn()
    p = conn.execute("SELECT * FROM players WHERE user_id=?", (str(uid),)).fetchone()
    today = str(date.today())

    if p["last_daily"] == today:
        conn.close()
        return "❌ پاداش روزانه رو قبلاً گرفتید.\nفردا دوباره بیایید! 🌅"

    cfg = conn.execute("SELECT * FROM daily_config LIMIT 1").fetchone()
    money_r = cfg["money_reward"]
    oil_r = cfg["oil_reward"]
    sat_r = cfg["satisfaction_reward"]

    conn.execute("UPDATE players SET last_daily=? WHERE user_id=?", (today, str(uid)))
    conn.execute("UPDATE countries SET money=money+?, oil=oil+?, satisfaction=MIN(100,satisfaction+?) WHERE id=?",
                 (money_r, oil_r, sat_r, c["id"]))
    conn.commit(); conn.close()

    return f"""🎁 *پاداش روزانه دریافت شد!*

{c['flag']} *{c['name']}*

💵 +`{money_r:,}` دلار
🛢 +`{oil_r:,}` بشکه نفت
😊 +`{sat_r}%` رضایت مردمی

فردا دوباره بیا! 📅"""

# ═══════════════════════════════════════════════════════
#  ادمین - اقتصاد
# ═══════════════════════════════════════════════════════

def admin_add_money(country_id, amount, by):
    conn = get_conn()
    c = conn.execute("SELECT * FROM countries WHERE id=?", (country_id,)).fetchone()
    if not c:
        conn.close(); return "❌ کشور پیدا نشد."
    conn.execute("UPDATE countries SET money=money+? WHERE id=?", (amount, country_id))
    conn.commit(); conn.close()
    sign = "+" if amount >= 0 else ""
    return f"✅ {c['flag']} {c['name']}: {sign}{amount:,}$ اعمال شد."

def admin_add_all(money, oil, satisfaction, by):
    conn = get_conn()
    conn.execute("UPDATE countries SET money=money+?, oil=oil+?, satisfaction=MIN(100,MAX(0,satisfaction+?)) WHERE is_active=1",
                 (money, oil, satisfaction))
    count = conn.execute("SELECT COUNT(*) FROM countries WHERE is_active=1").fetchone()[0]
    conn.commit(); conn.close()
    return f"✅ به {count} کشور اعمال شد:\n💵 {money:+,}$\n🛢 {oil:+,} بشکه\n😊 {satisfaction:+}%"

def admin_set_daily(money, oil, satisfaction, by):
    conn = get_conn()
    conn.execute("UPDATE daily_config SET money_reward=?, oil_reward=?, satisfaction_reward=?",
                 (money, oil, satisfaction))
    conn.commit(); conn.close()
    return f"✅ پاداش روزانه تنظیم شد:\n💵 {money:,}$\n🛢 {oil:,} بشکه\n😊 {satisfaction}%"

# ═══════════════════════════════════════════════════════
#  بکاپ
# ═══════════════════════════════════════════════════════

def create_backup(by):
    conn = get_conn()
    data = {}
    for tbl in ["countries","players","country_equipment","buildings","country_troops","country_tankers"]:
        rows = conn.execute(f"SELECT * FROM {tbl}").fetchall()
        data[tbl] = [dict(r) for r in rows]
    json_data = json.dumps(data, ensure_ascii=False)
    conn.execute("INSERT INTO backups (created_by,data) VALUES (?,?)", (str(by), json_data))
    conn.commit()
    bid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return f"✅ بکاپ #{bid} ایجاد شد."

def list_backups():
    conn = get_conn()
    rows = conn.execute("SELECT id,backup_time,created_by FROM backups ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()
    if not rows: return "❌ بکاپی وجود نداره."
    t = "💾 *بکاپ‌های اخیر:*\n\n"
    for r in rows:
        t += f"[{r['id']}] {r['backup_time']} | توسط: {r['created_by']}\n"
    return t

def do_rollback(bid, by):
    conn = get_conn()
    b = conn.execute("SELECT * FROM backups WHERE id=?", (bid,)).fetchone()
    if not b:
        conn.close(); return "❌ بکاپ پیدا نشد."
    data = json.loads(b["data"])
    try:
        for tbl, rows in data.items():
            conn.execute(f"DELETE FROM {tbl}")
            for row in rows:
                cols = ",".join(row.keys())
                vals = ",".join(["?"] * len(row))
                conn.execute(f"INSERT INTO {tbl} ({cols}) VALUES ({vals})", list(row.values()))
        conn.commit()
        conn.close()
        return f"✅ rollback به بکاپ #{bid} انجام شد."
    except Exception as e:
        conn.close()
        return f"❌ خطا: {e}"

# ═══════════════════════════════════════════════════════
#  ادمین - تجهیزات بازی
# ═══════════════════════════════════════════════════════

def admin_give_equip(country_id, eq_id, amount, by):
    conn = get_conn()
    c = conn.execute("SELECT * FROM countries WHERE id=?", (country_id,)).fetchone()
    eq = conn.execute("SELECT * FROM equipment_types WHERE id=?", (eq_id,)).fetchone()
    if not c or not eq:
        conn.close(); return "❌ کشور یا تجهیزات پیدا نشد."
    conn.execute(
        "INSERT INTO country_equipment (country_id,equipment_type_id,amount) VALUES (?,?,?) "
        "ON CONFLICT(country_id,equipment_type_id) DO UPDATE SET amount=amount+?",
        (country_id, eq_id, amount, amount)
    )
    conn.commit(); conn.close()
    return f"✅ {eq['emoji']} {eq['name']} x{amount} به {c['flag']} {c['name']} داده شد."

def admin_set_sanction(country_id, status, by):
    conn = get_conn()
    c = conn.execute("SELECT * FROM countries WHERE id=?", (country_id,)).fetchone()
    if not c:
        conn.close(); return "❌ کشور پیدا نشد."
    conn.execute("UPDATE countries SET is_sanctioned=? WHERE id=?", (1 if status else 0, country_id))
    conn.commit(); conn.close()
    state = "تحریم شد 🚫" if status else "تحریم برداشته شد ✅"
    return f"{c['flag']} {c['name']} {state}"

# ═══════════════════════════════════════════════════════
#  متن‌های راهنما
# ═══════════════════════════════════════════════════════

RULES = """⚖️ *قوانین جنگ جهانی*
━━━━━━━━━━━━━━━

📌 *شروع بازی*
⛔ هر بازیکن با ۵ میلیارد دلار وارد می‌شود
🚫 تا ۳ روز اول جنگ بسته است

💵 *جریمه حمله زودرس*
• حمله اول: ۳ میلیارد دلار
• حمله دوم: ۵ میلیارد دلار
• حمله سوم: ۸ میلیارد دلار
• بعدی‌ها: +۲ میلیارد تا سقف ۱۲ میلیارد

📜 *بیانیه‌ها*
• باید شامل پرچم یا تصویر رئیس‌جمهور باشد
• حداقل ۳ خط مفید
• فعالیت روزانه: حداقل ۳ بیانیه

🤝 *اتحادها*
• هر کشور فقط در یک اتحاد می‌تواند عضو باشد
• اتحاد حداکثر ۵ عضو دارد
• خیانت = جریمه ۱۰ میلیارد دلار سازمان ملل

⚔️ *حمله و دفاع*
• فتح کشور نیازمند نیروی زمینی است
• حمله هوایی/موشکی فقط پول منتقل می‌کند
• زمان دفاع: ۴۵ دقیقه
• بدون انبار تسلیحات امکان حمله وجود ندارد
• سناریو باید کامل و با ذکر تجهیزات باشد

📊 *رضایت مردمی*
• روز اول: ۱۰۰٪
• هر روز بدون نفت: کاهش ۱۰٪
• زیر ۴۰٪ = شورش و احتمال از دست دادن پایگاه‌ها
• خرید پروژه‌های رفاهی رضایت را بالا می‌برد

🛢 *سوخت تجهیزات (بشکه نفت)*
✈️ جنگنده: ۲۰۰ | 💣 بمب‌افکن: ۳۰۰
🚢 ناو: ۴۰۰ | ⛴ نفتکش: ۱۵۰
⚓ زیردریایی: ۳۰۰ | ✈️ ترابری هوایی: ۴۰۰

🔄 *خرید و انتقال*
• خرید باید در تگ خرید ثبت و توسط ادمین تأیید شود
• انتقال تجهیزات به متحدان مجاز است
• حمله به محموله مجاز است

/قوانین_تنگه - قوانین تنگه‌های جهانی
/قوانین_تحریم - قوانین تحریم‌ها"""

HELP = """📖 *راهنمای ربات جنگ جهانی*
━━━━━━━━━━━━━━━

🌍 *انتخاب کشور:*
/کشور - منوی انتخاب قاره
/قاره_آسیا - کشورهای آسیا
/قاره_امریکا - کشورهای آمریکا
/قاره_اروپا - کشورهای اروپا
/قاره_آفریقا - کشورهای آفریقا
/country [ID] - انتخاب کشور با شناسه

📊 *اطلاعات:*
/پروفایل - پروفایل کشور
/اقتصاد - وضعیت اقتصادی
/ارتش - تجهیزات نظامی
/ساختمانها - ساختمان‌ها

🛒 *فروشگاه (بر اساس قاره شما):*
/فروشگاه - منوی فروشگاه
/فروشگاه_موشک - موشک‌ها
/فروشگاه_جنگنده - جنگنده‌ها
/فروشگاه_بمب_افکن - بمب‌افکن‌ها
/فروشگاه_دریایی - نیروی دریایی
/فروشگاه_پدافند - پدافند
/فروشگاه_زمینی - تجهیزات زمینی
/فروشگاه_پرتاب - سامانه پرتاب
/فروشگاه_بمب - بمب‌ها
/فروشگاه_پایگاه - پایگاه‌ها
/فروشگاه_ترابری - ترابری
/فروشگاه_ساختمان - پروژه‌های اقتصادی
/فروشگاه_نیرو - نیروی انسانی
/فروشگاه_نفتکش - نفتکش‌ها

💰 *خرید:*
/خرید_تجهیز [ID] [تعداد]
/خرید_ساختمان [ID] [تعداد]
/خرید_نیرو [ID] [تعداد]
/خرید_نفتکش [ID] [تعداد]

🎁 /روزانه - پاداش روزانه
📜 /قوانین - قوانین بازی"""

import random
import string
from config import OWNER_RUBIKA_ID

# ═══════════════════════════════════════════════════════
#  خریدهای پولی (اختراع، VIP، ماهواره)
# ═══════════════════════════════════════════════════════

PREMIUM_ITEMS = {
    # اختراعات آمریکا
    "invention_fighter_america":   {"name": "تولید جنگنده اختصاصی آمریکا",   "price": 50000,  "continent": "آمریکا"},
    "invention_missile_america":   {"name": "تولید موشک اختصاصی آمریکا",     "price": 65000,  "continent": "آمریکا"},
    "invention_defense_america":   {"name": "تولید پدافند اختصاصی آمریکا",   "price": 70000,  "continent": "آمریکا"},
    "invention_drone_america":     {"name": "تولید پهپاد اختصاصی آمریکا",    "price": 80000,  "continent": "آمریکا"},
    "satellite_america":           {"name": "ماهواره جاسوسی آمریکا",          "price": 120000, "continent": "آمریکا"},
    "vip_america":                 {"name": "VIP عقاب سیاه آمریکا 🦅",        "price": 110000, "continent": "آمریکا"},
    # اختراعات آسیا
    "invention_fighter_asia":      {"name": "تولید جنگنده اختصاصی آسیا",     "price": 50000,  "continent": "آسیا"},
    "invention_missile_asia":      {"name": "تولید موشک اختصاصی آسیا",       "price": 65000,  "continent": "آسیا"},
    "invention_defense_asia":      {"name": "تولید پدافند اختصاصی آسیا",     "price": 70000,  "continent": "آسیا"},
    "invention_drone_asia":        {"name": "تولید پهپاد اختصاصی آسیا",      "price": 80000,  "continent": "آسیا"},
    "satellite_asia":              {"name": "ماهواره جاسوسی آسیا",            "price": 120000, "continent": "آسیا"},
    "vip_asia":                    {"name": "VIP اژدهای آسمانی آسیا 🐉",      "price": 85000,  "continent": "آسیا"},
    # اختراعات اروپا
    "invention_fighter_europe":    {"name": "تولید جنگنده اختصاصی اروپا",    "price": 45000,  "continent": "اروپا"},
    "invention_missile_europe":    {"name": "تولید موشک اختصاصی اروپا",      "price": 60000,  "continent": "اروپا"},
    "invention_defense_europe":    {"name": "تولید پدافند اختصاصی اروپا",    "price": 65000,  "continent": "اروپا"},
    "vip_europe":                  {"name": "VIP تاج امپراتوری اروپا 👑",     "price": 85000,  "continent": "اروپا"},
    # اختراعات آفریقا
    "invention_fighter_africa":    {"name": "تولید جنگنده اختصاصی آفریقا",   "price": 45000,  "continent": "آفریقا"},
    "invention_missile_africa":    {"name": "تولید موشک اختصاصی آفریقا",     "price": 60000,  "continent": "آفریقا"},
    "invention_defense_africa":    {"name": "تولید پدافند اختصاصی آفریقا",   "price": 65000,  "continent": "آفریقا"},
    "vip_africa":                  {"name": "VIP الماس سیاه آفریقا 💎",       "price": 70000,  "continent": "آفریقا"},
    # منابع ویژه آفریقا (پولی)
    "diamond_mine":                {"name": "معدن الماس ویژه آفریقا 💎",      "price": 10000,  "continent": "آفریقا"},
    "gold_mine":                   {"name": "معدن طلا ویژه آفریقا 🥇",        "price": 25000,  "continent": "آفریقا"},
    "uranium_mine":                {"name": "معدن اورانیوم ویژه آفریقا ☢️",  "price": 35000,  "continent": "آفریقا"},
    # ارتقاء ماهواره
    "satellite_upgrade2":          {"name": "ارتقاء ماهواره سطح ۲",          "price": 50000,  "continent": "همه"},
    "satellite_upgrade3":          {"name": "ارتقاء ماهواره سطح ۳",          "price": 75000,  "continent": "همه"},
    "satellite_upgrade4":          {"name": "ارتقاء ماهواره سطح ۴",          "price": 100000, "continent": "همه"},
}

def _gen_confirm_code():
    return ''.join(random.choices(string.digits, k=5))

def cmd_shop_premium(uid):
    """نمایش فروشگاه آیتم‌های پولی"""
    c = _get_player_country(uid)
    cont = c["continent"] if c else None

    t = "💎 *فروشگاه ویژه (پولی)*\n\n"
    t += "📌 پس از انتخاب، آیدی مالک برای پرداخت داده می‌شود.\n"
    t += "📌 رسید را ارسال کنید تا کد تایید دریافت کنید.\n\n"

    last_cont = None
    for key, item in PREMIUM_ITEMS.items():
        item_cont = item["continent"]
        if item_cont != "همه" and cont and item_cont != cont:
            continue
        if item_cont != last_cont:
            t += f"\n🗺 *{item_cont}:*\n"
            last_cont = item_cont
        t += f"🔹 `{key}`\n   {item['name']} | 💴 {item['price']:,} تومان\n"

    t += "\n\n📲 برای خرید:\n/buy_premium [کد_آیتم]\nمثال: /buy_premium vip_asia"
    return t

def cmd_buy_premium(uid, username, item_key):
    """شروع فرایند خرید پولی"""
    if item_key not in PREMIUM_ITEMS:
        return "❌ کد آیتم نامعتبر است.\n/shop_premium - مشاهده لیست"

    c = _get_player_country(uid)
    country_name = f"{c['flag']} {c['name']}" if c else "بدون کشور"

    item = PREMIUM_ITEMS[item_key]

    conn = get_conn()
    # بررسی سفارش در انتظار
    existing = conn.execute(
        "SELECT * FROM premium_orders WHERE user_id=? AND status='pending'",
        (str(uid),)
    ).fetchone()
    if existing:
        conn.close()
        return (f"⏳ شما یک سفارش در انتظار دارید:\n"
                f"🛒 {existing['item_name']}\n"
                f"📋 کد سفارش: #{existing['id']}\n\n"
                f"لطفاً ابتدا سفارش قبلی را تکمیل یا لغو کنید.\n"
                f"/cancel_order - لغو سفارش")

    conn.execute(
        "INSERT INTO premium_orders (user_id, country_name, order_type, item_name, price_toman) VALUES (?,?,?,?,?)",
        (str(uid), country_name, item_key, item["name"], item["price"])
    )
    conn.commit()
    order_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()

    t = f"""🛒 *سفارش ثبت شد!*

📦 آیتم: {item['name']}
💴 مبلغ: *{item['price']:,} تومان*
📋 شماره سفارش: #{order_id}
👤 کشور: {country_name}

━━━━━━━━━━━━━━

💳 *مرحله پرداخت:*

۱. مبلغ را به مالک بازی واریز کنید
۲. آیدی مالک: *{OWNER_RUBIKA_ID}*
۳. رسید پرداخت را برای مالک ارسال کنید
۴. مالک کد ۵ رقمی تایید برایتان می‌فرستد
۵. کد را با دستور /confirm_order [کد] وارد کنید

━━━━━━━━━━━━━━
⚠️ برای لغو: /cancel_order"""
    return t

def cmd_cancel_order(uid):
    """لغو سفارش در انتظار"""
    conn = get_conn()
    order = conn.execute(
        "SELECT * FROM premium_orders WHERE user_id=? AND status='pending'",
        (str(uid),)
    ).fetchone()
    if not order:
        conn.close()
        return "❌ سفارش در انتظاری ندارید."
    conn.execute(
        "UPDATE premium_orders SET status='cancelled' WHERE id=?",
        (order["id"],)
    )
    conn.commit()
    conn.close()
    return f"✅ سفارش #{order['id']} لغو شد."

def cmd_confirm_order(uid, code):
    """تایید سفارش با کد ۵ رقمی"""
    conn = get_conn()
    order = conn.execute(
        "SELECT * FROM premium_orders WHERE user_id=? AND status='pending'",
        (str(uid),)
    ).fetchone()
    if not order:
        conn.close()
        return "❌ سفارش در انتظاری ندارید."
    if order["confirm_code"] is None:
        conn.close()
        return "⏳ هنوز کد تایید صادر نشده.\nپس از پرداخت، منتظر کد از مالک باشید."
    if str(order["confirm_code"]) != str(code):
        conn.close()
        return "❌ کد تایید اشتباه است."

    # تایید سفارش و اعمال آیتم
    conn.execute(
        "UPDATE premium_orders SET status='confirmed', confirmed_at=CURRENT_TIMESTAMP WHERE id=?",
        (order["id"],)
    )
    conn.commit()

    result = _apply_premium_item(conn, uid, order["order_type"], order["item_name"])
    conn.close()
    return f"✅ *خرید تایید شد!*\n\n{result}"

def _apply_premium_item(conn, uid, item_key, item_name):
    """اعمال آیتم پریمیوم بعد از تایید"""
    c_row = conn.execute(
        "SELECT c.* FROM players p JOIN countries c ON p.country_id=c.id WHERE p.user_id=?",
        (str(uid),)
    ).fetchone()
    if not c_row:
        return "❌ کشوری انتخاب نکردید."

    cid = c_row["id"]

    if item_key.startswith("invention_"):
        parts = item_key.split("_")
        inv_type = parts[1]
        type_map = {"fighter": "جنگنده", "missile": "موشک", "defense": "پدافند", "drone": "پهپاد"}
        type_fa = type_map.get(inv_type, inv_type)

        init_count = {"fighter": 5, "missile": 10, "defense": 3, "drone": 15}.get(inv_type, 5)
        daily = {"fighter": 2, "missile": 3, "defense": 0, "drone": 5}.get(inv_type, 1)

        conn.execute(
            "INSERT INTO inventions (country_id, invention_type, name, daily_production) VALUES (?,?,?,?)",
            (cid, inv_type, item_name, daily)
        )
        conn.commit()
        return (f"🧪 اختراع *{item_name}* ثبت شد!\n"
                f"📦 تحویل اولیه: {init_count} عدد\n"
                f"⚙️ تولید خودکار: هر شب {daily} عدد")

    elif item_key.startswith("satellite"):
        if item_key == "satellite_upgrade2":
            level = 2
        elif item_key == "satellite_upgrade3":
            level = 3
        elif item_key == "satellite_upgrade4":
            level = 4
        else:
            level = 1
            conn.execute(
                "INSERT OR IGNORE INTO satellites (country_id, level) VALUES (?,1)",
                (cid,)
            )

        conn.execute(
            "INSERT INTO satellites (country_id, level) VALUES (?,?) "
            "ON CONFLICT(country_id) DO UPDATE SET level=MAX(level,?)",
            (cid, level, level)
        )
        conn.commit()

        abilities = {
            1: "مشاهده موشک، جنگنده، بمب‌افکن، ناو و نیروهای دشمن",
            2: "مشاهده تمام پایگاه‌های نظامی/هوایی/موشکی دشمن",
            3: "اطلاع از حمله ۲ ساعت زودتر + مشاهده ناوگان دریایی",
            4: "دسترسی کامل به تمام اطلاعات نظامی کشور هدف",
        }
        return f"🛰 ماهواره جاسوسی سطح {level} فعال شد!\n⭐ {abilities.get(level, '')}"

    elif item_key.startswith("vip_"):
        vip_map = {
            "vip_america": "عقاب سیاه 🦅",
            "vip_asia":    "اژدهای آسمانی 🐉",
            "vip_europe":  "تاج امپراتوری 👑",
            "vip_africa":  "الماس سیاه 💎",
        }
        vip_name = vip_map.get(item_key, "VIP")
        conn.execute(
            "INSERT OR IGNORE INTO country_vip (country_id, vip_type) VALUES (?,?)",
            (cid, vip_name)
        )
        conn.execute(
            "UPDATE country_vip SET vip_type=?, is_active=1 WHERE country_id=?",
            (vip_name, cid)
        )
        conn.execute("UPDATE countries SET is_vip=1 WHERE id=?", (cid,))
        conn.commit()

        bonuses = {
            "vip_america": "💵 ۳ میلیارد دلار + ✈️ ۳ جنگنده + 🚀 ۱۰ موشک کروز + 🛡 ۲ پدافند + 🛰 ۱ ماهواره",
            "vip_asia":    "💵 ۵ میلیارد دلار + 💢 ۱۵ پهپاد + 🤖 هوش مصنوعی + 📈 ۳۰۰M درآمد روزانه",
            "vip_europe":  "💵 ۱۰ میلیارد دلار + 💰 ۱ میلیارد درآمد روزانه + 😊 ۲۰٪ رضایت + 🏭 ۳ پروژه رایگان",
            "vip_africa":  "💵 ۷ میلیارد دلار + 🏔 ۳ معدن + ⛽ ۳۰٪ نفت بیشتر + 📈 ۵۰۰M روزانه",
        }
        bonus_text = bonuses.get(item_key, "")

        # اعمال پول اولیه VIP
        vip_money = {
            "vip_america": 3000000000,
            "vip_asia":    5000000000,
            "vip_europe":  10000000000,
            "vip_africa":  7000000000,
        }
        money = vip_money.get(item_key, 0)
        if money:
            conn.execute("UPDATE countries SET money=money+? WHERE id=?", (money, cid))
            conn.commit()

        return f"👑 VIP *{vip_name}* فعال شد!\n\n🎁 پاداش‌ها:\n{bonus_text}"

    elif item_key in ("diamond_mine", "gold_mine", "uranium_mine"):
        mine_map = {
            "diamond_mine": ("معدن الماس ویژه", 700000000),
            "gold_mine":    ("معدن طلا ویژه",   1500000000),
            "uranium_mine": ("معدن اورانیوم ویژه", 2000000000),
        }
        mine_name, daily_inc = mine_map[item_key]
        conn.execute(
            "INSERT INTO inventions (country_id, invention_type, name, daily_production) VALUES (?,?,?,?)",
            (cid, "mine", mine_name, daily_inc)
        )
        conn.commit()
        return f"⛏ {mine_name} فعال شد!\n💵 درآمد روزانه: {daily_inc//1000000}M دلار"

    return "✅ آیتم فعال شد."

# ─── ادمین: صدور کد تایید ───────────────────────────────

def admin_list_orders(by):
    """لیست سفارش‌های در انتظار"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM premium_orders WHERE status='pending' ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    conn.close()
    if not rows:
        return "📭 سفارش در انتظاری وجود ندارد."
    t = "📋 *سفارش‌های در انتظار:*\n\n"
    for r in rows:
        t += (f"#{r['id']} | {r['country_name']}\n"
              f"   🛒 {r['item_name']}\n"
              f"   💴 {r['price_toman']:,} تومان\n"
              f"   👤 uid: {r['user_id']}\n"
              f"   📅 {r['created_at'][:16]}\n"
              f"   🔑 کد: {r['confirm_code'] or '(صادر نشده)'}\n\n")
    t += "/issue_code [شماره_سفارش] [کد۵رقمی] - صدور کد\n"
    t += "یا /issue_code [شماره_سفارش] auto - کد خودکار"
    return t

def admin_issue_code(order_id, code_input, by):
    """صدور کد تایید برای یک سفارش"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    order = conn.execute("SELECT * FROM premium_orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        conn.close()
        return "❌ سفارش پیدا نشد."
    if order["status"] != "pending":
        conn.close()
        return f"❌ این سفارش در وضعیت {order['status']} است."

    if code_input == "auto":
        code = _gen_confirm_code()
    else:
        if not str(code_input).isdigit() or len(str(code_input)) != 5:
            conn.close()
            return "❌ کد باید ۵ رقم عددی باشد."
        code = str(code_input)

    conn.execute(
        "UPDATE premium_orders SET confirm_code=? WHERE id=?",
        (code, order_id)
    )
    conn.commit()
    conn.close()
    return (f"✅ کد تایید صادر شد!\n\n"
            f"📋 سفارش: #{order_id}\n"
            f"🛒 آیتم: {order['item_name']}\n"
            f"👤 کشور: {order['country_name']}\n"
            f"🔑 *کد تایید: {code}*\n\n"
            f"این کد را برای کاربر (uid: {order['user_id']}) ارسال کنید.")

# ═══════════════════════════════════════════════════════
#  گروهک‌های تروریستی / هکری
# ═══════════════════════════════════════════════════════

TERROR_GROUPS = [
    "القاعده","دزدان دریایی","سپاه","داعش","ابو سیاف",
    "واگنر","الاقصی","حماس","ساواک","پژاک","الشباب",
    "حزب‌الله","فارک","طالبان","حزب نازی","اولستر","چچن"
]
HACKER_GROUPS = ["موساد","حنظله","عدالت علی","انانیموس","دارک وب"]

def cmd_groups_numbered():
    """لیست عددی گروهک‌ها برای انتخاب راحت"""
    all_groups = [
        ("☠","القاعده","terror","عملیات ویژه | جمع‌آوری اطلاعات",""),
        ("🏴","دزدان دریایی","terror","سرقت نفتکش | توقیف کشتی","💎VIP"),
        ("🛡","سپاه","terror","عملیات برون‌مرزی | پشتیبانی متحدان",""),
        ("🦂","داعش","terror","رعب عمومی | خرابکاری اقتصادی","💎VIP"),
        ("🛢","ابو سیاف","terror","ربایش محموله | سرقت نفتکش",""),
        ("🦅","واگنر","terror","تصرف میادین نفتی | عملیات نظامی","💎VIP"),
        ("🌑","الاقصی","terror","عملیات اطلاعاتی | حمله به کاروان",""),
        ("🏴","حماس","terror","عملیات ویژه | حمله به زیرساخت",""),
        ("🦇","ساواک","terror","ضدجاسوسی | کشف عملیات دشمن","💎VIP"),
        ("⚡","پژاک","terror","حمله به خطوط انرژی | عملیات مرزی",""),
        ("🔥","الشباب","terror","سرقت منابع | حمله به کاروان",""),
        ("🛡","حزب‌الله","terror","عملیات ویژه | شبکه اطلاعاتی",""),
        ("🦊","فارک","terror","قاچاق منابع | تصرف موقت مناطق",""),
        ("⚔","طالبان","terror","تصرف مناطق | تصرف منابع طبیعی",""),
        ("☠","حزب نازی","terror","تبلیغات گسترده | جنگ روانی",""),
        ("🍀","اولستر","terror","عملیات شهری | حمله اقتصادی",""),
        ("🗡","چچن","terror","عملیات زمینی ویژه | شناسایی اهداف",""),
        ("🥉","موساد","hack","هک ۱۵٪ پدافند | سرقت ۱۰۰-۲۰۰M$",""),
        ("🥉","حنظله","hack","هک ۱۵٪ پدافند | سرقت ۱۰۰-۲۰۰M$",""),
        ("🥈","عدالت علی","hack","هک ۲۵٪ پدافند | سرقت ۳۰۰-۴۰۰M$",""),
        ("🥇","انانیموس","hack","هک ۴۰٪ پدافند | سرقت ۵۰۰-۶۰۰M$","💎VIP"),
        ("🥇","دارک وب","hack","هک ۴۰٪ پدافند | سرقت ۵۰۰-۶۰۰M$","💎VIP"),
    ]
    t = "☠ *انتخاب گروهک*\n"
    t += "━━━━━━━━━━━━━━\n\n"
    t += "🏴 *گروهک‌های تروریستی/نظامی:*\n\n"
    for i, (em, name, gtype, ab, vip) in enumerate(all_groups, 1):
        if gtype == "hack" and i == 18:
            t += "\n━━━━━━━━━━━━━━\n\n"
            t += "💻 *گروهک‌های هکری:*\n\n"
        vip_str = f" {vip}" if vip else ""
        t += f"`{i}` {em} *{name}*{vip_str}\n"
        t += f"   📌 {ab}\n\n"
    t += "━━━━━━━━━━━━━━\n"
    t += "📌 *برای ثبت‌نام عدد بفرست یا:*\n"
    t += "/ثبت_گروهک [شماره یا نام]\n"
    t += "مثال: `/ثبت_گروهک 6` یا `/ثبت_گروهک واگنر`\n\n"
    t += "💎 VIP = ۲۰ هزار تومان"
    return t, all_groups

def cmd_join_group(uid, username, group_input):
    """ثبت‌نام در یک گروهک"""
    conn = get_conn()
    existing = conn.execute("SELECT * FROM groups WHERE user_id=?", (str(uid),)).fetchone()
    if existing:
        conn.close()
        return f"❌ شما قبلاً در گروهک *{existing['group_name']}* هستید."

    # لیست ترتیبی - قبول عدد یا اسم
    ordered = [
        "القاعده","دزدان دریایی","سپاه","داعش","ابو سیاف",
        "واگنر","الاقصی","حماس","ساواک","پژاک","الشباب",
        "حزب‌الله","فارک","طالبان","حزب نازی","اولستر","چچن",
        "موساد","حنظله","عدالت علی","انانیموس","دارک وب"
    ]
    if group_name.isdigit():
        idx = int(group_name) - 1
        if 0 <= idx < len(ordered):
            group_name = ordered[idx]
        else:
            conn.close()
            return f"❌ شماره نامعتبر. بین ۱ تا {len(ordered)} بفرست.\n/گروهکها - لیست کامل"

    all_groups = TERROR_GROUPS + HACKER_GROUPS
    if group_name not in all_groups:
        conn.close()
        return "❌ نام گروهک نامعتبر.\nبرای لیست: /گروهکها\nمثال: /ثبت_گروهک 6"


    gtype = "hack" if group_name in HACKER_GROUPS else "terror"
    budget = 2000000000 if gtype == "hack" else 3000000000

    conn.execute(
        "INSERT INTO groups (user_id, group_name, group_type, budget) VALUES (?,?,?,?)",
        (str(uid), group_name, gtype, budget)
    )
    conn.commit()
    conn.close()

    emoji = "💻" if gtype == "hack" else "☠"
    return (f"{emoji} *گروهک {group_name} ثبت شد!*\n\n"
            f"💸 بودجه اولیه: {budget//1000000000} میلیارد دلار\n"
            f"👥 نیرو: 500 نفر\n"
            f"😊 وفاداری: 100٪\n"
            f"⚡ قدرت عملیاتی: 100/100\n\n"
            f"/group_profile - پروفایل گروهک\n"
            f"/group_ops - عملیات‌ها")

def cmd_group_profile(uid):
    """پروفایل گروهک"""
    conn = get_conn()
    g = conn.execute("SELECT * FROM groups WHERE user_id=?", (str(uid),)).fetchone()
    conn.close()
    if not g:
        return "❌ در هیچ گروهکی نیستید.\n/join_group [نام] - ثبت‌نام"

    emoji = "💻" if g["group_type"] == "hack" else "☠"
    t = f"""{emoji} *گروهک {g['group_name']}*

━━━━━━━━━━━━━━

💸 بودجه: `{g['budget']:,}` دلار
💰 درآمد روزانه: `{g['daily_income']:,}` دلار
👥 نیروها: `{g['troops']}` نفر
😊 وفاداری: `{g['loyalty']}٪`
⚡ قدرت عملیاتی: `{g['op_power']}/100`
🛡 سطح امنیت: `{g['security']}/100`
📍 کشور مستقر: {g['host_country'] or '(تعیین نشده)'}

━━━━━━━━━━━━━━

/گروهک_عملیات - عملیات‌ها
/گروهک_فروشگاه - فروشگاه گروهک"""
    return t

# ── VIP گروهک‌ها ──────────────────────────────────────
VIP_TERROR = ["دزدان دریایی", "واگنر", "ساواک", "داعش"]
VIP_HACKER = ["انانیموس", "دارک وب"]
VIP_COUNTRIES = ["آمریکا","ایران","ترکیه","مصر","عربستان","قطر","بریتانیا","اسپانیا"]

# ── قابلیت‌های اختصاصی هر گروهک ─────────────────────
GROUP_ABILITIES = {
    "فارک":      ["قاچاق منابع","تصرف موقت مناطق"],
    "طالبان":    ["تصرف مناطق","تصرف منابع طبیعی"],
    "اولستر":    ["عملیات شهری","حمله به اهداف اقتصادی"],
    "چچن":       ["عملیات ویژه زمینی","شناسایی اهداف"],
    "الاقصی":    ["عملیات اطلاعاتی","حمله به کاروان‌های اقتصادی"],
    "حماس":      ["عملیات ویژه","حمله به زیرساخت‌ها"],
    "ساواک":     ["ضدجاسوسی","کشف عملیات مخفی دشمن"],
    "پژاک":      ["حمله به خطوط انتقال انرژی","عملیات مرزی"],
    "الشباب":    ["سرقت منابع طبیعی","حمله به کاروان‌های اقتصادی"],
    "حزب‌الله":  ["عملیات ویژه","شبکه اطلاعاتی"],
    "القاعده":   ["عملیات ویژه","جمع‌آوری اطلاعات"],
    "دزدان دریایی":["سرقت نفتکش","توقیف کشتی‌های تجاری"],
    "سپاه":      ["عملیات برون‌مرزی","پشتیبانی از گروهک‌های متحد"],
    "داعش":      ["ایجاد رعب عمومی","خرابکاری اقتصادی"],
    "ابو سیاف":  ["ربایش محموله‌های اقتصادی","سرقت نفتکش"],
    "واگنر":     ["تصرف میادین نفتی","عملیات نظامی ویژه"],
    "موساد":     ["هک ۱۵٪ پدافند","هک رادارها","سرقت ۱۰۰-۲۰۰M$"],
    "حنظله":     ["هک ۱۵٪ پدافند","هک رادارها","سرقت ۱۰۰-۲۰۰M$"],
    "عدالت علی": ["هک ۲۵٪ پدافند","هک رادارها","سرقت ۳۰۰-۴۰۰M$"],
    "انانیموس":  ["هک ۴۰٪ پدافند","هک رادارها","سرقت ۵۰۰-۶۰۰M$"],
    "دارک وب":   ["هک ۴۰٪ پدافند","هک رادارها","سرقت ۵۰۰-۶۰۰M$"],
}

# ── فروشگاه تجهیزات تروریستی ─────────────────────────
TERROR_SHOP = [
    {"id":1,  "name":"عملیات حذف شخصیت",    "price":800_000_000,  "emoji":"🎯"},
    {"id":2,  "name":"تصرف میدان نفتی",      "price":600_000_000,  "emoji":"🛢"},
    {"id":3,  "name":"حمله به محموله",        "price":450_000_000,  "emoji":"🚢"},
    {"id":4,  "name":"خرابکاری صنعتی",       "price":700_000_000,  "emoji":"🏭"},
    {"id":5,  "name":"تصرف مرکز مخابرات",    "price":550_000_000,  "emoji":"📡"},
    {"id":6,  "name":"باج‌گیری اقتصادی",     "price":500_000_000,  "emoji":"💰"},
    {"id":7,  "name":"اشغال منطقه",           "price":1_000_000_000,"emoji":"🏴"},
    {"id":8,  "name":"ایجاد رعب عمومی",      "price":400_000_000,  "emoji":"😨"},
    {"id":9,  "name":"هویت جعلی",            "price":200_000_000,  "emoji":"🎭"},
    {"id":10, "name":"تیم شناسایی",          "price":300_000_000,  "emoji":"🕵"},
    {"id":11, "name":"خودروی عملیاتی",       "price":150_000_000,  "emoji":"🚐"},
    {"id":12, "name":"شبکه خبرچینان",        "price":400_000_000,  "emoji":"📡"},
    {"id":13, "name":"واحد عملیات ویژه",     "price":750_000_000,  "emoji":"🎯"},
    {"id":14, "name":"اردوگاه آموزشی",       "price":400_000_000,  "emoji":"🏕"},
    {"id":15, "name":"شبکه قاچاق",           "price":750_000_000,  "emoji":"💰"},
    {"id":16, "name":"بازار سیاه تسلیحاتی",  "price":1_000_000_000,"emoji":"🏴"},
    {"id":17, "name":"بسته خرابکاری (۲عدد)", "price":85_000_000,   "emoji":"☠"},
]

# ── فروشگاه تجهیزات هکری ─────────────────────────────
HACK_SHOP = [
    {"id":1,  "name":"سرور رمزنگاری پیشرفته","price":250_000_000,  "emoji":"🔐"},
    {"id":2,  "name":"مرکز عملیات سایبری",   "price":500_000_000,  "emoji":"🖥"},
    {"id":3,  "name":"شبکه جاسوسی بین‌الملل","price":400_000_000,  "emoji":"📡"},
    {"id":4,  "name":"هویت جعلی دیجیتال",    "price":300_000_000,  "emoji":"🎭"},
    {"id":5,  "name":"ماهواره شناسایی سایبری","price":600_000_000, "emoji":"🛰"},
    {"id":6,  "name":"آرشیو اطلاعات محرمانه","price":350_000_000,  "emoji":"📂"},
    {"id":7,  "name":"هوش مصنوعی سایبری",    "price":750_000_000,  "emoji":"🤖"},
    {"id":8,  "name":"دیوار آتش ملی",        "price":450_000_000,  "emoji":"🛡"},
    {"id":9,  "name":"ویروس روز صفر",        "price":900_000_000,  "emoji":"☣️"},
    {"id":10, "name":"شبکه سایه",            "price":800_000_000,  "emoji":"👻"},
    {"id":11, "name":"درب پشتی",             "price":650_000_000,  "emoji":"⚫"},
    # درآمدزا
    {"id":12, "name":"فارم بدافزار",         "price":200_000_000,  "emoji":"🌐", "income":50_000_000},
    {"id":13, "name":"مرکز استخراج اطلاعات", "price":500_000_000,  "emoji":"🖥", "income":100_000_000},
    {"id":14, "name":"شبکه مالی سایه",       "price":2_000_000_000,"emoji":"💳", "income":350_000_000},
    {"id":15, "name":"نفوذ بانکی جهانی",     "price":3_000_000_000,"emoji":"🏦", "income":500_000_000},
    {"id":16, "name":"امپراتوری سایبری",     "price":5_000_000_000,"emoji":"🌍", "income":800_000_000},
]

def cmd_group_shop(uid):
    """فروشگاه گروهک"""
    conn = get_conn()
    g = conn.execute("SELECT * FROM groups WHERE user_id=?", (str(uid),)).fetchone()
    conn.close()
    if not g:
        return "❌ در هیچ گروهکی نیستید.\n/ثبت_گروهک [نام] - ثبت‌نام"

    if g["group_type"] == "hack":
        t = "🖥 *فروشگاه گروهک هکری*\n\n"
        t += f"💸 بودجه شما: `{g['budget']:,}$`\n\n"
        t += "━━━━━━━━━━━━━━\n\n"
        t += "🔐 *تجهیزات عملیاتی:*\n"
        for item in HACK_SHOP[:11]:
            t += f"`{item['id']}` {item['emoji']} {item['name']}\n    💰 `{item['price']//1_000_000}M$`\n"
        t += "\n📈 *تجهیزات درآمدزا:*\n"
        for item in HACK_SHOP[11:]:
            inc = item.get("income", 0)
            t += f"`{item['id']}` {item['emoji']} {item['name']}\n    💰 `{item['price']//1_000_000}M$` | درآمد: `{inc//1_000_000}M$/روز`\n"
        t += "\n📌 برای خرید: /گروهک_خرید [شماره]"
    else:
        t = "☠ *فروشگاه گروهک تروریستی*\n\n"
        t += f"💸 بودجه شما: `{g['budget']:,}$`\n\n"
        t += "━━━━━━━━━━━━━━\n\n"
        for item in TERROR_SHOP:
            t += f"`{item['id']}` {item['emoji']} {item['name']}\n    💰 `{item['price']//1_000_000}M$`\n"
        t += "\n📌 برای خرید: /گروهک_خرید [شماره]"
    return t

def cmd_group_buy(uid, item_id):
    """خرید از فروشگاه گروهک"""
    conn = get_conn()
    g = conn.execute("SELECT * FROM groups WHERE user_id=?", (str(uid),)).fetchone()
    if not g:
        conn.close()
        return "❌ در هیچ گروهکی نیستید."

    shop = HACK_SHOP if g["group_type"] == "hack" else TERROR_SHOP
    item = next((x for x in shop if x["id"] == item_id), None)
    if not item:
        conn.close()
        return "❌ شماره آیتم نامعتبر."

    if g["budget"] < item["price"]:
        conn.close()
        return f"❌ بودجه کافی نیست.\nدارید: `{g['budget']:,}$`\nنیاز: `{item['price']:,}$`"

    new_budget = g["budget"] - item["price"]
    new_income = g["daily_income"] + item.get("income", 0)
    conn.execute(
        "UPDATE groups SET budget=?, daily_income=? WHERE user_id=?",
        (new_budget, new_income, str(uid))
    )
    conn.commit()
    conn.close()
    return (f"✅ *{item['emoji']} {item['name']} خریداری شد!*\n\n"
            f"💸 بودجه باقیمانده: `{new_budget:,}$`\n"
            f"📌 برای استفاده از عملیات: /گروهک_عملیات")

def cmd_group_ops(uid):
    """لیست عملیات‌های گروهک"""
    conn = get_conn()
    g = conn.execute("SELECT * FROM groups WHERE user_id=?", (str(uid),)).fetchone()
    conn.close()
    if not g:
        return "❌ در هیچ گروهکی نیستید."

    abilities = GROUP_ABILITIES.get(g["group_name"], [])
    emoji = "💻" if g["group_type"] == "hack" else "☠"

    t = f"{emoji} *عملیات‌های {g['group_name']}*\n\n"
    t += "━━━━━━━━━━━━━━\n\n"
    t += "🎯 *قابلیت‌های اختصاصی:*\n"
    for ab in abilities:
        t += f"• {ab}\n"

    t += "\n⚔️ *قابلیت‌های مشترک همه گروهک‌ها:*\n"
    t += "• ترور شخصیت‌های سیاسی/نظامی/اقتصادی\n"
    t += "• خرابکاری در پروژه‌ها و تأسیسات\n"
    t += "• کاهش رضایت مردمی کشور هدف\n"
    t += "• سرقت محموله‌های اقتصادی\n"
    t += "• جمع‌آوری اطلاعات\n"
    t += "• عملیات ویژه با تأیید ادمین\n\n"
    t += "━━━━━━━━━━━━━━\n\n"
    t += "📌 *نحوه استفاده:*\n"
    t += "۱. از /گروهک_فروشگاه تجهیزات بخرید\n"
    t += "۲. برای هر عملیات، درخواست رو به ادمین بفرستید\n"
    t += "۳. نتیجه فقط توسط ادمین تعیین می‌شود\n\n"
    t += "⚠️ هیچ عملیاتی موفقیت ۱۰۰٪ ندارد"
    return t

def cmd_group_set_host(uid, country_name):
    """تنظیم کشور مستقر"""
    conn = get_conn()
    g = conn.execute("SELECT * FROM groups WHERE user_id=?", (str(uid),)).fetchone()
    if not g:
        conn.close()
        return "❌ در هیچ گروهکی نیستید."
    conn.execute("UPDATE groups SET host_country=? WHERE user_id=?", (country_name, str(uid)))
    conn.commit()
    conn.close()
    return f"✅ کشور مستقر به *{country_name}* تغییر یافت."

def cmd_vip_countries():
    """لیست کشورهای VIP"""
    t = "💎 *کشورهای VIP بازی*\n\n"
    t += "━━━━━━━━━━━━━━\n\n"
    vip_info = [
        ("🇺🇸","آمریکا","کنترل کانال پاناما + قوی‌ترین ارتش"),
        ("🇮🇷","ایران","کنترل تنگه هرمز + تولید ۹۰۰۰ بشکه نفت"),
        ("🇹🇷","ترکیه","کنترل تنگه بسفر + موقعیت استراتژیک"),
        ("🇪🇬","مصر","کنترل کانال سوئز + تولید نفت"),
        ("🇸🇦","عربستان","تولید ۹۳۰۰ بشکه نفت + VIP"),
        ("🇶🇦","قطر","تولید ۶۵۰۰ بشکه نفت + VIP"),
        ("🇬🇧","بریتانیا","کنترل جبل‌الطارق + نیروی دریایی قوی"),
        ("🇪🇸","اسپانیا","کنترل جبل‌الطارق + موقعیت دریایی"),
    ]
    for flag, name, desc in vip_info:
        t += f"{flag} *{name}*\n   📌 {desc}\n   💰 قیمت VIP: ۲۰ هزار تومان\n\n"
    t += "━━━━━━━━━━━━━━\n"
    t += "📌 برای خرید VIP با مالک تماس بگیرید"
    return t

def cmd_vip_groups():
    """لیست گروهک‌های VIP"""
    t = "💎 *گروهک‌های VIP بازی*\n\n"
    t += "━━━━━━━━━━━━━━\n\n"
    t += "💻 *گروهک‌های هکری VIP:*\n\n"
    hack_vip = [
        ("👻","انانیموس","هک ۴۰٪ پدافند | سرقت ۵۰۰-۶۰۰M$"),
        ("⚡","دارک وب","هک ۴۰٪ پدافند | سرقت ۵۰۰-۶۰۰M$"),
    ]
    for em, name, desc in hack_vip:
        t += f"{em} *{name}*\n   📌 {desc}\n   💰 قیمت VIP: ۲۰ هزار تومان\n\n"

    t += "━━━━━━━━━━━━━━\n\n"
    t += "☠ *گروهک‌های تروریستی VIP:*\n\n"
    terror_vip = [
        ("🏴","دزدان دریایی","سرقت نفتکش | توقیف کشتی‌های تجاری"),
        ("⚔","واگنر","تصرف میادین نفتی | عملیات نظامی ویژه"),
        ("🎭","ساواک","ضدجاسوسی | کشف عملیات مخفی دشمن"),
        ("☠","داعش","ایجاد رعب عمومی | خرابکاری اقتصادی"),
    ]
    for em, name, desc in terror_vip:
        t += f"{em} *{name}*\n   📌 {desc}\n   💰 قیمت VIP: ۲۰ هزار تومان\n\n"

    t += "━━━━━━━━━━━━━━\n"
    t += "📌 برای خرید VIP با مالک تماس بگیرید"
    return t

def cmd_groups_list():
    """لیست کامل گروهک‌ها"""
    t = """☠ *گروهک‌های تروریستی/نظامی:*

━━━━━━━━━━━━━━

🌙 *القاعده*
   📌 عملیات ویژه با تأیید ادمین
   📌 جمع‌آوری اطلاعات محرمانه
   💰 بودجه شروع: ۳ میلیارد دلار

🏴 *دزدان دریایی* 💎 VIP
   📌 سرقت نفتکش و دریافت ارزش محموله
   📌 توقیف کشتی‌های تجاری
   💰 بودجه شروع: ۳ میلیارد دلار

🛡 *سپاه*
   📌 عملیات برون‌مرزی
   📌 پشتیبانی از گروهک‌های متحد
   💰 بودجه شروع: ۳ میلیارد دلار

🦂 *داعش* 💎 VIP
   📌 ایجاد رعب عمومی (کاهش ۵-۲۰٪ رضایت)
   📌 خرابکاری اقتصادی
   💰 بودجه شروع: ۳ میلیارد دلار

🛢 *ابو سیاف*
   📌 ربایش محموله‌های اقتصادی
   📌 سرقت نفتکش
   💰 بودجه شروع: ۳ میلیارد دلار

🦅 *واگنر* 💎 VIP
   📌 تصرف میادین نفتی (درآمد موقت)
   📌 عملیات نظامی ویژه با قدرت بیشتر
   💰 بودجه شروع: ۳ میلیارد دلار

🌑 *الاقصی*
   📌 عملیات اطلاعاتی (کشف اطلاعات محرمانه)
   📌 حمله به کاروان‌های اقتصادی
   💰 بودجه شروع: ۳ میلیارد دلار

🏴 *حماس*
   📌 عملیات ویژه با تأیید ادمین
   📌 حمله به زیرساخت‌های اقتصادی
   💰 بودجه شروع: ۳ میلیارد دلار

🦇 *ساواک* 💎 VIP
   📌 ضدجاسوسی (شناسایی جاسوسان)
   📌 کشف عملیات مخفی دشمن پیش از اجرا
   💰 بودجه شروع: ۳ میلیارد دلار

⚡ *پژاک*
   📌 حمله به خطوط انتقال انرژی
   📌 عملیات مرزی
   💰 بودجه شروع: ۳ میلیارد دلار

🔥 *الشباب*
   📌 سرقت منابع طبیعی
   📌 حمله به کاروان‌های اقتصادی
   💰 بودجه شروع: ۳ میلیارد دلار

🛡 *حزب‌الله*
   📌 عملیات ویژه با تأیید ادمین
   📌 شبکه اطلاعاتی گسترده
   💰 بودجه شروع: ۳ میلیارد دلار

🦊 *فارک*
   📌 قاچاق منابع (درآمد مخفی)
   📌 تصرف موقت مناطق
   💰 بودجه شروع: ۳ میلیارد دلار

⚔ *طالبان*
   📌 تصرف مناطق و شهرها
   📌 تصرف منابع طبیعی
   💰 بودجه شروع: ۳ میلیارد دلار

☠ *حزب نازی*
   📌 تبلیغات گسترده (کاهش رضایت هدف)
   📌 جنگ روانی و بی‌ثباتی در کشور هدف
   💰 بودجه شروع: ۳ میلیارد دلار

🍀 *اولستر*
   📌 عملیات شهری در شهرهای بزرگ
   📌 حمله به اهداف اقتصادی
   💰 بودجه شروع: ۳ میلیارد دلار

🗡 *چچن*
   📌 عملیات ویژه زمینی (شانس موفقیت بالاتر)
   📌 شناسایی اهداف و تأسیسات
   💰 بودجه شروع: ۳ میلیارد دلار

━━━━━━━━━━━━━━

⚔️ *قابلیت مشترک همه گروهک‌ها:*
• ترور شخصیت سیاسی/نظامی/اقتصادی
• خرابکاری در پروژه‌ها و تأسیسات
• کاهش رضایت مردمی کشور هدف
• سرقت محموله‌های اقتصادی
• جمع‌آوری اطلاعات
• عملیات ویژه با تأیید ادمین

━━━━━━━━━━━━━━

💻 *گروهک‌های هکری:*

🥉 *موساد* [هکر عادی]
   📌 هک ۱۵٪ پدافند از هر نوع
   📌 هک تمامی رادارها
   📌 سرقت ۱۰۰ تا ۲۰۰ میلیون دلار
   💰 بودجه شروع: ۲ میلیارد دلار

🥉 *حنظله* [هکر عادی]
   📌 هک ۱۵٪ پدافند از هر نوع
   📌 هک تمامی رادارها
   📌 سرقت ۱۰۰ تا ۲۰۰ میلیون دلار
   💰 بودجه شروع: ۲ میلیارد دلار

🥈 *عدالت علی* [هکر متوسط]
   📌 هک ۲۵٪ پدافند از هر نوع
   📌 هک تمامی رادارها
   📌 سرقت ۳۰۰ تا ۴۰۰ میلیون دلار
   💰 بودجه شروع: ۲ میلیارد دلار

🥇 *انانیموس* 💎 VIP [هکر عالی]
   📌 هک ۴۰٪ پدافند از هر نوع
   📌 هک تمامی رادارها
   📌 سرقت ۵۰۰ تا ۶۰۰ میلیون دلار
   💰 بودجه شروع: ۲ میلیارد دلار

🥇 *دارک وب* 💎 VIP [هکر عالی]
   📌 هک ۴۰٪ پدافند از هر نوع
   📌 هک تمامی رادارها
   📌 سرقت ۵۰۰ تا ۶۰۰ میلیون دلار
   💰 بودجه شروع: ۲ میلیارد دلار

━━━━━━━━━━━━━━

💎 *گروهک‌های VIP هر کدام ۲۰ هزار تومان*
📌 برای عضویت: /ثبت_گروهک [نام]
📌 فروشگاه: /گروهک_فروشگاه
📌 عملیات: /گروهک_عملیات
⚠️ نتیجه همه عملیات‌ها توسط ادمین تعیین می‌شود"""
    return t

def cmd_create_alliance(uid, alliance_name):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    conn = get_conn()
    existing = conn.execute(
        "SELECT a.name FROM alliance_members am JOIN alliances a ON am.alliance_id=a.id WHERE am.country_id=?",
        (c["id"],)
    ).fetchone()
    if existing:
        conn.close()
        return f"❌ شما عضو اتحاد *{existing['name']}* هستید."
    try:
        conn.execute(
            "INSERT INTO alliances (name, leader_country_id) VALUES (?,?)",
            (alliance_name, c["id"])
        )
        conn.commit()
        aid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO alliance_members (alliance_id, country_id) VALUES (?,?)", (aid, c["id"]))
        conn.commit()
        conn.close()
        return (f"✅ اتحاد *{alliance_name}* ایجاد شد!\n"
                f"👑 رهبر: {c['flag']} {c['name']}\n"
                f"📋 اعضا: ۱/۵\n\n"
                f"برای دعوت: /alliance_invite [ID_کشور]")
    except:
        conn.close()
        return "❌ این نام قبلاً استفاده شده."

def cmd_alliance_invite(uid, target_cid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    conn = get_conn()
    am = conn.execute(
        "SELECT a.* FROM alliance_members am JOIN alliances a ON am.alliance_id=a.id WHERE am.country_id=?",
        (c["id"],)
    ).fetchone()
    if not am:
        conn.close()
        return "❌ در هیچ اتحادی نیستید."
    if am["leader_country_id"] != c["id"]:
        conn.close()
        return "❌ فقط رهبر اتحاد می‌تواند دعوت کند."
    member_count = conn.execute("SELECT COUNT(*) FROM alliance_members WHERE alliance_id=?", (am["id"],)).fetchone()[0]
    if member_count >= 5:
        conn.close()
        return "❌ اتحاد پر است (حداکثر ۵ عضو)."
    target = conn.execute("SELECT * FROM countries WHERE id=?", (target_cid,)).fetchone()
    if not target:
        conn.close()
        return "❌ کشور پیدا نشد."
    existing_m = conn.execute("SELECT * FROM alliance_members WHERE country_id=?", (target_cid,)).fetchone()
    if existing_m:
        conn.close()
        return f"❌ {target['flag']} {target['name']} در یک اتحاد دیگر است."
    conn.execute("INSERT INTO alliance_members (alliance_id, country_id) VALUES (?,?)", (am["id"], target_cid))
    conn.commit()
    conn.close()
    return f"✅ {target['flag']} {target['name']} به اتحاد *{am['name']}* اضافه شد."

def cmd_alliance_info(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    conn = get_conn()
    am = conn.execute(
        "SELECT a.* FROM alliance_members m JOIN alliances a ON m.alliance_id=a.id WHERE m.country_id=?",
        (c["id"],)
    ).fetchone()
    if not am:
        conn.close()
        return "❌ عضو هیچ اتحادی نیستید.\n/create_alliance [نام] - ایجاد اتحاد"
    members = conn.execute(
        "SELECT c.flag, c.name, c.id FROM alliance_members m JOIN countries c ON m.country_id=c.id WHERE m.alliance_id=?",
        (am["id"],)
    ).fetchall()
    conn.close()
    t = f"🤝 *اتحاد: {am['name']}*\n\n👥 اعضا ({len(members)}/5):\n"
    for i, m in enumerate(members, 1):
        is_leader = " 👑" if m["id"] == am["leader_country_id"] else ""
        t += f"{i}. {m['flag']} {m['name']}{is_leader}\n"
    t += "\n⚠️ خیانت = جریمه ۱۰ میلیارد دلار"
    return t

def cmd_leave_alliance(uid):
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    conn = get_conn()
    am_row = conn.execute(
        "SELECT am.*, a.name, a.leader_country_id FROM alliance_members am JOIN alliances a ON am.alliance_id=a.id WHERE am.country_id=?",
        (c["id"],)
    ).fetchone()
    if not am_row:
        conn.close()
        return "❌ عضو هیچ اتحادی نیستید."
    conn.execute("DELETE FROM alliance_members WHERE country_id=?", (c["id"],))
    conn.commit()
    conn.close()
    return f"✅ از اتحاد *{am_row['name']}* خارج شدید.\n⚠️ جریمه خیانت: ۱۰ میلیارد دلار توسط ادمین اعمال می‌شود."

# ═══════════════════════════════════════════════════════
#  تنگه‌ها
# ═══════════════════════════════════════════════════════

def cmd_straits_info():
    """نمایش وضعیت تنگه‌ها"""
    conn = get_conn()
    rows = conn.execute("SELECT * FROM straits ORDER BY id").fetchall()
    conn.close()
    if not rows:
        return "❌ اطلاعات تنگه‌ها موجود نیست."
    t = "🌊 *وضعیت تنگه‌های جهانی*\n\n"
    for r in rows:
        status = "🔴 بسته" if r["is_closed"] else "🟢 باز"
        t += f"❤️ *{r['name']}*\n"
        t += f"   🏳 کنترل: {r['controller_country']}\n"
        t += f"   {status}\n"
        if r["is_closed"] and r["closed_by"]:
            t += f"   🔒 بسته‌شده توسط: {r['closed_by']}\n"
        t += "\n"
    return t

def admin_toggle_strait(strait_name, close, by, closer=""):
    """باز/بستن تنگه توسط ادمین"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    r = conn.execute("SELECT * FROM straits WHERE name=?", (strait_name,)).fetchone()
    if not r:
        conn.close()
        return "❌ تنگه پیدا نشد."
    conn.execute(
        "UPDATE straits SET is_closed=?, closed_by=?, closed_at=CURRENT_TIMESTAMP WHERE name=?",
        (1 if close else 0, closer if close else "", strait_name)
    )
    conn.commit()
    conn.close()
    action = "بسته شد 🔴" if close else "باز شد 🟢"
    return f"✅ تنگه *{strait_name}* {action}"

# ═══════════════════════════════════════════════════════
#  سیستم رضایت مردمی و نفت
# ═══════════════════════════════════════════════════════

def admin_daily_tick(by):
    """اجرای tick روزانه: کاهش رضایت بدون نفت + درآمد ساختمان‌ها"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    countries = conn.execute("SELECT * FROM countries WHERE is_active=1").fetchall()
    results = []
    for c in countries:
        changes = []
        new_money = c["money"]
        new_oil = c["oil"]
        new_sat = c["satisfaction"]

        # درآمد ساختمان‌ها
        income_rows = conn.execute(
            "SELECT bt.effect_value, b.amount FROM buildings b "
            "JOIN building_types bt ON b.building_type_id=bt.id "
            "WHERE b.country_id=? AND bt.effect_type='money' AND b.amount>0",
            (c["id"],)
        ).fetchall()
        total_income = sum(r["effect_value"] * r["amount"] for r in income_rows)
        if total_income > 0:
            new_money += total_income
            changes.append(f"💵 +{total_income//1000000}M$ درآمد")

        # اضافه کردن نفت روزانه
        if c["daily_oil"] > 0:
            new_oil += c["daily_oil"]
            changes.append(f"🛢 +{c['daily_oil']} بشکه")

        # کاهش رضایت بدون نفت
        if c["oil"] <= 0:
            new_sat = max(0, new_sat - 10)
            changes.append("😠 -10% رضایت (بدون نفت)")

        conn.execute(
            "UPDATE countries SET money=?, oil=?, satisfaction=? WHERE id=?",
            (new_money, new_oil, new_sat, c["id"])
        )

        if changes:
            results.append(f"{c['flag']} {c['name']}: {' | '.join(changes)}")

    conn.commit()
    conn.close()
    if not results:
        return "✅ Tick روزانه اجرا شد. تغییری نبود."
    return "✅ *Tick روزانه اجرا شد:*\n\n" + "\n".join(results)

# ═══════════════════════════════════════════════════════
#  انتقال پول بین کشورها
# ═══════════════════════════════════════════════════════

def cmd_transfer_money(uid, target_cid, amount):
    """انتقال پول به کشور دیگر"""
    if amount <= 0:
        return "❌ مبلغ باید مثبت باشد."
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    if c["money"] < amount:
        return f"❌ بودجه کافی نیست.\nدارید: `{c['money']:,}$`"
    conn = get_conn()
    target = conn.execute("SELECT * FROM countries WHERE id=?", (target_cid,)).fetchone()
    if not target:
        conn.close()
        return "❌ کشور مقصد پیدا نشد."
    conn.execute("UPDATE countries SET money=money-? WHERE id=?", (amount, c["id"]))
    conn.execute("UPDATE countries SET money=money+? WHERE id=?", (amount, target_cid))
    conn.commit()
    conn.close()
    return (f"✅ *انتقال موفق!*\n\n"
            f"از: {c['flag']} {c['name']}\n"
            f"به: {target['flag']} {target['name']}\n"
            f"💵 مبلغ: `{amount:,}$`")

# ═══════════════════════════════════════════════════════
#  بیانیه (فرم رسمی)
# ═══════════════════════════════════════════════════════

def cmd_declaration_form(uid):
    """نمایش فرم بیانیه"""
    c = _get_player_country(uid)
    if not c:
        return "❌ کشوری انتخاب نکردید."
    return (f"🔥 *فرم بیانیه رسمی*\n\n"
            f"متن زیر را کپی کرده، تکمیل و ارسال کنید:\n\n"
            f"━━━━━━━━━━━━━━⊱✿⊰━━━━━━━━━━━━━━\n"
            f"🌐 کشور: {c['flag']} {c['name']}\n"
            f"👤 صادرکننده: (نام شما)\n"
            f"📍 مکان صدور: (مثلاً کاخ ریاست جمهوری)\n"
            f"━━━━━━━━━━━━━━⊱✿⊰━━━━━━━━━━━━━━\n"
            f"📝 متن بیانیه:\n"
            f"________\n"
            f"________\n"
            f"________\n"
            f"━━━━━━━━━━━━━━⊱✿⊰━━━━━━━━━━━━━━\n"
            f"📌 حداقل ۳ خط مفید | زبان فارسی")

# ═══════════════════════════════════════════════════════
#  تگ‌های رسمی
# ═══════════════════════════════════════════════════════

def cmd_tags(uid):
    """نمایش تگ‌های رسمی"""
    c = _get_player_country(uid)
    country_name = f"{c['flag']} {c['name']}" if c else "کشور شما"
    return f"""📋 *تگ‌های رسمی بازی*

📟💸 *تگ خرید:*
📌📜 نام کشور/گروهک: {country_name}
♨️📟 تجهیزات خریداری شده: __
♨️📟 جمع خرید 💸: __
🪙💽 باقیمانده 💰: __

━━━━━━━━━━━━

♨️📟 *تگ انتقال محموله:*
📢 نام کشور: {country_name}
♨️ تجهیزات منتقل شده: __
🏷️ کشور گیرنده: __
☠️ مدافع محموله: __

━━━━━━━━━━━━

✈️ *فرم سفر:*
[ 👤 ] نام مسافر: __
[ 📍 ] کشور مبدا: {country_name}
[ 📌 ] کشور مقصد: __
[ ✈️ ] اسکورت: __
[ 🛫 ] زمان حرکت: __

━━━━━━━━━━━━

#فرم_انتقال_پول
👑 از کشور: {country_name}
👑 به کشور: __
💸 مبلغ: __"""

# ═══════════════════════════════════════════════════════
#  لیدربورد
# ═══════════════════════════════════════════════════════

def cmd_leaderboard():
    """رتبه‌بندی کشورها"""
    conn = get_conn()
    countries = conn.execute(
        "SELECT c.*, "
        "COALESCE((SELECT SUM(ct.amount) FROM country_troops ct WHERE ct.country_id=c.id),0) as total_troops, "
        "COALESCE((SELECT SUM(ce.amount) FROM country_equipment ce WHERE ce.country_id=c.id),0) as total_equip "
        "FROM countries c WHERE c.is_active=1 ORDER BY c.money DESC LIMIT 10"
    ).fetchall()
    conn.close()
    if not countries:
        return "❌ هنوز بازیکنی نیست."
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    t = "🏆 *لیدربورد قدرتمندترین کشورها*\n\n"
    for i, c in enumerate(countries):
        vip = "👑" if c["is_vip"] else ""
        t += (f"{medals[i]} {vip}{c['flag']} *{c['name']}*\n"
              f"   💵 `{c['money']//1000000000:.1f}B$` | "
              f"🪖 `{c['total_troops']:,}` | "
              f"⚔️ `{c['total_equip']:,}`\n\n")
    return t

# ═══════════════════════════════════════════════════════
#  بروزرسانی HELP و RULES
# ═══════════════════════════════════════════════════════

RULES = """⚖️ *قوانین جنگ جهانی*

📌 *شروع بازی*
⛔ هر بازیکن با ۵ میلیارد دلار وارد می‌شود
🚫 تا ۳ روز اول جنگ بسته است

💵 *جریمه حمله زودرس*
• حمله اول: ۳ میلیارد دلار
• حمله دوم: ۵ میلیارد دلار
• حمله سوم: ۸ میلیارد دلار
• بعدی‌ها: +۲ میلیارد تا سقف ۱۲ میلیارد

🤝 *اتحادها*
• هر کشور فقط در یک اتحاد می‌تواند عضو باشد
• اتحاد حداکثر ۵ عضو دارد
• خیانت = جریمه ۱۰ میلیارد دلار

⚔️ *حمله و دفاع*
• فتح کشور نیازمند نیروی زمینی است
• حمله هوایی/موشکی فقط پول منتقل می‌کند
• زمان دفاع: ۴۵ دقیقه
• بدون انبار تسلیحات امکان حمله وجود ندارد

📊 *رضایت مردمی*
• هر روز بدون نفت: کاهش ۱۰٪
• زیر ۴۰٪ = احتمال شورش
• خرید پروژه‌های رفاهی رضایت را بالا می‌برد

🛢 *سوخت تجهیزات (هر بار استفاده)*
✈️ جنگنده: 200 بشکه | 💣 بمب‌افکن: 300 بشکه
🚢 ناو: 400 بشکه | ⚓ زیردریایی: 300 بشکه
🚢 ترابری: 300 بشکه | ⛴ نفتکش: 150 بشکه

📉 *تحریم بین‌المللی*
• حداقل ۵ کشور باید موافق باشند
• مدت: ۷ روز
• کاهش ۱۵٪ رضایت + ۲۰٪ کاهش درآمد نفت"""

HELP = """📖 *راهنمای کامل دستورات*

━━━━━━━━━━━━━━
💡 *میانبر عددی:* فقط عدد بفرست!
1=کشور | 2=پروفایل | 3=اقتصاد | 4=ارتش
5=ساختمانها | 6=فروشگاه | 7=روزانه
8=رتبه‌بندی | 9=اتحاد | 10=گروهک‌ها
━━━━━━━━━━━━━━

🌍 *کشور و پروفایل:*
/کشور — لیست کشورها و انتخاب
/کشور [شماره] — انتخاب مستقیم (مثال: /کشور 3)
/قاره_آسیا | /قاره_اروپا | /قاره_امریکا | /قاره_آفریقا
/پروفایل — پروفایل کشور شما
/اقتصاد — وضعیت اقتصادی و درآمد
/ارتش — لیست کامل تجهیزات
/ساختمانها — ساختمان‌ها و پروژه‌ها

━━━━━━━━━━━━━━

🛒 *خرید تجهیزات:*
/فروشگاه — فروشگاه اصلی
/فروشگاه_موشک — موشک‌ها
/فروشگاه_جنگنده — جنگنده‌ها و بمب‌افکن‌ها
/فروشگاه_دریایی — نیروی دریایی
/فروشگاه_پدافند — سامانه‌های پدافندی
/فروشگاه_زمینی — تجهیزات زمینی
/فروشگاه_پرتاب — سامانه‌های پرتاب
/فروشگاه_بمب — بمب‌های سنگین
/فروشگاه_پایگاه — ساختمان‌های نظامی
/فروشگاه_ترابری — وسایل نقلیه ترابری
/فروشگاه_ساختمان — پروژه‌های اقتصادی
/فروشگاه_نیرو — نیروی انسانی
/فروشگاه_نفتکش — نفتکش‌ها
/فروشگاه_ویژه — آیتم‌های پولی 💎

📌 *نحوه خرید:*
/خرید_تجهیز [شناسه] [تعداد]
/خرید_ساختمان [شناسه] [تعداد]
/خرید_نیرو [شناسه] [تعداد]
/خرید_نفتکش [شناسه] [تعداد]

━━━━━━━━━━━━━━

💰 *مالی و اقتصاد:*
/روزانه — دریافت پاداش روزانه
/انتقال [ID_کشور] [مبلغ] — انتقال پول
/رتبه_بندی — رتبه‌بندی قدرتمندترین کشورها

━━━━━━━━━━━━━━

🤝 *اتحادها:*
/اتحاد — اطلاعات اتحاد فعلی
/ایجاد_اتحاد [نام] — ایجاد اتحاد جدید
/دعوت_اتحاد [ID_کشور] — دعوت کشور به اتحاد
/خروج_اتحاد — خروج از اتحاد

━━━━━━━━━━━━━━

☠ *گروهک‌ها:*
/گروهکها — لیست همه گروهک‌ها
/ثبت_گروهک [نام] — عضویت در گروهک
/پروفایل_گروهک — پروفایل گروهکت
/گروهک_فروشگاه — فروشگاه تجهیزات
/گروهک_خرید [شماره] — خرید از فروشگاه
/گروهک_عملیات — لیست عملیات‌ها
/گروهک_مستقر [نام کشور] — تعیین کشور مستقر

━━━━━━━━━━━━━━

💎 *VIP (هر کدام ۲۰ هزار تومان):*
/vip_کشورها — کشورهای VIP و مزایا
/vip_گروهکها — گروهک‌های VIP و مزایا
/فروشگاه_ویژه — خرید آیتم‌های پولی
/خرید_ویژه [کد] — ثبت سفارش پولی
/تایید_سفارش [کد۵رقمی] — تایید خرید

━━━━━━━━━━━━━━

🌊 *تنگه‌ها و قوانین:*
/تنگه_ها — وضعیت تنگه‌های جهانی
/قوانین_تنگه — قوانین تنگه‌ها
/قوانین_تحریم — قوانین تحریم
/قوانین — قوانین کامل بازی

━━━━━━━━━━━━━━

📋 *فرم‌های رسمی:*
/بیانیه — فرم بیانیه رسمی
/تگها — تگ‌های رسمی خرید و انتقال

━━━━━━━━━━━━━━

👮 *دستورات ادمین:*
/ادمین — پنل ادمین
/سفارشات — سفارشات پولی در انتظار
/کد_تایید [ID] [کد|auto] — صدور کد
/افزودن_پول [ID] [مبلغ] — افزودن بودجه
/اعطای_تجهیز [cID] [eID] [تعداد]
/تیک_روزانه — اجرای tick روزانه
/تنگه [نام] [close|open]
/تحریم [ID] | /رفع_تحریم [ID]
/بکاپ | /لیست_بکاپ | /بازگردانی [ID]"""

# ═══════════════════════════════════════════════════════
#  پنل مدیریت کامل
# ═══════════════════════════════════════════════════════

def admin_panel_main(uid):
    """پنل اصلی مدیریت"""
    if not is_admin(uid):
        return "❌ دسترسی ندارید."
    owner = is_owner(uid)
    t = "👑 *پنل مدیریت جنگ جهانی*\n"
    t += "━━━━━━━━━━━━━━\n\n"

    t += "📋 *مشاهده و آمار:*\n"
    t += "1️⃣ /پنل_کشورها — لیست کشورها\n"
    t += "2️⃣ /پنل_بازیکنان — لیست بازیکنان\n"
    t += "3️⃣ /پنل_اقتصاد — وضعیت اقتصادی\n"
    t += "4️⃣ /پنل_تجهیزات — وضعیت تجهیزات\n"
    t += "5️⃣ /لیست_اتحادها — اتحادهای فعال\n"
    t += "6️⃣ /لیست_گروهکها — گروهک‌های فعال\n"
    t += "7️⃣ /آمار — آمار کلی بازی\n"
    t += "8️⃣ /اطلاعات_کشور [ID] — پروفایل کامل\n"
    t += "9️⃣ /اطلاعات_بازیکن [uid] — اطلاعات بازیکن\n"
    t += "\n━━━━━━━━━━━━━━\n"

    t += "\n⚙️ *مدیریت کشور:*\n"
    t += "/افزودن_پول [ID] [مبلغ]\n"
    t += "/تنظیم_بودجه [ID] [مبلغ] — تنظیم مستقیم\n"
    t += "/افزودن_نفت [ID] [مقدار]\n"
    t += "/تنظیم_رضایت [ID] [درصد]\n"
    t += "/اعطای_تجهیز [ID] [eq_id] [تعداد]\n"
    t += "/اعطای_نیرو [ID] [troop_id] [تعداد]\n"
    t += "/حذف_تجهیز [ID] [eq_id] [تعداد]\n"
    t += "/اعطای_vip [ID] [نوع] [روز]\n"
    t += "/تحریم [ID] | /رفع_تحریم [ID]\n"
    t += "\n━━━━━━━━━━━━━━\n"

    t += "\n👥 *مدیریت بازیکنان:*\n"
    t += "/اخراج_بازیکن [uid]\n"
    t += "/ریست_روزانه [ID|0برای همه] — ریست daily\n"
    t += "/اعلام_همگانی [پیام] — پیام به همه\n"
    t += "\n━━━━━━━━━━━━━━\n"

    t += "\n⚔️ *مدیریت جنگ و گروهک:*\n"
    t += "/نتیجه_جنگ [att_id] [def_id] [attacker|defender]\n"
    t += "/پنل_گروهکها — مدیریت گروهک‌ها\n"
    t += "/نتیجه_عملیات [uid] [success|fail] [توضیح]\n"
    t += "/بودجه_گروهک [uid] [مبلغ]\n"
    t += "/انحلال_اتحاد [ID]\n"
    t += "\n━━━━━━━━━━━━━━\n"

    t += "\n💎 *VIP و سفارشات:*\n"
    t += "/پنل_vip — لیست VIP و سفارشات\n"
    t += "/سفارشات — سفارشات در انتظار\n"
    t += "/کد_تایید [ID] [کد|auto]\n"
    t += "\n━━━━━━━━━━━━━━\n"

    t += "\n🌊 *تنگه و محیط:*\n"
    t += "/تنگه [نام] [close|open]\n"
    t += "/تیک_روزانه — اجرای دستی\n"
    t += "\n━━━━━━━━━━━━━━\n"

    t += "\n💾 *بکاپ:*\n"
    t += "/بکاپ | /لیست_بکاپ\n"

    t += "\n━━━━━━━━━━━━━━\n"
    t += "\n🎮 *مدیریت بازی:*\n"
    t += "/وضعیت_بازی — وضعیت فعلی\n"
    t += "/رزروها — لیست رزروها\n"
    t += "/لغو_رزرو [نام] — لغو رزرو\n"
    t += "/شروع_بازی — شروع و تأیید رزروها\n"
    t += "/تایمر_بازی [ساعت] — تنظیم زمان پایان\n"
    if owner:
        t += "\n━━━━━━━━━━━━━━\n"
        t += "\n👑 *اختیارات اونر:*\n"
        t += "/پنل_ادمینها — مدیریت ادمین‌ها\n"
        t += "/افزودن_ادمین [uid] [نام]\n"
        t += "/حذف_ادمین [uid]\n"
        t += "/بازگردانی [ID] — رول‌بک دیتابیس\n"
        t += "/حذف_گروهک [uid] — انحلال گروهک\n"
        t += "/پایان_بازی — پایان رسمی بازی\n"
        t += "/ری_استارت — ری‌استارت کامل بازی\n"
        t += "/حذف_کشور [ID] — حذف کامل کشور\n"
    return t

def admin_panel_countries(uid):
    """پنل مدیریت کشورها"""
    if not is_admin(uid):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    rows = conn.execute(
        "SELECT id,flag,name,continent,money,oil,satisfaction,daily_oil,"
        "current_players,max_players,is_vip,is_sanctioned FROM countries ORDER BY id"
    ).fetchall()
    conn.close()
    t = "🏳 *لیست کشورها*\n"
    t += "━━━━━━━━━━━━━━\n\n"
    for c in rows:
        vip = " 👑" if c["is_vip"] else ""
        sanc = " 🚫" if c["is_sanctioned"] else ""
        oil_str = f" | 🛢{c['daily_oil']:,}" if c["daily_oil"] else ""
        t += (f"`[{c['id']}]` {c['flag']} *{c['name']}*{vip}{sanc}\n"
              f"   💰`{c['money']//1_000_000}M$` | 😊`{c['satisfaction']}%`"
              f"{oil_str} | 👤`{c['current_players']}/{c['max_players']}`\n\n")
    t += "━━━━━━━━━━━━━━\n"
    t += "📌 *دستورات:*\n"
    t += "/افزودن_کشور [نام] [پرچم] [قاره]\n"
    t += "/حذف_کشور [ID]\n"
    t += "/ویرایش_کشور [ID] [فیلد] [مقدار]\n"
    t += "/اطلاعات_کشور [ID] — پروفایل کامل\n"
    t += "/تحریم [ID] | /رفع_تحریم [ID]\n"
    return t

def admin_panel_players(uid):
    """پنل مدیریت بازیکنان"""
    if not is_admin(uid):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    rows = conn.execute(
        "SELECT p.user_id, p.username, c.flag, c.name as cname, p.last_daily "
        "FROM players p LEFT JOIN countries c ON p.country_id=c.id ORDER BY p.id"
    ).fetchall()
    conn.close()
    if not rows:
        return "❌ هیچ بازیکنی ثبت نشده."
    t = "👤 *لیست بازیکنان*\n"
    t += "━━━━━━━━━━━━━━\n\n"
    for p in rows:
        country = f"{p['flag']} {p['cname']}" if p["cname"] else "— بدون کشور"
        t += f"👤 *{p['username'] or 'بی‌نام'}*\n"
        t += f"   🆔 `{p['user_id']}`\n"
        t += f"   🌍 {country}\n\n"
    t += "━━━━━━━━━━━━━━\n"
    t += "📌 /اخراج_بازیکن [user_id] — حذف از کشور\n"
    t += "📌 /اطلاعات_بازیکن [user_id] — جزئیات\n"
    return t

def admin_country_full_info(uid, country_id):
    """اطلاعات کامل یک کشور برای ادمین"""
    if not is_admin(uid):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    c = conn.execute("SELECT * FROM countries WHERE id=?", (country_id,)).fetchone()
    if not c:
        conn.close()
        return "❌ کشور پیدا نشد."

    equips = conn.execute(
        "SELECT et.name,et.emoji,et.category,ce.amount FROM country_equipment ce "
        "JOIN equipment_types et ON ce.equipment_type_id=et.id "
        "WHERE ce.country_id=? AND ce.amount>0 ORDER BY et.category",
        (country_id,)
    ).fetchall()

    troops = conn.execute(
        "SELECT tt.name,tt.emoji,ct.amount FROM country_troops ct "
        "JOIN troop_types tt ON ct.troop_type_id=tt.id "
        "WHERE ct.country_id=? AND ct.amount>0", (country_id,)
    ).fetchall()

    buildings = conn.execute(
        "SELECT bt.name,bt.emoji,bt.effect_type,bt.effect_value,b.amount FROM buildings b "
        "JOIN building_types bt ON b.building_type_id=bt.id "
        "WHERE b.country_id=? AND b.amount>0", (country_id,)
    ).fetchall()

    players = conn.execute(
        "SELECT username,user_id FROM players WHERE country_id=?", (country_id,)
    ).fetchall()

    vip_info = conn.execute(
        "SELECT vip_type,expire_date FROM country_vip WHERE country_id=? AND is_active=1",
        (country_id,)
    ).fetchone()

    satellite = conn.execute(
        "SELECT level FROM satellites WHERE country_id=? AND is_active=1", (country_id,)
    ).fetchone()

    inventions = conn.execute(
        "SELECT name,invention_type,daily_production FROM inventions "
        "WHERE country_id=? AND is_active=1", (country_id,)
    ).fetchall()

    conn.close()

    # دسته‌بندی
    grouped = {}
    for e in equips:
        grouped.setdefault(e["category"], []).append(f"{e['emoji']}{e['name']}×{e['amount']}")

    daily_income = sum(b["effect_value"]*b["amount"] for b in buildings if b["effect_type"]=="money")

    t = f"🔍 *اطلاعات کامل: {c['flag']} {c['name']}* `[ID:{c['id']}]`\n"
    t += "━━━━━━━━━━━━━━\n\n"

    # بازیکنان
    t += "👥 *بازیکنان:*\n"
    for p in players:
        t += f"  • {p['username'] or 'بی‌نام'} | `{p['user_id']}`\n"
    if not players: t += "  〰 خالی\n"

    t += f"\n💸 بودجه: `{c['money']:,}$`\n"
    t += f"🛢 نفت: `{c['oil']:,}` | تولید: `{c['daily_oil']:,}/روز`\n"
    t += f"😊 رضایت: `{c['satisfaction']}%`\n"
    t += f"💰 درآمد روزانه: `{daily_income:,}$`\n"

    if vip_info:
        t += f"👑 VIP: {vip_info['vip_type']} | تا {vip_info['expire_date']}\n"
    if satellite:
        t += f"🛰 ماهواره: سطح {satellite['level']}\n"
    if c["is_sanctioned"]:
        t += f"🚫 تحریم: فعال ({c['sanction_days']} روز)\n"

    # تجهیزات
    cat_names = {
        "missile":"🚀موشک","fighter":"🛩جنگنده","bomber":"✈️بمب‌افکن",
        "navy":"🚢دریایی","bomb":"💣بمب","defense":"🛡پدافند",
        "ground":"🚛زمینی","launcher":"🎯پرتاب","transport":"🚙ترابری","base":"🏰پایگاه"
    }
    t += "\n🔫 *تجهیزات نظامی:*\n"
    has_equip = False
    for cat, items in grouped.items():
        lbl = cat_names.get(cat, cat)
        t += f"  {lbl}: {' | '.join(items)}\n"
        has_equip = True
    if not has_equip: t += "  〰 ندارد\n"

    t += "\n🪖 *نیروها:*\n"
    for tr in troops:
        t += f"  {tr['emoji']}{tr['name']}: `{tr['amount']:,}`\n"
    if not troops: t += "  〰 ندارد\n"

    t += "\n📈 *ساختمان‌ها:*\n"
    for b in buildings:
        t += f"  {b['emoji']}{b['name']}×{b['amount']}"
        if b["effect_type"]=="money": t += f" → `{b['effect_value']*b['amount']:,}$`"
        t += "\n"
    if not buildings: t += "  〰 ندارد\n"

    if inventions:
        t += "\n🧪 *اختراعات:*\n"
        for inv in inventions:
            t += f"  🔬{inv['name']}[{inv['invention_type']}]"
            if inv["daily_production"]: t += f" +`{inv['daily_production']:,}$`"
            t += "\n"

    t += "\n━━━━━━━━━━━━━━\n"
    t += f"📌 *دستورات برای این کشور:*\n"
    t += f"/افزودن_پول {c['id']} [مبلغ]\n"
    t += f"/اعطای_تجهیز {c['id']} [eq_id] [تعداد]\n"
    t += f"/اعطای_نیرو {c['id']} [troop_id] [تعداد]\n"
    t += f"/تنظیم_رضایت {c['id']} [درصد]\n"
    t += f"/تحریم {c['id']} | /رفع_تحریم {c['id']}\n"
    t += f"/اعطای_vip {c['id']} [نوع] [روز]\n"
    return t

def admin_panel_economy(uid):
    """پنل اقتصاد"""
    if not is_admin(uid):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    rows = conn.execute(
        "SELECT id,flag,name,money,oil,daily_oil,satisfaction FROM countries "
        "WHERE is_active=1 ORDER BY money DESC"
    ).fetchall()
    conn.close()
    t = "💰 *وضعیت اقتصادی کشورها*\n"
    t += "━━━━━━━━━━━━━━\n\n"
    for c in rows:
        t += f"`[{c['id']}]` {c['flag']} *{c['name']}*\n"
        t += f"   💸`{c['money']//1_000_000}M$` 🛢`{c['oil']:,}` ⛽`{c['daily_oil']:,}/روز` 😊`{c['satisfaction']}%`\n\n"
    t += "━━━━━━━━━━━━━━\n"
    t += "📌 *دستورات:*\n"
    t += "/افزودن_پول [ID] [مبلغ]\n"
    t += "/افزودن_همه [پول] [نفت] [رضایت] — به همه\n"
    t += "/تنظیم_روزانه [پول] [نفت] [رضایت]\n"
    t += "/تنظیم_رضایت [ID] [درصد]\n"
    t += "/تیک_روزانه — اجرای دستی\n"
    return t

def admin_panel_equip(uid):
    """پنل تجهیزات"""
    if not is_admin(uid):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    # top equipped countries
    rows = conn.execute(
        "SELECT c.id,c.flag,c.name, COUNT(ce.id) as types, SUM(ce.amount) as total "
        "FROM countries c LEFT JOIN country_equipment ce ON c.id=ce.country_id "
        "GROUP BY c.id ORDER BY total DESC NULLS LAST"
    ).fetchall()
    conn.close()
    t = "⚔️ *وضعیت تجهیزات کشورها*\n"
    t += "━━━━━━━━━━━━━━\n\n"
    for c in rows:
        total = c["total"] or 0
        types = c["types"] or 0
        t += f"`[{c['id']}]` {c['flag']} *{c['name']}*: `{total:,}` واحد ({types} نوع)\n"
    t += "\n━━━━━━━━━━━━━━\n"
    t += "📌 *دستورات:*\n"
    t += "/اطلاعات_کشور [ID] — تجهیزات کامل\n"
    t += "/اعطای_تجهیز [ID] [eq_id] [تعداد]\n"
    t += "/اعطای_نیرو [ID] [troop_id] [تعداد]\n"
    t += "/حذف_تجهیز [ID] [eq_id] [تعداد]\n"
    return t

def admin_panel_vip(uid):
    """پنل VIP"""
    if not is_admin(uid):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    orders = conn.execute(
        "SELECT id,user_id,country_name,item_name,order_type,price_toman,status,created_at "
        "FROM premium_orders ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    vips = conn.execute(
        "SELECT cv.*, c.name,c.flag FROM country_vip cv "
        "JOIN countries c ON cv.country_id=c.id WHERE cv.is_active=1"
    ).fetchall()
    conn.close()
    t = "💎 *پنل VIP و سفارشات*\n"
    t += "━━━━━━━━━━━━━━\n\n"
    t += "👑 *VIP های فعال:*\n"
    for v in vips:
        t += f"  {v['flag']} {v['name']}: {v['vip_type']} | تا {v['expire_date'] or 'نامحدود'}\n"
    if not vips: t += "  〰 ندارد\n"
    t += "\n📦 *سفارشات اخیر:*\n"
    for o in orders:
        status_em = "✅" if o["status"]=="confirmed" else ("⏳" if o["status"]=="pending" else "❌")
        t += f"{status_em} `[{o['id']}]` {o['item_name']}\n"
        t += f"   👤`{o['user_id']}` | {o['order_type']} | {o['price_toman']:,}تومان\n"
        t += f"   📅{o['created_at'][:10]}\n\n"
    t += "━━━━━━━━━━━━━━\n"
    t += "📌 /کد_تایید [ID_سفارش] [کد|auto]\n"
    t += "📌 /اعطای_vip [country_id] [نوع] [روز]\n"
    t += "📌 /لغو_سفارش [ID]\n"
    return t

def admin_panel_admins(uid):
    """پنل مدیریت ادمین‌ها — فقط اونر"""
    if not is_owner(uid):
        return "❌ فقط اونر."
    conn = get_conn()
    admins = conn.execute("SELECT * FROM admins ORDER BY is_owner DESC").fetchall()
    conn.close()
    t = "👮 *مدیریت ادمین‌ها*\n"
    t += "━━━━━━━━━━━━━━\n\n"
    for a in admins:
        em = "👑" if a["is_owner"] else "🛡"
        t += f"{em} *{a['name']}*\n   🆔 `{a['user_id']}`\n\n"
    t += "━━━━━━━━━━━━━━\n"
    t += "📌 /افزودن_ادمین [user_id] [نام]\n"
    t += "📌 /حذف_ادمین [user_id]\n"
    return t

def admin_give_troop(country_id, troop_id, amount, by):
    """اعطای نیرو به کشور"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    c = conn.execute("SELECT name FROM countries WHERE id=?", (country_id,)).fetchone()
    if not c:
        conn.close()
        return "❌ کشور پیدا نشد."
    conn.execute(
        "INSERT INTO country_troops (country_id,troop_type_id,amount) VALUES (?,?,?) "
        "ON CONFLICT(country_id,troop_type_id) DO UPDATE SET amount=amount+?",
        (country_id, troop_id, amount, amount)
    )
    conn.commit()
    conn.close()
    return f"✅ {amount:,} نیرو به کشور [{country_id}] اضافه شد."

def admin_set_satisfaction(country_id, value, by):
    """تنظیم رضایت مردمی"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    value = max(0, min(100, value))
    conn = get_conn()
    c = conn.execute("SELECT name FROM countries WHERE id=?", (country_id,)).fetchone()
    if not c:
        conn.close()
        return "❌ کشور پیدا نشد."
    conn.execute("UPDATE countries SET satisfaction=? WHERE id=?", (value, country_id))
    conn.commit()
    conn.close()
    return f"✅ رضایت کشور [{country_id}] به `{value}%` تنظیم شد."

def admin_give_vip(country_id, vip_type, days, by):
    """اعطای VIP به کشور"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    import datetime
    expire = (datetime.date.today() + datetime.timedelta(days=days)).isoformat() if days > 0 else None
    conn = get_conn()
    c = conn.execute("SELECT name,flag FROM countries WHERE id=?", (country_id,)).fetchone()
    if not c:
        conn.close()
        return "❌ کشور پیدا نشد."
    conn.execute("UPDATE countries SET is_vip=1 WHERE id=?", (country_id,))
    conn.execute(
        "INSERT INTO country_vip (country_id,vip_type,expire_date,is_active) VALUES (?,?,?,1) "
        "ON CONFLICT(country_id) DO UPDATE SET vip_type=?,expire_date=?,is_active=1",
        (country_id, vip_type, expire, vip_type, expire)
    )
    conn.commit()
    conn.close()
    return (f"✅ VIP *{vip_type}* به کشور {c['flag']} {c['name']} اعطا شد.\n"
            f"📅 انقضا: {expire or 'نامحدود'}")

def admin_remove_equip(country_id, eq_id, amount, by):
    """حذف تجهیز از کشور"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    conn.execute(
        "UPDATE country_equipment SET amount=MAX(0,amount-?) "
        "WHERE country_id=? AND equipment_type_id=?",
        (amount, country_id, eq_id)
    )
    conn.commit()
    conn.close()
    return f"✅ {amount} واحد تجهیز [{eq_id}] از کشور [{country_id}] حذف شد."

def admin_kick_player(target_uid, by):
    """اخراج بازیکن از کشور"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    p = conn.execute("SELECT country_id,username FROM players WHERE user_id=?", (str(target_uid),)).fetchone()
    if not p or not p["country_id"]:
        conn.close()
        return "❌ بازیکن یا کشور پیدا نشد."
    conn.execute(
        "UPDATE countries SET current_players=MAX(0,current_players-1) WHERE id=?",
        (p["country_id"],)
    )
    conn.execute("UPDATE players SET country_id=NULL WHERE user_id=?", (str(target_uid),))
    conn.commit()
    conn.close()
    return f"✅ بازیکن {p['username'] or target_uid} از کشور اخراج شد."

def admin_player_info(target_uid, by):
    """اطلاعات یک بازیکن"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    p = conn.execute(
        "SELECT p.*,c.name as cname,c.flag FROM players p "
        "LEFT JOIN countries c ON p.country_id=c.id WHERE p.user_id=?",
        (str(target_uid),)
    ).fetchone()
    if not p:
        conn.close()
        return "❌ بازیکن پیدا نشد."
    orders = conn.execute(
        "SELECT item_name,order_type,status,created_at FROM premium_orders "
        "WHERE user_id=? ORDER BY created_at DESC LIMIT 5",
        (str(target_uid),)
    ).fetchall()
    g = conn.execute("SELECT group_name,group_type,budget FROM groups WHERE user_id=?", (str(target_uid),)).fetchone()
    conn.close()

    t = f"👤 *اطلاعات بازیکن: {p['username'] or 'بی‌نام'}*\n"
    t += "━━━━━━━━━━━━━━\n"
    t += f"🆔 `{p['user_id']}`\n"
    country = f"{p['flag']} {p['cname']}" if p["cname"] else "— بدون کشور"
    t += f"🌍 کشور: {country}\n"
    t += f"📅 آخرین daily: {p['last_daily'] or 'هرگز'}\n"
    if g:
        t += f"☠ گروهک: {g['group_name']} [{g['group_type']}] | بودجه: `{g['budget']:,}$`\n"
    if orders:
        t += "\n💎 *سفارشات:*\n"
        for o in orders:
            em = "✅" if o["status"]=="confirmed" else "⏳"
            t += f"  {em} {o['item_name']} | {o['created_at'][:10]}\n"
    return t

# ═══════════════════════════════════════════════════════
#  قابلیت‌های ادمین — بخش دوم
# ═══════════════════════════════════════════════════════

def admin_broadcast(message, by):
    """ارسال پیام همگانی به همه بازیکنان"""
    if not is_admin(by):
        return "❌ دسترسی ندارید.", []
    conn = get_conn()
    players = conn.execute("SELECT user_id FROM players").fetchall()
    conn.close()
    uids = [p["user_id"] for p in players]
    return f"📢 پیام برای ارسال به {len(uids)} بازیکن آماده شد.", uids

def admin_reset_daily(country_id, by):
    """ریست کردن daily تمام بازیکنان یک کشور"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    if country_id == 0:
        conn.execute("UPDATE players SET last_daily=NULL")
        msg = "✅ daily همه بازیکنان ریست شد."
    else:
        c = conn.execute("SELECT name FROM countries WHERE id=?", (country_id,)).fetchone()
        if not c:
            conn.close()
            return "❌ کشور پیدا نشد."
        conn.execute("UPDATE players SET last_daily=NULL WHERE country_id=?", (country_id,))
        msg = f"✅ daily بازیکنان کشور [{country_id}] ریست شد."
    conn.commit()
    conn.close()
    return msg

def admin_add_oil(country_id, amount, by):
    """افزودن نفت به کشور"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    c = conn.execute("SELECT name,flag FROM countries WHERE id=?", (country_id,)).fetchone()
    if not c:
        conn.close()
        return "❌ کشور پیدا نشد."
    conn.execute("UPDATE countries SET oil=oil+? WHERE id=?", (amount, country_id))
    conn.commit()
    conn.close()
    return f"✅ {amount:,} بشکه نفت به {c['flag']} {c['name']} اضافه شد."

def admin_set_money(country_id, amount, by):
    """تنظیم مستقیم بودجه کشور"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    c = conn.execute("SELECT name,flag FROM countries WHERE id=?", (country_id,)).fetchone()
    if not c:
        conn.close()
        return "❌ کشور پیدا نشد."
    conn.execute("UPDATE countries SET money=? WHERE id=?", (amount, country_id))
    conn.commit()
    conn.close()
    return f"✅ بودجه {c['flag']} {c['name']} به `{amount:,}$` تنظیم شد."

def admin_war_result(attacker_id, defender_id, winner, by):
    """ثبت نتیجه جنگ توسط ادمین"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    att = conn.execute("SELECT name,flag FROM countries WHERE id=?", (attacker_id,)).fetchone()
    dfn = conn.execute("SELECT name,flag FROM countries WHERE id=?", (defender_id,)).fetchone()
    if not att or not dfn:
        conn.close()
        return "❌ یکی از کشورها پیدا نشد."
    conn.close()
    if winner == "attacker":
        return (f"⚔️ *نتیجه جنگ ثبت شد:*\n\n"
                f"🏆 برنده: {att['flag']} {att['name']}\n"
                f"💥 بازنده: {dfn['flag']} {dfn['name']}\n\n"
                f"⚠️ برای اعمال خسارت از /اعطای_تجهیز و /افزودن_پول استفاده کنید.")
    else:
        return (f"⚔️ *نتیجه جنگ ثبت شد:*\n\n"
                f"🛡 برنده: {dfn['flag']} {dfn['name']}\n"
                f"💥 بازنده: {att['flag']} {att['name']}\n\n"
                f"⚠️ برای اعمال خسارت از /اعطای_تجهیز و /افزودن_پول استفاده کنید.")

def admin_alliance_info_all(by):
    """لیست همه اتحادها"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    alliances = conn.execute("SELECT * FROM alliances").fetchall()
    if not alliances:
        conn.close()
        return "❌ هیچ اتحادی وجود ندارد."
    t = "🤝 *لیست اتحادها:*\n━━━━━━━━━━━━━━\n\n"
    for a in alliances:
        members = conn.execute(
            "SELECT c.name,c.flag FROM alliance_members am "
            "JOIN countries c ON am.country_id=c.id WHERE am.alliance_id=?", (a["id"],)
        ).fetchall()
        t += f"🤝 *{a['name']}* `[ID:{a['id']}]`\n"
        for m in members:
            t += f"  {m['flag']} {m['name']}\n"
        t += "\n"
    conn.close()
    return t

def admin_disband_alliance(alliance_id, by):
    """انحلال اتحاد"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    a = conn.execute("SELECT name FROM alliances WHERE id=?", (alliance_id,)).fetchone()
    if not a:
        conn.close()
        return "❌ اتحاد پیدا نشد."
    conn.execute("DELETE FROM alliance_members WHERE alliance_id=?", (alliance_id,))
    conn.execute("DELETE FROM alliances WHERE id=?", (alliance_id,))
    conn.commit()
    conn.close()
    return f"✅ اتحاد *{a['name']}* منحل شد."

def admin_group_info_all(by):
    """لیست همه گروهک‌های فعال"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    groups = conn.execute(
        "SELECT g.*, p.username FROM groups g "
        "LEFT JOIN players p ON g.user_id=p.user_id ORDER BY g.budget DESC"
    ).fetchall()
    conn.close()
    if not groups:
        return "❌ هیچ گروهکی ثبت نشده."
    t = "☠ *لیست گروهک‌های فعال:*\n━━━━━━━━━━━━━━\n\n"
    for g in groups:
        em = "💻" if g["group_type"] == "hack" else "☠"
        t += (f"{em} *{g['group_name']}*\n"
              f"   👤 {g['username'] or g['user_id']}\n"
              f"   💸 `{g['budget']:,}$` | 📍 {g['host_country'] or '—'}\n"
              f"   👥 {g['troops']:,} نفر | ⚡ {g['op_power']}/100\n\n")
    return t

def admin_set_group_budget(user_id_target, amount, by):
    """تنظیم بودجه گروهک"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    g = conn.execute("SELECT group_name FROM groups WHERE user_id=?", (str(user_id_target),)).fetchone()
    if not g:
        conn.close()
        return "❌ گروهک پیدا نشد."
    conn.execute("UPDATE groups SET budget=? WHERE user_id=?", (amount, str(user_id_target)))
    conn.commit()
    conn.close()
    return f"✅ بودجه گروهک *{g['group_name']}* به `{amount:,}$` تنظیم شد."

def admin_op_result(group_uid, success, note, by):
    """اعلام نتیجه عملیات گروهک"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    g = conn.execute("SELECT group_name,group_type FROM groups WHERE user_id=?", (str(group_uid),)).fetchone()
    if not g:
        conn.close()
        return "❌ گروهک پیدا نشد."
    conn.close()
    em = "✅" if success else "❌"
    status = "موفق" if success else "ناموفق"
    t = f"{em} *نتیجه عملیات گروهک {g['group_name']}:*\n\n"
    t += f"📋 وضعیت: {status}\n"
    if note:
        t += f"📝 توضیح: {note}\n"
    t += "\n⚠️ برای اعمال تغییرات از دستورات مربوطه استفاده کنید."
    return t

def admin_stats(by):
    """آمار کلی بازی"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    total_countries = conn.execute("SELECT COUNT(*) as n FROM countries WHERE is_active=1").fetchone()["n"]
    active_countries = conn.execute("SELECT COUNT(*) as n FROM countries WHERE current_players>0").fetchone()["n"]
    total_players = conn.execute("SELECT COUNT(*) as n FROM players").fetchone()["n"]
    players_with_country = conn.execute("SELECT COUNT(*) as n FROM players WHERE country_id IS NOT NULL").fetchone()["n"]
    total_groups = conn.execute("SELECT COUNT(*) as n FROM groups").fetchone()["n"]
    total_alliances = conn.execute("SELECT COUNT(*) as n FROM alliances").fetchone()["n"]
    pending_orders = conn.execute("SELECT COUNT(*) as n FROM premium_orders WHERE status='pending'").fetchone()["n"]
    total_money = conn.execute("SELECT SUM(money) as s FROM countries").fetchone()["s"] or 0
    total_oil = conn.execute("SELECT SUM(oil) as s FROM countries").fetchone()["s"] or 0
    vips = conn.execute("SELECT COUNT(*) as n FROM country_vip WHERE is_active=1").fetchone()["n"]
    conn.close()

    t = "📊 *آمار کلی بازی*\n━━━━━━━━━━━━━━\n\n"
    t += f"🌍 کشورها: `{active_countries}/{total_countries}` فعال\n"
    t += f"👤 بازیکنان: `{players_with_country}/{total_players}` داخل بازی\n"
    t += f"☠ گروهک‌ها: `{total_groups}` ثبت‌شده\n"
    t += f"🤝 اتحادها: `{total_alliances}` فعال\n"
    t += f"👑 VIP: `{vips}` کشور\n"
    t += f"⏳ سفارشات در انتظار: `{pending_orders}`\n\n"
    t += f"💸 کل پول بازی: `{total_money//1_000_000_000}B$`\n"
    t += f"🛢 کل نفت: `{total_oil:,}` بشکه\n"
    return t

def admin_panel_groups(by):
    """پنل مدیریت گروهک‌ها"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    t = "☠ *پنل مدیریت گروهک‌ها*\n━━━━━━━━━━━━━━\n\n"
    t += "📋 *دستورات:*\n\n"
    t += "👁 /لیست_گروهکها — همه گروهک‌های فعال\n"
    t += "💰 /بودجه_گروهک [user_id] [مبلغ] — تنظیم بودجه\n"
    t += "✅ /نتیجه_عملیات [user_id] [success|fail] [توضیح]\n"
    t += "🚫 /حذف_گروهک [user_id] — انحلال گروهک\n\n"
    t += "━━━━━━━━━━━━━━\n"
    t += "⚠️ نتیجه همه عملیات‌ها باید توسط ادمین اعلام شود."
    return t

def admin_delete_group(target_uid, by):
    """انحلال گروهک"""
    if not is_owner(by):
        return "❌ فقط اونر."
    conn = get_conn()
    g = conn.execute("SELECT group_name FROM groups WHERE user_id=?", (str(target_uid),)).fetchone()
    if not g:
        conn.close()
        return "❌ گروهک پیدا نشد."
    conn.execute("DELETE FROM groups WHERE user_id=?", (str(target_uid),))
    conn.commit()
    conn.close()
    return f"✅ گروهک *{g['group_name']}* منحل شد."

# ═══════════════════════════════════════════════════════
#  سیستم رزرو، شروع و مدیریت بازی
# ═══════════════════════════════════════════════════════

def get_game_status():
    conn = get_conn()
    r = conn.execute("SELECT * FROM game_state WHERE id=1").fetchone()
    conn.close()
    return dict(r) if r else {"status": "waiting", "game_round": 0}

def set_game_status(status):
    conn = get_conn()
    import datetime
    now = datetime.datetime.now().isoformat()
    if status == "running":
        conn.execute("UPDATE game_state SET status=?, start_time=? WHERE id=1", (status, now))
    elif status == "ended":
        conn.execute("UPDATE game_state SET status=?, end_time=? WHERE id=1", (status, now))
    else:
        conn.execute("UPDATE game_state SET status=? WHERE id=1", (status,))
    conn.commit()
    conn.close()

def cmd_reserve(uid, username, target_name):
    """رزرو کشور یا گروهک قبل از شروع بازی"""
    gs = get_game_status()
    if gs["status"] != "waiting":
        return None, "❌ بازی در حال اجراست. دیگر نمی‌توان رزرو کرد."

    conn = get_conn()

    # چک کردن رزرو قبلی
    existing = conn.execute("SELECT target_name FROM reservations WHERE user_id=?", (str(uid),)).fetchone()
    if existing:
        conn.close()
        return None, f"❌ شما قبلاً *{existing['target_name']}* رو رزرو کردید."

    # پیدا کردن هدف
    all_countries = conn.execute("SELECT name,flag,continent FROM countries WHERE is_active=1").fetchall()
    all_groups = TERROR_GROUPS + HACKER_GROUPS

    # جستجو در کشورها
    found_country = None
    for c in all_countries:
        if c["name"].strip() == target_name.strip() or target_name.strip() in c["name"]:
            found_country = c
            break

    # جستجو در گروهک‌ها
    found_group = None
    if not found_country:
        for g in all_groups:
            if g.strip() == target_name.strip():
                found_group = g
                break

    if not found_country and not found_group:
        conn.close()
        return None, f"❌ *{target_name}* پیدا نشد.\n/کشور — لیست کشورها\n/گروهکها — لیست گروهک‌ها"

    # چک تکراری بودن رزرو
    already = conn.execute(
        "SELECT username FROM reservations WHERE target_name=? AND status IN ('pending','confirmed')",
        (target_name,)
    ).fetchone()
    if already:
        conn.close()
        return None, f"❌ *{target_name}* قبلاً توسط {already['username'] or 'کسی'} رزرو شده."

    target_type = "country" if found_country else "group"
    conn.execute(
        "INSERT INTO reservations (user_id, username, target_name, target_type) VALUES (?,?,?,?)",
        (str(uid), username, target_name, target_type)
    )
    conn.commit()
    conn.close()

    if found_country:
        msg = (f"✅ *رزرو موفق!*\n\n"
               f"{found_country['flag']} *{found_country['name']}*\n"
               f"🗺 قاره: {found_country['continent']}\n\n"
               f"⏳ منتظر شروع بازی باشید.")
        channel_msg = (f"🎯 *رزرو جدید!*\n\n"
                       f"{found_country['flag']} کشور *{found_country['name']}*\n"
                       f"توسط 👤 *{username}* رزرو شد.\n\n"
                       f"🗺 قاره: {found_country['continent']}")
    else:
        gtype = "💻 هکری" if found_group in HACKER_GROUPS else "☠ تروریستی"
        msg = (f"✅ *رزرو موفق!*\n\n"
               f"☠ گروهک *{found_group}* [{gtype}]\n\n"
               f"⏳ منتظر شروع بازی باشید.")
        channel_msg = (f"🎯 *رزرو جدید!*\n\n"
                       f"☠ گروهک *{found_group}* [{gtype}]\n"
                       f"توسط 👤 *{username}* رزرو شد.")

    return channel_msg, msg

def cmd_reservations_list():
    """لیست رزروها"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM reservations WHERE status IN ('pending','confirmed') ORDER BY created_at"
    ).fetchall()
    conn.close()

    if not rows:
        return "📋 هنوز رزروی ثبت نشده."

    countries = [r for r in rows if r["target_type"] == "country"]
    groups = [r for r in rows if r["target_type"] == "group"]

    t = f"📋 *لیست رزروها* ({len(rows)} نفر)\n━━━━━━━━━━━━━━\n\n"

    if countries:
        t += "🌍 *کشورها:*\n"
        for r in countries:
            em = "✅" if r["status"] == "confirmed" else "⏳"
            t += f"  {em} *{r['target_name']}* — 👤 {r['username'] or r['user_id']}\n"

    if groups:
        t += "\n☠ *گروهک‌ها:*\n"
        for r in groups:
            em = "✅" if r["status"] == "confirmed" else "⏳"
            t += f"  {em} *{r['target_name']}* — 👤 {r['username'] or r['user_id']}\n"

    return t

def admin_cancel_reserve(target_name, by):
    """لغو رزرو توسط ادمین"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    conn = get_conn()
    r = conn.execute("SELECT * FROM reservations WHERE target_name=?", (target_name,)).fetchone()
    if not r:
        conn.close()
        return f"❌ رزروی برای *{target_name}* پیدا نشد."
    conn.execute("DELETE FROM reservations WHERE target_name=?", (target_name,))
    conn.commit()
    conn.close()
    return f"✅ رزرو *{target_name}* لغو شد."

def admin_start_game(by):
    """شروع بازی — تأیید رزروها و پر کردن کشورها"""
    if not is_admin(by):
        return "❌ دسترسی ندارید.", []

    gs = get_game_status()
    if gs["status"] == "running":
        return "❌ بازی در حال اجراست.", []

    conn = get_conn()
    reservations = conn.execute(
        "SELECT * FROM reservations WHERE status='pending' ORDER BY created_at"
    ).fetchall()

    if not reservations:
        conn.close()
        return "❌ هیچ رزروی ثبت نشده.", []

    channel_messages = []
    activated = 0

    for r in reservations:
        try:
            if r["target_type"] == "country":
                # پیدا کردن کشور
                country = conn.execute(
                    "SELECT * FROM countries WHERE name=?", (r["target_name"],)
                ).fetchone()
                if not country:
                    continue

                # ثبت بازیکن
                conn.execute(
                    "INSERT OR IGNORE INTO players (user_id, username, country_id) VALUES (?,?,?)",
                    (r["user_id"], r["username"], country["id"])
                )
                conn.execute(
                    "UPDATE players SET country_id=?, username=? WHERE user_id=?",
                    (country["id"], r["username"], r["user_id"])
                )
                conn.execute(
                    "UPDATE countries SET current_players=current_players+1 WHERE id=?",
                    (country["id"],)
                )
                conn.execute(
                    "UPDATE reservations SET status='confirmed' WHERE id=?", (r["id"],)
                )

                channel_messages.append(
                    f"✅ *{country['flag']} {country['name']}*\n"
                    f"   👤 {r['username'] or r['user_id']} وارد بازی شد!\n"
                    f"   💰 بودجه: `{country['money']//1_000_000_000}B$`"
                    + (f" | 🛢 `{country['daily_oil']:,}` بشکه/روز" if country["daily_oil"] else "")
                )

            elif r["target_type"] == "group":
                # ثبت گروهک
                all_groups = TERROR_GROUPS + HACKER_GROUPS
                if r["target_name"] not in all_groups:
                    continue
                gtype = "hack" if r["target_name"] in HACKER_GROUPS else "terror"
                budget = 2_000_000_000 if gtype == "hack" else 3_000_000_000

                conn.execute(
                    "INSERT OR IGNORE INTO players (user_id, username) VALUES (?,?)",
                    (r["user_id"], r["username"])
                )
                conn.execute(
                    "INSERT OR IGNORE INTO groups (user_id, group_name, group_type, budget) VALUES (?,?,?,?)",
                    (r["user_id"], r["target_name"], gtype, budget)
                )
                conn.execute(
                    "UPDATE reservations SET status='confirmed' WHERE id=?", (r["id"],)
                )

                em = "💻" if gtype == "hack" else "☠"
                channel_messages.append(
                    f"{em} گروهک *{r['target_name']}*\n"
                    f"   👤 {r['username'] or r['user_id']} وارد بازی شد!\n"
                    f"   💰 بودجه: `{budget//1_000_000_000}B$`"
                )
            activated += 1
        except Exception as e:
            print(f"⚠️ خطا در شروع برای {r['target_name']}: {e}")

    set_game_status("running")
    conn.commit()
    conn.close()

    summary = (f"🚀 *بازی جنگ جهانی شروع شد!*\n\n"
               f"✅ {activated} بازیکن وارد شدند\n"
               f"━━━━━━━━━━━━━━\n"
               f"⚔️ موفق باشید!")

    return summary, channel_messages

def admin_end_game(by):
    """پایان بازی"""
    if not is_owner(by):
        return "❌ فقط اونر.", None

    gs = get_game_status()
    if gs["status"] != "running":
        return "❌ بازی در حال اجرا نیست.", None

    set_game_status("ended")

    conn = get_conn()
    # رتبه‌بندی نهایی
    rows = conn.execute(
        "SELECT name,flag,money,oil,satisfaction FROM countries "
        "WHERE current_players>0 ORDER BY money DESC LIMIT 10"
    ).fetchall()
    conn.close()

    t = "🏁 *بازی جنگ جهانی پایان یافت!*\n━━━━━━━━━━━━━━\n\n"
    t += "🏆 *رتبه‌بندی نهایی:*\n\n"
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    for i, c in enumerate(rows):
        t += f"{medals[i]} {c['flag']} *{c['name']}*\n"
        t += f"   💰 `{c['money']//1_000_000_000}B$` | 😊 `{c['satisfaction']}%`\n\n"

    channel_msg = t + "\nممنون از همه بازیکنان! 🎮"
    return "✅ بازی پایان یافت. پیام به کانال ارسال شد.", channel_msg

def admin_restart_game(by):
    """ری‌استارت بازی — ریست کامل"""
    if not is_owner(by):
        return "❌ فقط اونر."

    conn = get_conn()
    # ریست کشورها
    conn.execute("UPDATE countries SET money=5000000000, oil=daily_oil, satisfaction=100, current_players=0, is_sanctioned=0, sanction_days=0")
    # ریست بازیکنان
    conn.execute("UPDATE players SET country_id=NULL, last_daily=NULL")
    # ریست تجهیزات
    conn.execute("DELETE FROM country_equipment")
    conn.execute("DELETE FROM country_troops")
    conn.execute("DELETE FROM buildings")
    conn.execute("DELETE FROM country_tankers")
    conn.execute("DELETE FROM country_vip")
    conn.execute("DELETE FROM satellites")
    conn.execute("DELETE FROM inventions")
    conn.execute("DELETE FROM groups")
    conn.execute("DELETE FROM alliances")
    conn.execute("DELETE FROM alliance_members")
    conn.execute("DELETE FROM reservations")
    conn.execute("DELETE FROM premium_orders")
    # ریست وضعیت
    conn.execute("UPDATE game_state SET status='waiting', start_time=NULL, end_time=NULL, game_round=0")
    conn.commit()
    conn.close()

    return ("✅ *بازی ری‌استارت شد!*\n\n"
            "🔄 همه داده‌ها ریست شدند.\n"
            "📋 رزروها پاک شدند.\n"
            "⏳ بازیکنان می‌توانند دوباره رزرو کنند.")

def admin_set_game_timer(hours, by):
    """تنظیم تایمر پایان بازی"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    import datetime
    end_time = (datetime.datetime.now() + datetime.timedelta(hours=hours)).isoformat()
    conn = get_conn()
    conn.execute("UPDATE game_state SET end_time=? WHERE id=1", (end_time,))
    conn.commit()
    conn.close()
    return (f"⏱ *تایمر بازی تنظیم شد!*\n\n"
            f"⏰ پایان بازی: `{end_time[:16]}`\n"
            f"⏳ مدت: {hours} ساعت")

# ═══════════════════════════════════════════════════════
#  هوش مصنوعی — دستیار بازی
# ═══════════════════════════════════════════════════════

GAME_CONTEXT = """تو دستیار هوشمند ربات بازی «جنگ جهانی» روبیکا هستی.

اطلاعات بازی:
- هر بازیکن یک کشور یا گروهک انتخاب می‌کنه
- کشورها می‌تونن تجهیزات نظامی بخرن، نفت تولید کنن، اتحاد بسازن
- گروهک‌ها (تروریستی/هکری) می‌تونن عملیات انجام بدن
- هر کشور بودجه، نفت، رضایت مردمی داره
- تجهیزات: موشک، جنگنده، بمب‌افکن، ناوگان، پدافند، زمینی
- قوانین: 3 روز اول جنگ ممنوع، هر کشور max 10 بازیکن
- VIP کشورها: آمریکا، ایران، ترکیه، مصر، عربستان، قطر، بریتانیا، اسپانیا
- VIP گروهک‌ها: انانیموس، دارک وب، دزدان دریایی، واگنر، ساواک، داعش

دستورات مهم:
/کشور - انتخاب کشور
/پروفایل - پروفایل کشور
/فروشگاه - خرید تجهیزات
/روزانه - پاداش روزانه
/رزرو [نام] - رزرو کشور/گروهک
/اقتصاد - وضعیت اقتصادی
/ارتش - تجهیزات نظامی

جواب‌هات باید:
- کوتاه و واضح باشه (max 3-4 جمله)
- فارسی باشه
- مرتبط با بازی باشه
- اگه سوال ربطی به بازی نداره، بگو «فقط سوالات مرتبط با بازی جنگ جهانی رو می‌تونم جواب بدم»
"""

# شمارنده استفاده از کلیدها
_gemini_usage = {}        # {key_index: daily_count}
_gemini_minute = {}       # {key_index: [timestamps]}
_gemini_date = None
_gemini_rpm_limit = 15    # هر کلید max 15 درخواست در دقیقه

def _get_active_gemini_key():
    """پیدا کردن کلید فعال — چک روزانه و دقیقه‌ای"""
    global _gemini_date, _gemini_usage, _gemini_minute
    import datetime, time
    from config import GEMINI_API_KEYS, GEMINI_DAILY_LIMIT

    today = datetime.date.today().isoformat()
    if _gemini_date != today:
        _gemini_date = today
        _gemini_usage = {}
        _gemini_minute = {}

    keys = [k for k in GEMINI_API_KEYS if k and not k.startswith("YOUR_")]
    if not keys:
        return None, -1

    per_key_daily = GEMINI_DAILY_LIMIT // len(keys)
    now = time.time()

    for i, key in enumerate(keys):
        # چک محدودیت روزانه
        if _gemini_usage.get(i, 0) >= per_key_daily:
            continue

        # چک محدودیت دقیقه‌ای — پاک کردن timestamps قدیمی
        recent = [t for t in _gemini_minute.get(i, []) if now - t < 60]
        _gemini_minute[i] = recent

        if len(recent) < _gemini_rpm_limit:
            return key, i

    return None, -1

def ask_claude(question, user_context=""):
    """ارسال سوال به Gemini - با پروکسی داخلی برای دور زدن فیلتر"""
    import json, time
    from config import GEMINI_API_KEYS, GEMINI_PROXY

    key, key_idx = _get_active_gemini_key()
    if not key:
        return "⚠️ ظرفیت دستیار هوشمند برای امروز پر شده. فردا دوباره تلاش کن."

    context_msg = f"\nاطلاعات بازیکن: {user_context}" if user_context else ""
    full_prompt = GAME_CONTEXT + context_msg + "\n\nسوال بازیکن: " + question

    payload = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {"maxOutputTokens": 300, "temperature": 0.7}
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"

    # پروکسی برای دور زدن فیلتر (اختیاری)
    proxies = None
    if GEMINI_PROXY:
        proxies = {"http": GEMINI_PROXY, "https": GEMINI_PROXY}

    try:
        import requests as req_lib
        resp = req_lib.post(
            url,
            json=payload,
            timeout=20,
            headers={"Content-Type": "application/json"},
            proxies=proxies
        )
        resp.raise_for_status()
        result = resp.json()
        answer = result["candidates"][0]["content"]["parts"][0]["text"]
        _gemini_usage[key_idx] = _gemini_usage.get(key_idx, 0) + 1
        _gemini_minute.setdefault(key_idx, []).append(time.time())
        print(f"🤖 Gemini key[{key_idx+1}] daily:{_gemini_usage[key_idx]}")
        return answer

    except Exception as e:
        err = str(e)
        if "429" in err:
            _gemini_minute.setdefault(key_idx, [])
            _gemini_minute[key_idx] = [time.time()] * _gemini_rpm_limit
            print(f"⚠️ Gemini key[{key_idx+1}] rate limited, switching...")
            return ask_claude(question, user_context)
        print(f"⚠️ Gemini error: {e}")
        return "❌ هوش مصنوعی در دسترس نیست.\nفیلترشکن روی گوشی روشن نیست یا سرور خطا داره."

def cmd_ai_help(uid, question):
    """دستیار هوشمند بازی"""
    if not question.strip():
        return ("🤖 *دستیار هوشمند بازی*\n\n"
                "هر سوالی درباره بازی داری بپرس!\n\n"
                "مثال‌ها:\n"
                "• چطور نفت بخرم؟\n"
                "• بهترین تجهیزات برای حمله چیه؟\n"
                "• چطور اتحاد بسازم؟\n"
                "• قوانین جنگ چیه؟\n"
                "• VIP چه مزایایی داره؟\n\n"
                "📌 بفرست: /ai [سوالت]")

    # اطلاعات بازیکن برای context بهتر
    c = _get_player_country(uid)
    user_ctx = ""
    if c:
        user_ctx = f"کشور بازیکن: {c['name']} | بودجه: {c['money']:,}$ | نفت: {c['oil']:,}"

    answer = ask_claude(question, user_ctx)
    return f"🤖 *دستیار هوشمند:*\n\n{answer}"

def admin_ai_stats(by):
    """آمار استفاده از هوش مصنوعی"""
    if not is_admin(by):
        return "❌ دسترسی ندارید."
    import time
    from config import GEMINI_API_KEYS, GEMINI_DAILY_LIMIT
    keys = [k for k in GEMINI_API_KEYS if k and not k.startswith("YOUR_")]
    per_key = GEMINI_DAILY_LIMIT // len(keys) if keys else 0
    total_used = sum(_gemini_usage.values())
    now = time.time()

    t = "🤖 *آمار هوش مصنوعی امروز*\n━━━━━━━━━━━━━━\n\n"
    for i, key in enumerate(keys):
        daily = _gemini_usage.get(i, 0)
        recent_rpm = len([ts for ts in _gemini_minute.get(i, []) if now - ts < 60])
        bar_len = (daily * 10 // per_key) if per_key else 0
        bar = "█" * bar_len + "░" * (10 - bar_len)
        status = "✅" if daily < per_key and recent_rpm < _gemini_rpm_limit else "🔴"
        t += f"{status} *کلید {i+1}:*\n"
        t += f"   روزانه: `{daily}/{per_key}` {bar}\n"
        t += f"   این دقیقه: `{recent_rpm}/{_gemini_rpm_limit}`\n\n"

    t += f"━━━━━━━━━━━━━━\n"
    t += f"📊 کل امروز: `{total_used}/{GEMINI_DAILY_LIMIT}`\n"
    t += f"⚡ ظرفیت دقیقه: `{len(keys) * _gemini_rpm_limit}` پیام/دقیقه\n"
    t += f"⏳ باقیمانده: `{GEMINI_DAILY_LIMIT - total_used}` پیام"
    return t
