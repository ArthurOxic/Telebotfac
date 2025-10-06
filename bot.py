#!/usr/bin/env python3
import os
import yt_dlp
import telebot
import tempfile
import shutil

# ==== BOT CONFIG ====
BOT_TOKEN = "8196935057:AAE6GH-lZmB4z2qB-CRQZ__SBEyLhUb8bHI"
CHANNEL_ID = -1002994588817  # Your private channel UID

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==== Facebook Download Function ====
def download_with_yt_dlp(url, quality='best'):
    """
    Download Facebook video using yt-dlp into a temporary directory.
    Returns the full path to the video file and the temp folder path for cleanup.
    """
    tmpdir = tempfile.mkdtemp()  # Create temp folder
    output_template = os.path.join(tmpdir, '%(title)s.%(ext)s')
    ydl_opts = {
        'outtmpl': output_template,
        'format': quality,
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename, tmpdir  # return temp folder for cleanup
    except Exception as e:
        print("Error downloading:", e)
        shutil.rmtree(tmpdir, ignore_errors=True)  # cleanup on error
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

        # Send video to private channel
        with open(filename, "rb") as vid:
            bot.send_video(CHANNEL_ID, vid, caption=f"📺 From: @{msg.from_user.username or msg.from_user.first_name}")

        # Cleanup temp folder
        shutil.rmtree(tmpdir, ignore_errors=True)

    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error: {e}")

print("🤖 Bot is running...")
bot.infinity_polling()
