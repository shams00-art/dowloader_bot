import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
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
        "🚀 Men biznes rejimda ishlaydigan downloader botman.\n"
        "Istalgan chatga link yuborsangiz, Video yoki MP3 tanlash uchun tugmalar chiqaraman!"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.MARKDOWN)


# Link kelganda tugmalar chiqarish (Ham oddiy, ham biznes chatlar uchun)
@dp.message(F.text.regexp(r'https?://[^\s]+'))
async def send_download_choice(message: Message) -> None:
    url = message.text.strip()
    # Tugmalar: Video yoki MP3 yuklab olish uchun
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎬 Video", callback_data=f"dl_video|{url}"),
            InlineKeyboardButton(text="🎵 Musiqa (MP3)", callback_data=f"dl_audio|{url}")
        ]
    ])
    
    # Biznes xabar bo'lsa connection_id ni saqlaymiz
    await message.answer(
        "📥 *Qanday formatda yuklab olmoqchisiz?*", 
        reply_markup=keyboard, 
        parse_mode=ParseMode.MARKDOWN
    )


# Tugma bosilganda ishlaydigan qism
@dp.callback_query(F.data.startswith("dl_"))
async def process_download(callback: CallbackQuery):
    data_parts = callback.data.split("|", 1)
    action = data_parts[0] # dl_video yoki dl_audio
    url = data_parts[1]
    
    message = callback.message
    business_conn_id = message.business_connection_id if hasattr(message, "business_connection_id") else None

    await callback.answer("⏳ Yuklab olish boshlandi...")
    status_msg = await message.answer("⚡️ *Fayl tayyorlanmoqda, kuting...*", parse_mode=ParseMode.MARKDOWN)

    file_path = None
    try:
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
            'noplaylist': True,
        }

        if action == "dl_audio":
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            ydl_opts['format'] = 'best[filesize<40M]/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if action == "dl_audio":
                base, _ = os.path.splitext(filename)
                file_path = base + ".mp3"
            else:
                if os.path.exists(filename):
                    file_path = filename
                else:
                    base, _ = os.path.splitext(filename)
                    for ext in ['.mp4', '.mkv', '.webm']:
                        if os.path.exists(base + ext):
                            file_path = base + ext
                            break

        if file_path and os.path.exists(file_path):
            await status_msg.edit_text("📤 *Yuborilmoqda...*", parse_mode=ParseMode.MARKDOWN)
            caption_text = "📥 @xertion_bot orqali yuklab olindi"
            
            # Biznes chat orqali yuborishda business_connection_id ni qo'shamiz
            send_kwargs = {"caption": caption_text}
            if business_conn_id:
                send_kwargs["business_connection_id"] = business_conn_id

            if action == "dl_audio":
                await message.answer_audio(FSInputFile(file_path), **send_kwargs)
            else:
                await message.answer_video(FSInputFile(file_path), **send_kwargs)
            
            await status_msg.delete()
            try:
                os.remove(file_path)
            except:
                pass
        else:
            await status_msg.edit_text("❌ Kechirasiz, bu havoladan faylni yuklab bo'lmadi.")

    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi. Havolani tekshiring.")


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
            "deleted_business_messages",
            "callback_query"
        ]
    )

if __name__ == "__main__":
    asyncio.run(main())