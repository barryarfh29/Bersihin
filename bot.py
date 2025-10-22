import os, re, logging
from collections import OrderedDict
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    ContextTypes, filters
)

# ====== Setup ======
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Baca token dari .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN tidak ditemukan. Pastikan file .env berisi: BOT_TOKEN=xxx "
        "dan file .env berada di folder yang sama dengan bot.py."
    )

# ====== Aturan filter: sisakan hanya link & @mention ======
TOKEN_PATTERN = re.compile(
    r'(https?://\S+|http://\S+|t\.me/\S+|@[\w_]+)',
    flags=re.IGNORECASE
)

def extract_tokens(text: str):
    seen = OrderedDict()
    for m in TOKEN_PATTERN.finditer(text or ""):
        token = m.group(0).strip().rstrip('.,;!?)"]}')
        if token and token not in seen:
            seen[token] = True
    return list(seen.keys())

# ====== Handlers ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hai! Aku akan membersihkan pesan: hanya sisakan link & @mention.\n"
        "• Jadikan aku admin dengan izin Delete messages.\n"
        "• Otomatis untuk semua pesan teks.\n"
        "• Atau balas pesan lalu pakai /clean untuk bersihkan satu pesan."
    )

async def clean_single(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = update.message.reply_to_message
    if not target or not (target.text or target.caption):
        return await update.message.reply_text(
            "Reply /clean ke pesan teks yang mau dibersihkan ya."
        )
    text = target.text or target.caption
    tokens = extract_tokens(text)
    cleaned = "\n".join(tokens) if tokens else ""
    try:
        await target.delete()
    except Exception as e:
        logging.info(f"Gagal hapus pesan target: {e}")
    if cleaned:
        await update.message.reply_text(cleaned, disable_web_page_preview=True)

async def auto_clean(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Abaikan pesan dari bot
    if update.effective_user and update.effective_user.is_bot:
        return
    msg = update.message
    text = msg.text or msg.caption
    tokens = extract_tokens(text)
    cleaned = "\n".join(tokens) if tokens else ""

    # Jika tidak ada link/mention, hapus pesan (opsional)
    if not cleaned:
        try:
            await msg.delete()
        except Exception as e:
            logging.info(f"Gagal hapus pesan kosong: {e}")
        return

    # Hapus pesan asli, kirim versi bersih
    try:
        await msg.delete()
    except Exception as e:
        logging.info(f"Gagal hapus pesan asli: {e}")
    await msg.chat.send_message(cleaned, disable_web_page_preview=True)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clean", clean_single))
    # Otomatis bersihkan semua pesan teks/caption
    app.add_handler(MessageHandler(filters.TEXT | filters.CAPTION, auto_clean))

    app.run_polling()

if __name__ == "__main__":
    main()
