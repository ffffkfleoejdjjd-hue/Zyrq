from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = "7949383069:AAFjFLsMgBAlWqPcFvKlfS-RZ8Tqr1kCe-M"
ADMIN_ID = 8362709543
CHANNEL_ID = -1003550141591

waiting_ss = {}        # admin_msg_id -> (user_id, file_id, unique_id)
used_unique_ids = set()

user_stats = {}        # user_id -> {"sent":0,"approved":0,"rejected":0}
total_wins = 0


def get_user(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = {"sent": 0, "approved": 0, "rejected": 0}
    return user_stats[user_id]


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("📤 Win SS Gönder", callback_data="send_ss")]]
    await update.message.reply_text(
        f"Marka Zarion Win SS Botuna Hoşgeldin\n\n"
        f"👋 Hoşgeldin {update.effective_user.first_name}\n\n"
        "Win SS atmak için alttaki butona tıkla ⬇️",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 Win İstatistikleri\n\n"
        f"✅ Toplam Onaylanan Win: {total_wins}"
    )


# /me
async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    await update.message.reply_text(
        f"👤 Kullanıcı Paneli\n\n"
        f"📤 Gönderilen: {u['sent']}\n"
        f"✅ Onaylanan: {u['approved']}\n"
        f"❌ Reddedilen: {u['rejected']}"
    )


# Butonlar
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global total_wins
    q = update.callback_query
    await q.answer()

    if q.data == "send_ss":
        await q.message.reply_text("📸 Win SS gönder (sadece fotoğraf)")
        return

    if q.from_user.id != ADMIN_ID:
        return

    if q.data.startswith("approve_"):
        msg_id = int(q.data.split("_")[1])

        if msg_id not in waiting_ss:
            await q.answer("Kayıt yok", show_alert=True)
            return

        user_id, file_id, unique_id = waiting_ss.pop(msg_id)

        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=file_id
        )

        u = get_user(user_id)
        u["approved"] += 1
        total_wins += 1

        await context.bot.send_message(
            chat_id=user_id,
            text="✅ Win SS onaylandı ve kanala atıldı"
        )

        await q.message.edit_caption("✅ ONAYLANDI")

    elif q.data.startswith("reject_"):
        msg_id = int(q.data.split("_")[1])

        if msg_id not in waiting_ss:
            await q.answer("Kayıt yok", show_alert=True)
            return

        user_id, _, unique_id = waiting_ss.pop(msg_id)

        u = get_user(user_id)
        u["rejected"] += 1

        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Win SS reddedildi"
        )

        await q.message.edit_caption("❌ REDDEDİLDİ")


# Foto yakala
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo = update.message.photo[-1]
    unique_id = photo.file_unique_id

    if unique_id in used_unique_ids:
        await update.message.reply_text("❌ Bu Win SS daha önce gönderilmiş")
        return

    used_unique_ids.add(unique_id)

    u = get_user(user.id)
    u["sent"] += 1

    sent = await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo.file_id,
        caption=f"📥 Yeni Win SS\n\n👤 {user.first_name} (@{user.username})"
    )

    kb = [
        [
            InlineKeyboardButton("✅ Onayla", callback_data=f"approve_{sent.message_id}"),
            InlineKeyboardButton("❌ Reddet", callback_data=f"reject_{sent.message_id}")
        ]
    ]

    await sent.edit_reply_markup(reply_markup=InlineKeyboardMarkup(kb))

    waiting_ss[sent.message_id] = (user.id, photo.file_id, unique_id)

    await update.message.reply_text("⏳ Admin onayı bekleniyor")


# BOT
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CommandHandler("me", me))
app.add_handler(CallbackQueryHandler(buttons))
app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

print("✅ Win SS bot aktif...")
app.run_polling()