import telebot
import json
import os
import time
from flask import Flask, request, jsonify

# ==================== НАСТРОЙКИ ====================

TOKEN = "8682369232:AAH3qcTjO0QYdfGvunCNT1zaTkhyGTnm0Co"
WEBHOOK_URL = "https://kitten-gift-bot.onrender.com/webhook"
MINIAPP_URL = "https://t.me/kittenGift_Bot/adminpanel?startapp=adminpanel"

ADMINS = ["5870949629"]
USERS = ["5870949629"]  # Добавляйте ID пользователей

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==================== ОБРАБОТЧИКИ КОМАНД ====================

@bot.message_handler(commands=['start'])
def start(message):
    welcome = (
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Добро пожаловать в бота @kittenGift_Bot\n\n"
        f"🆔 Ваш ID: {message.from_user.id}"
    )
    
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(
        text="⚙️ Админ-панель",
        url=MINIAPP_URL
    ))
    
    bot.reply_to(message, welcome, reply_markup=keyboard)

# ==================== ОБРАБОТЧИК ДАННЫХ ИЗ MINI APP ====================

@bot.message_handler(func=lambda message: message.text and message.text.startswith('{"action"'))
def handle_webapp_data(message):
    user_id = str(message.from_user.id)
    text = message.text
    
    try:
        data = json.loads(text)
        action = data.get("action")
        
        # === РАССЫЛКА ===
        if action == "broadcast":
            if user_id not in ADMINS:
                bot.reply_to(message, "❌ У вас нет прав для рассылки.")
                return
            
            broadcast_text = data.get("text", "")
            if not broadcast_text:
                bot.reply_to(message, "❌ Текст рассылки не может быть пустым.")
                return
            
            bot.reply_to(message, f"📨 Начинаю рассылку для {len(USERS)} пользователей...")
            
            success = 0
            for uid in USERS:
                try:
                    bot.send_message(chat_id=int(uid), text=broadcast_text)
                    success += 1
                    time.sleep(0.05)
                except Exception as e:
                    print(f"Ошибка отправки {uid}: {e}")
            
            bot.reply_to(
                message,
                f"✅ Рассылка завершена!\n📨 Отправлено: {success} из {len(USERS)} пользователей"
            )
        
        # === СТАТИСТИКА ===
        elif action == "stats":
            bot.reply_to(
                message,
                f"📊 *Статистика*\n\n"
                f"👥 Всего пользователей: {len(USERS)}\n"
                f"👑 Администраторов: {len(ADMINS)}",
                parse_mode="Markdown"
            )
        
        # === СПИСОК ПОЛЬЗОВАТЕЛЕЙ ===
        elif action == "get_users":
            users_list = "\n".join([f"🆔 {uid}" for uid in USERS[:10]])
            more = "\n...и еще" if len(USERS) > 10 else ""
            bot.reply_to(
                message,
                f"👥 *Список пользователей (первые 10)*\n\n{users_list}{more}",
                parse_mode="Markdown"
            )
    
    except Exception as e:
        print(f"Ошибка: {e}")
        bot.reply_to(message, f"❌ Произошла ошибка: {str(e)}")

# ==================== WEBHOOK ====================

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_str = request.get_data().decode('UTF-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print(f"Ошибка Webhook: {e}")
        return jsonify({"status": "error"}), 500

@app.route('/', methods=['GET'])
def index():
    return "✅ Bot is running!"

# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    # Удаляем старый Webhook
    bot.remove_webhook()
    
    # Устанавливаем новый Webhook
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"🚀 Webhook установлен: {WEBHOOK_URL}")
    
    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
