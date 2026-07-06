import telebot
import json
import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime

# ==================== НАСТРОЙКИ ====================

TOKEN = "8682369232:AAH3qcTjO0QYdfGvunCNT1zaTkhyGTnm0Co"
WEBHOOK_URL = "https://kitten-gift-bot.onrender.com/webhook"
MINIAPP_URL = "https://t.me/kittenGift_Bot/app"  # Ссылка на Mini App

# Хранилище последних посетителей (максимум 7)
last_visitors = []  # [{"user_id": "123", "name": "Имя", "username": "@user", "time": "2024-01-01 12:00"}]

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)

# ==================== КОМАНДА /start ====================

@bot.message_handler(commands=['start'])
def start(message):
    welcome = (
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Добро пожаловать в бота @kittenGift_Bot\n\n"
        f"🆔 Ваш ID: {message.from_user.id}"
    )

    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(
        text="🚀 Открыть Mini App",
        url=MINIAPP_URL
    ))

    bot.reply_to(message, welcome, reply_markup=keyboard)

# ==================== API ДЛЯ MINI APP ====================

@app.route('/api/visitor', methods=['POST', 'OPTIONS'])
def api_visitor():
    """Сохраняет информацию о посетителе"""
    
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        data = request.json
        user_id = data.get('user_id')
        name = data.get('name', 'Пользователь')
        username = data.get('username', '')

        if not user_id:
            return jsonify({"status": "error", "message": "user_id обязателен"}), 400

        # Проверяем, есть ли уже этот пользователь в списке
        for visitor in last_visitors:
            if visitor['user_id'] == user_id:
                last_visitors.remove(visitor)
                break

        # Добавляем в начало списка
        last_visitors.insert(0, {
            'user_id': user_id,
            'name': name,
            'username': username,
            'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

        # Оставляем только 7 последних
        if len(last_visitors) > 7:
            last_visitors = last_visitors[:7]

        return jsonify({
            "status": "success",
            "message": "Посетитель сохранён",
            "data": {"visitors": last_visitors}
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/visitors', methods=['GET', 'OPTIONS'])
def api_get_visitors():
    """Возвращает список последних посетителей"""
    
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    return jsonify({
        "status": "success",
        "data": {"visitors": last_visitors}
    })

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
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"🚀 Webhook установлен: {WEBHOOK_URL}")
    print(f"📱 Mini App: {MINIAPP_URL}")

    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
