#!/usr/bin/env python3
import os
import yt_dlp
import telebot
import tempfile
import shutil
from pathlib import Path

# ==== Load environment variables ====
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

if not BOT_TOKEN:
    raise SystemExit("🚨 BOT_TOKEN not set. Please set it in Railway environment variables.")

# Convert CHANNEL_ID to integer if set
if CHANNEL_ID:
    try:
        CHANNEL_ID = int(CHANNEL_ID)
    except ValueError:
        print("⚠️ CHANNEL_ID is not a valid number. Videos to channel may fail.")
        CHANNEL_ID = None

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==== Facebook Download Function ====
def download_with_yt_dlp(url, quality='best'):
    tmpdir = tempfile.mkdtemp(prefix="yt_")
    output_template = os.path.join(tmpdir, '%(title)s.%(ext)s')
    ydl_opts = {
        'outtmpl': output_template,
        'format': quality,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, tmpdir
    except Exception as e:
        print("❌ Download error:", e)
        shutil.rmtree(tmpdir, ignore_errors=True)
        return None, None

# ==== Bot Handlers ====
@bot.message_handler(commands=['start'])
def welcome(msg):
    bot.reply_to(
        msg,
        "👋 Welcome!\n\n"
        "Send a Facebook video link like:\n"
        "<code>/fac https://www.facebook.com/watch?v=xxxx</code>"
    )

@bot.message_handler(commands=['fac'])
def handle_fac(msg):
    try:
        parts = msg.text.split(maxsplit=1)
        if len(parts) < 2:
            bot.reply_to(msg, "⚠️ Please send a Facebook video link after /fac")
            return

        url = parts[1].strip()
        waiting_msg = bot.reply_to(msg, "📥 Downloading video... please wait ⏳")

        # Download the video
        filename, tmpdir = download_with_yt_dlp(url)

        # Remove waiting message
        try:
            bot.delete_message(msg.chat.id, waiting_msg.message_id)
        except Exception:
            pass

        if not filename or not os.path.exists(filename):
            bot.reply_to(msg, "❌ Failed to download the video.")
            return

        # Send video to user
        with open(filename, "rb") as vid:
            bot.send_video(msg.chat.id, vid, caption="✅ Done!")

        # Send video to private channel if CHANNEL_ID is set
        if CHANNEL_ID:
            try:
                with open(filename, "rb") as vid:
                    name = msg.from_user.username or msg.from_user.first_name or "user"
                    bot.send_video(CHANNEL_ID, vid, caption=f"📺 From: @{name}")
            except Exception as e:
                print("⚠️ Failed to send to channel:", e)

        # Cleanup temp folder
        shutil.rmtree(tmpdir, ignore_errors=True)

    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error: {e}")

if __name__ == "__main__":
    print("🤖 Bot is running...")
    bot.infinity_polling()
