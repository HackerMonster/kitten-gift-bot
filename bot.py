from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram import F
import asyncio
import logging
import json
import os
from aiohttp import web

# ==================== НАСТРОЙКИ ====================

TOKEN = "8682369232:AAH3qcTjO0QYdfGvunCNT1zaTkhyGTnm0Co"

# ССЫЛКА НА ВАШ БОТ НА RENDER (ЗАМЕНИТЕ ПОСЛЕ ДЕПЛОЯ!)
WEBHOOK_URL = "https://ВАШ-БОТ.onrender.com/webhook"

# ССЫЛКА НА MINI APP (ОТ BOTFATHER) С ПАРАМЕТРОМ
MINIAPP_URL = "https://t.me/kittenGift_Bot/adminpanel?startapp=adminpanel"

# ID администраторов
ADMINS = ["5870949629"]

# Список пользователей для рассылки (ДОБАВЛЯЙТЕ СЮДА)
USERS = [
    "5870949629",
    # "123456789",
]

# ==================== КОД БОТА ====================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    welcome = (
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Добро пожаловать в бота @kittenGift_Bot\n\n"
        f"🆔 Ваш ID: {message.from_user.id}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="⚙️ Админ-панель",
            url=MINIAPP_URL
        )]
    ])
    
    await message.answer(welcome, reply_markup=keyboard)

@dp.message(F.text)
async def handle_webapp_data(message: types.Message):
    user_id = str(message.from_user.id)
    text = message.text
    
    if not text or not text.startswith('{"action"'):
        return
    
    try:
        data = json.loads(text)
        action = data.get("action")
        
        logger.info(f"📩 Получены данные от {user_id}: {action}")
        
        if action == "broadcast":
            if user_id not in ADMINS:
                await message.answer("❌ У вас нет прав для рассылки.")
                return
            
            broadcast_text = data.get("text", "")
            if not broadcast_text:
                await message.answer("❌ Текст рассылки не может быть пустым.")
                return
            
            await message.answer(f"📨 Начинаю рассылку для {len(USERS)} пользователей...")
            
            success = 0
            for uid in USERS:
                try:
                    await bot.send_message(chat_id=int(uid), text=broadcast_text)
                    success += 1
                    await asyncio.sleep(0.05)
                except Exception as e:
                    logger.error(f"Ошибка отправки {uid}: {e}")
            
            await message.answer(
                f"✅ Рассылка завершена!\n"
                f"📨 Отправлено: {success} из {len(USERS)} пользователей"
            )
        
        elif action == "stats":
            await message.answer(
                f"📊 *Статистика*\n\n"
                f"👥 Всего пользователей: {len(USERS)}\n"
                f"👑 Администраторов: {len(ADMINS)}",
                parse_mode="Markdown"
            )
        
        elif action == "get_users":
            users_list = "\n".join([f"🆔 {uid}" for uid in USERS[:10]])
            more = "\n...и еще" if len(USERS) > 10 else ""
            await message.answer(
                f"👥 *Список пользователей (первые 10)*\n\n{users_list}{more}",
                parse_mode="Markdown"
            )
    
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await message.answer(f"❌ Произошла ошибка: {str(e)}")

async def webhook(request):
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot, update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Ошибка Webhook: {e}")
        return web.Response(status=500)

async def set_webhook():
    await bot.delete_webhook()
    result = await bot.set_webhook(url=WEBHOOK_URL)
    if result:
        logger.info("✅ Webhook установлен!")
    return result

async def on_startup():
    logger.info("🚀 Бот запускается...")
    await set_webhook()
    logger.info("✅ Бот готов!")

async def main():
    app = web.Application()
    app.router.add_post("/webhook", webhook)
    app.router.add_get("/", lambda req: web.Response(text="✅ Bot is running!"))
    
    await on_startup()
    
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"🌐 Запуск на порту {port}")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    
    logger.info("✅ Сервер запущен!")
    
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("⏹️ Остановка...")
        await bot.delete_webhook()

if __name__ == "__main__":
    asyncio.run(main())
