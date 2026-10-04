import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import yt_dlp

# O'z tokeningizni shu yerga yozing
TOKEN = "8703127466:AAHB4GsnEf8vLLXR4pUp10Igmj7xjLAkMAg"

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

dp = Dispatcher()

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    welcome_text = (
        f"✨ **Assalomu alaykum, {html.bold(message.from_user.full_name)}!**\n\n"
        "🚀 Men biznes rejimda ishlaydigan downloader botman.\n"
        "Istalgan chatga link yuborsangiz, uni yuklab beraman!"
    )
    await message.answer(welcome_text, parse_mode=ParseMode.MARKDOWN)


# 1. Botning o'ziga yuborilgan linklar uchun
@dp.message(F.text.regexp(r'https?://[^\s]+'))
async def download_media(message: Message) -> None:
    await handle_download(message, message.text.strip())


# 2. Telegram Business orqali boshqa chatlarda yozilgandagi linklar uchun
@dp.business_message(F.text.regexp(r'https?://[^\s]+'))
async def download_business_media(message: Message) -> None:
    await handle_download(message, message.text.strip())


# Asosiy yuklab berish funksiyasi
async def handle_download(message: Message, url: str):
    status_msg = await message.answer("⚡️ *Media yuklab olinmoqda...*", parse_mode=ParseMode.MARKDOWN)
    
    file_path = None
    try:
        ydl_opts = {
            'format': 'best[filesize<40M]/best',
            'outtmpl': f'{DOWNLOAD_DIR}/%(id)s.%(ext)s',
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if os.path.exists(filename):
                file_path = filename
            else:
                base, _ = os.path.splitext(filename)
                for ext in ['.mp4', '.mkv', '.webm', '.mp3', '.jpg', '.webp']:
                    if os.path.exists(base + ext):
                        file_path = base + ext
                        break

        if file_path and os.path.exists(file_path):
            await status_msg.edit_text("📤 *Yuborilmoqda...*", parse_mode=ParseMode.MARKDOWN)
            
            caption_text = "📥 @xertion_bot orqali yuklab olindi"
            
            if file_path.endswith(('.mp3', '.m4a', '.wav')):
                await message.answer_audio(FSInputFile(file_path), caption=caption_text)
            elif file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                await message.answer_photo(FSInputFile(file_path), caption=caption_text)
            else:
                await message.answer_video(FSInputFile(file_path), caption=caption_text)
            
            await status_msg.delete()
            
            try:
                os.remove(file_path)
            except:
                pass
        else:
            await status_msg.edit_text("❌ Kechirasiz, havoladan faylni yuklab bo'lmadi.")

    except Exception as e:
        logging.error(f"Xatolik: {e}")
        await status_msg.edit_text("❌ Xatolik yuz berdi. Havola ochiqligini tekshiring.")


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Biznes xabarlarni qabul qilishi uchun allowed_updates
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