import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from aiohttp import web
import yt_dlp

TOKEN = os.getenv("BOT_TOKEN", "8703127466:AAHB4GsnEf8vLLXR4pUp10Igmj7xjLAkMAg")

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

dp = Dispatcher()

# Render port talabini qondirish uchun veb-server
async def handle(request):
    return web.Response(text="Bot is running and alive!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    welcome_text = (
        f"✨ **Assalomu alaykum, {html.bold(message.from_user.full_name)}!**\n\n"
        "🚀 Menga istalgan ijtimoiy tarmoqdan link yuboring.\n"
        "Men sizga ham **videoni**, ham uning **MP3 audiosini** yuboraman!"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.MARKDOWN)


# Link kelganda avtomatik ravishda video va MP3 ni birga yuklab yuborish
@dp.message(F.text.regexp(r'https?://[^\s]+'))
async def download_media(message: Message) -> None:
    url = message.text.strip()
    status_msg = await message.answer("⚡️ *Video va audio yuklab olinmoqda, kuting...*", parse_mode=ParseMode.MARKDOWN)
    
    video_path = None
    audio_path = None
    
    try:
        # 1. Videoni yuklab olish
        ydl_video_opts = {
            'format': 'best[filesize<40M]/best',
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s_video.%(ext)s',
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_video_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if os.path.exists(filename):
                video_path = filename
            else:
                base, _ = os.path.splitext(filename)
                for ext in ['.mp4', '.mkv', '.webm']:
                    if os.path.exists(base + ext):
                        video_path = base + ext
                        break

        # 2. MP3 audioni ajratib olish
        ydl_audio_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s_audio.%(ext)s',
            'noplaylist': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_audio_opts) as ydl:
            info_audio = ydl.extract_info(url, download=True)
            filename_audio = ydl.prepare_filename(info_audio)
            base, _ = os.path.splitext(filename_audio)
            if os.path.exists(base + ".mp3"):
                audio_path = base + ".mp3"

        # Biznes chat uchun ID ni aniqlaymiz
        business_conn_id = message.business_connection_id if hasattr(message, "business_connection_id") else None
        send_kwargs = {}
        if business_conn_id:
            send_kwargs["business_connection_id"] = business_conn_id

        caption_text = "📥 @xertion_bot orqali yuklab olindi"

        # Videoni yuborish
        if video_path and os.path.exists(video_path):
            await message.answer_video(FSInputFile(video_path), caption=caption_text, **send_kwargs)

        # MP3 audioni yuborish
        if audio_path and os.path.exists(audio_path):
            await message.answer_audio(FSInputFile(audio_path), caption=caption_text, **send_kwargs)

        await status_msg.delete()

        # Fayllarni o'chirish (server xotirasi to'lib qolmasligi uchun)
        for p in [video_path, audio_path]:
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except:
                    pass

        if not video_path and not audio_path:
            await status_msg.edit_text("❌ Kechirasiz, bu havoladan fayllarni yuklab bo'lmadi.")

    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi. Havolaning ochiqligini tekshiring.")


async def main() -> None:
    await start_web_server()

    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)
    
    await dp.start_polling(
        bot, 
        allowed_updates=[
            "message", 
            "edited_message", 
            "business_message", 
            "business_connection", 
            "deleted_business_messages"
        ]
    )

if __name__ == "__main__":
    asyncio.run(main())