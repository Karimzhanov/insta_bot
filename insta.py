import instaloader
from aiogram import Bot, Dispatcher, executor, types
import requests
import os
import tempfile
import logging
from config import token

# Инициализация бота и диспетчера
bot = Bot(token=token)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

# Инициализация Instaloader
L = instaloader.Instaloader()

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! Отправь мне ссылку на видео из Instagram или TikTok, и я загружу его для тебя.")

@dp.message_handler()
async def download_video(message: types.Message):
    url = message.text.strip()

    if "instagram.com/reel/" in url:
        await message.reply("Видео из Instagram загружается, пожалуйста, подождите...")
        try:
            short_code = url.split("/reel/")[1].split("/")[0]
            post = instaloader.Post.from_shortcode(L.context, short_code)

            # Создание временной директории для загрузки
            with tempfile.TemporaryDirectory() as temp_dir:
                L.dirname_pattern = temp_dir
                L.download_post(post, target='')

                # Поиск всех файлов во временной директории
                files = os.listdir(temp_dir)

                # Поиск файла видео
                video_file = None
                for file in files:
                    if file.endswith('.mp4'):
                        video_file = os.path.join(temp_dir, file)
                        break

                if video_file:
                    await bot.send_video(message.chat.id, open(video_file, 'rb'))
                else:
                    await message.reply("Не удалось найти загруженное видео.")
        except Exception as e:
            await message.reply(f"Произошла ошибка при загрузке видео из Instagram: {e}")

    elif "tiktok.com/" in url:
        await message.reply("Видео из TikTok загружается, пожалуйста, подождите...")
        try:
            # Получение прямой ссылки на видео TikTok
            response = requests.get(url)
            if response.status_code == 200:
                html = response.text
                video_url = html.split('src_no_ratelimit":"')[1].split('"')[0].replace('amp;', '')
                
                # Создание временной директории для загрузки
                with tempfile.TemporaryDirectory() as temp_dir:
                    video_path = os.path.join(temp_dir, 'video.mp4')

                    # Загрузка видео
                    video_data = requests.get(video_url).content
                    with open(video_path, 'wb') as f:
                        f.write(video_data)

                    # Отправка видео пользователю
                    await bot.send_video(message.chat.id, open(video_path, 'rb'))
            else:
                await message.reply("Не удалось найти URL для загрузки видео.")
        except Exception as e:
            await message.reply(f"Произошла ошибка при загрузке видео из TikTok: {e}")
    else:
        await message.reply("Пожалуйста, отправьте действительную ссылку на видео из Instagram или TikTok.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
