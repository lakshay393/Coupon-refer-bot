import json
import random
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler

TOKEN = "8287264174:AAHNcBvqk4xTrF8ppG_4Kv4of609hj30Ivo"
ADMIN_ID = 7515220054
BOT_USERNAME = "SheinReferEarn_bot"
SUPPORT_ID = "@ZEXUS_HERE"

USERS_FILE = "users.json"
CHANNELS_FILE = "channels.txt"
CODES500_FILE = "codes500.txt"
CODES1000_FILE = "codes1000.txt"


# ---------- FILE ---------- #

def load_json(file):
    try:
        return json.load(open(file))
    except:
        return {}

def save_json(file, data):
    json.dump(data, open(file, "w"), indent=4)

users = load_json(USERS_FILE)


def load_channels():
    try:
        return [x.strip() for x in open(CHANNELS_FILE).read().splitlines() if x.strip()]
    except:
        return []


# ---------- FORCE JOIN ---------- #

def check_force(uid, bot):
    channels = load_channels()
    if not channels:
        return True

    for ch in channels:
        try:
            m = bot.get_chat_member(ch, uid)
            if m.status in ["left", "kicked"]:
                return False
        except:
            return False
    return True


# ---------- START ---------- #

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    uid = str(user.id)
    ref = context.args[0] if context.args else None

    if not check_force(uid, context.bot):
        btn = []
        for ch in load_channels():
            btn.append([InlineKeyboardButton("Join Channel", url=f"https://t.me/{ch.replace('@','')}")])

        btn.append([InlineKeyboardButton("I Joined", callback_data="joined")])

        update.message.reply_text(
            "Please join all channels first!",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return

    if uid not in users:
        users[uid] = {"points": 0, "refers": 0, "history": []}
        save_json(USERS_FILE, users)

        context.bot.send_message(
            ADMIN_ID,
            f"👤 New User Joined\nID: {uid}\nUsername: @{user.username}"
        )

        if ref and ref != uid and ref in users:
            users[ref]["points"] += 1
            users[ref]["refers"] += 1
            save_json(USERS_FILE, users)

            context.bot.send_message(
                int(ref),
                f"🎉 New Referral Joined!\nUser: @{user.username}\n+1 Point Added"
            )

            context.bot.send_message(
                ADMIN_ID,
                f"👥 Referral Completed\nReferrer: {ref}\nUser: @{user.username}"
            )

    menu = [
        ["💌 Refer & Earn", "🎁 Withdraw"],
        ["👛 Wallet", "📜 History"],
        ["☎️ Support"]
    ]

    update.message.reply_text(
        "🏠 Main Menu",
        reply_markup=ReplyKeyboardMarkup(menu, resize_keyboard=True)
    )


def joined_cb(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()
    start(q, context)


# ---------- REFER ---------- #

def refer(update: Update, context: CallbackContext):
    uid = update.message.from_user.id
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    msg = f"""👥 Refer & Earn

🎯 1 referral = 1 point

🔗 Your referral link:
{link}

⚠️ Same user count only once
❌ Self referral not allowed"""

    update.message.reply_text(msg)


# ---------- WALLET ---------- #

def read_codes(file):
    try:
        return open(file).read().splitlines()
    except:
        return []


def wallet(update: Update, context: CallbackContext):
    uid = str(update.message.from_user.id)
    pts = users.get(uid, {}).get("points", 0)

    c500 = len(read_codes(CODES500_FILE))
    c1000 = len(read_codes(CODES1000_FILE))

    msg = f"""👛 Your Wallet

💰 Points: {pts}

🎁 Rewards:

{'✅' if c500 else '❌'} ₹500 OFF — 1 Point
{'✅' if c1000 else '❌'} ₹1000 OFF — 5 Points"""

    update.message.reply_text(msg)


# ---------- HISTORY ---------- #

def history(update: Update, context: CallbackContext):
    uid = str(update.message.from_user.id)
    h = users.get(uid, {}).get("history", [])

    if not h:
        update.message.reply_text("No redeem history")
    else:
        update.message.reply_text("\n".join(h))


# ---------- SUPPORT ---------- #

def support(update: Update, context: CallbackContext):
    update.message.reply_text(f"Contact: {SUPPORT_ID}")


# ---------- WITHDRAW ---------- #

def withdraw_menu(update: Update, context: CallbackContext):
    btn = [
        [InlineKeyboardButton("₹500 Coupon (1 pt)", callback_data="c500")],
        [InlineKeyboardButton("₹1000 Coupon (5 pt)", callback_data="c1000")]
    ]

    update.message.reply_text(
        "Choose Coupon",
        reply_markup=InlineKeyboardMarkup(btn)
    )


# ---------- REDEEM ---------- #

def redeem_cb(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()
    uid = str(q.from_user.id)

    if q.data == "c500":
        need = 1
        file = CODES500_FILE
        name = "₹500"
    else:
        need = 5
        file = CODES1000_FILE
        name = "₹1000"

    if users[uid]["points"] < need:
        q.message.reply_text("Not enough points")
        return

    codes = read_codes(file)
    if not codes:
        q.message.reply_text("Out of stock")
        return

    code = random.choice(codes)
    codes.remove(code)
    open(file, "w").write("\n".join(codes))

    users[uid]["points"] -= need
    users[uid]["history"].append(code)
    save_json(USERS_FILE, users)

    q.message.reply_text(
        f"🎉 Coupon Redeemed\n\nCode: {code}"
    )

    context.bot.send_message(
        ADMIN_ID,
        f"🎁 Coupon Redeemed\nUser: {uid}\nCoupon: {name}\nCode: {code}\nRemaining: {len(codes)}"
    )


# ---------- ADMIN ---------- #

def admin(update: Update, context: CallbackContext):
    if update.message.from_user.id != ADMIN_ID:
        return

    menu = [
        ["Add Channel", "Remove Channel"],
        ["Add 500 Codes", "Add 1000 Codes"],
        ["Give Points", "Broadcast"],
        ["Statistics", "Check Stock"]
    ]

    update.message.reply_text(
        "Admin Panel",
        reply_markup=ReplyKeyboardMarkup(menu, resize_keyboard=True)
    )


def admin_text(update: Update, context: CallbackContext):

    if update.message.from_user.id != ADMIN_ID:
        return

    text = update.message.text


    if text == "Check Stock":
        c500 = len(read_codes(CODES500_FILE))
        c1000 = len(read_codes(CODES1000_FILE))

        update.message.reply_text(
            f"Stock:\n₹500 → {c500}\n₹1000 → {c1000}"
        )
        return


    if text == "Statistics":
        update.message.reply_text(f"Total Users: {len(users)}")
        return


    if text == "Add Channel":
        update.message.reply_text("Send channel username")
        context.user_data["mode"] = "add_ch"
        return

    if context.user_data.get("mode") == "add_ch":
        open(CHANNELS_FILE, "a").write(text + "\n")
        update.message.reply_text("Channel Added")
        context.user_data.clear()
        return


    if text == "Remove Channel":
        update.message.reply_text("Send channel username")
        context.user_data["mode"] = "rem_ch"
        return

    if context.user_data.get("mode") == "rem_ch":
        chs = load_channels()
        if text in chs:
            chs.remove(text)
            open(CHANNELS_FILE, "w").write("\n".join(chs))
        update.message.reply_text("Channel Removed")
        context.user_data.clear()
        return


    if text == "Add 500 Codes":
        update.message.reply_text("Send codes")
        context.user_data["mode"] = "c500"
        return

    if context.user_data.get("mode") == "c500":
        open(CODES500_FILE, "a").write(text + "\n")
        update.message.reply_text("500 Codes Added")
        return


    if text == "Add 1000 Codes":
        update.message.reply_text("Send codes")
        context.user_data["mode"] = "c1000"
        return

    if context.user_data.get("mode") == "c1000":
        open(CODES1000_FILE, "a").write(text + "\n")
        update.message.reply_text("1000 Codes Added")
        return


    if text == "Broadcast":
        update.message.reply_text("Send message")
        context.user_data["mode"] = "bc"
        return

    if context.user_data.get("mode") == "bc":
        for u in users:
            try:
                context.bot.send_message(int(u), text)
            except:
                pass
        update.message.reply_text("Broadcast Sent")
        return


    if text == "Give Points":
        update.message.reply_text("Send: user_id points")
        context.user_data["mode"] = "gp"
        return

    if context.user_data.get("mode") == "gp":
        uid, pts = text.split()
        users[uid]["points"] += int(pts)
        save_json(USERS_FILE, users)
        update.message.reply_text("Points Added")
        return


# ---------- TEXT ---------- #

def text_handler(update: Update, context: CallbackContext):
    t = update.message.text

    if t == "💌 Refer & Earn":
        refer(update, context)

    elif t == "🎁 Withdraw":
        withdraw_menu(update, context)

    elif t == "👛 Wallet":
        wallet(update, context)

    elif t == "📜 History":
        history(update, context)

    elif t == "☎️ Support":
        support(update, context)


# ---------- RUN ---------- #

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("admin", admin))
dp.add_handler(CallbackQueryHandler(joined_cb, pattern="joined"))
dp.add_handler(CallbackQueryHandler(redeem_cb, pattern="^c"))
dp.add_handler(MessageHandler(Filters.text, admin_text), group=1)
dp.add_handler(MessageHandler(Filters.text, text_handler), group=2)

updater.start_polling()
updater.idle()