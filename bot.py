import telebot
import json
import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# ==================== НАСТРОЙКИ ====================

TOKEN = "8682369232:AAH3qcTjO0QYdfGvunCNT1zaTkhyGTnm0Co"
WEBHOOK_URL = "https://kitten-gift-bot.onrender.com/webhook"
MINIAPP_URL = "https://t.me/kittenGift_Bot/adminpanel?startapp=adminpanel"

# Администраторы (могут делать рассылку)
ADMINS = ["5870949629"]

# Пользователи для рассылки (ДОБАВЛЯЙТЕ СЮДА)
USERS = [
    "5870949629",  # Вы
    # "123456789",  # Другой пользователь
    # "987654321",  # Ещё один
]

# Счётчик рассылок
broadcast_count = 0

# ==================== ИНИЦИАЛИЗАЦИЯ ====================

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
CORS(app)  # Разрешает запросы с любых доменов

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
        text="⚙️ Админ-панель",
        url=MINIAPP_URL
    ))

    bot.reply_to(message, welcome, reply_markup=keyboard)

# ==================== ФУНКЦИЯ РАССЫЛКИ ====================

def send_broadcast(text, photo_url=None, admin_id=None):
    """Отправляет рассылку всем пользователям"""
    global broadcast_count
    success = 0

    for uid in USERS:
        try:
            if photo_url:
                # Отправляем с фото
                bot.send_photo(chat_id=int(uid), photo=photo_url, caption=text)
            else:
                # Отправляем только текст
                bot.send_message(chat_id=int(uid), text=text)
            success += 1
            time.sleep(0.05)  # Защита от блокировки
        except Exception as e:
            print(f"Ошибка отправки {uid}: {e}")

    broadcast_count += 1
    return success

# ==================== API ДЛЯ HTML ====================

@app.route('/api/send', methods=['POST', 'OPTIONS'])
def api_send():
    """Принимает POST-запрос из HTML и делает рассылку"""
    
    # Обработка preflight запроса (CORS)
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Получаем данные (поддерживаем и JSON, и FormData)
        admin_id = request.form.get('admin_id') or request.json.get('admin_id')
        text = request.form.get('text') or request.json.get('text', '')

        # Проверяем права
        if admin_id not in ADMINS:
            response = jsonify({
                "status": "error",
                "message": "У вас нет прав для рассылки."
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 403

        if not text:
            response = jsonify({
                "status": "error",
                "message": "Текст рассылки не может быть пустым."
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if len(text) < 5:
            response = jsonify({
                "status": "error",
                "message": "Текст слишком короткий (минимум 5 символов)."
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Проверяем фото
        photo = request.files.get('photo')
        photo_url = None

        if photo:
            # Сохраняем фото временно
            filename = f"photo_{int(time.time())}.jpg"
            photo.save(filename)
            photo_url = filename
            print(f"📸 Фото сохранено: {filename}")

        # Делаем рассылку
        success = send_broadcast(text, photo_url, admin_id)

        # Удаляем временное фото
        if photo_url and os.path.exists(photo_url):
            os.remove(photo_url)

        response = jsonify({
            "status": "success",
            "message": f"Рассылка завершена! Отправлено: {success} из {len(USERS)} пользователей."
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200

    except Exception as e:
        print(f"Ошибка API: {e}")
        response = jsonify({
            "status": "error",
            "message": f"Ошибка: {str(e)}"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

# ==================== API СТАТИСТИКИ ====================

@app.route('/api/stats', methods=['GET', 'OPTIONS'])
def api_stats():
    """Возвращает статистику"""
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    response = jsonify({
        "status": "success",
        "users": len(USERS),
        "admins": len(ADMINS),
        "broadcasts": broadcast_count
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# ==================== API СПИСОК ПОЛЬЗОВАТЕЛЕЙ ====================

@app.route('/api/users', methods=['GET', 'OPTIONS'])
def api_users():
    """Возвращает список пользователей"""
    if request.method == 'OPTIONS':
        response = jsonify({"status": "ok"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    response = jsonify({
        "status": "success",
        "users": USERS
    })
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

# ==================== ОБРАБОТЧИК ДАННЫХ ИЗ MINI APP ====================

@bot.message_handler(func=lambda message: message.text and message.text.startswith('{"action"'))
def handle_webapp_data(message):
    """Обрабатывает данные из Mini App (через tg.sendData)"""
    user_id = str(message.from_user.id)
    text = message.text

    try:
        data = json.loads(text)
        action = data.get("action")

        print(f"📩 Получены данные от {user_id}: {action}")

        if action == "broadcast":
            if user_id not in ADMINS:
                bot.reply_to(message, "❌ У вас нет прав для рассылки.")
                return

            broadcast_text = data.get("text", "")
            if not broadcast_text:
                bot.reply_to(message, "❌ Текст рассылки не может быть пустым.")
                return

            bot.reply_to(message, f"📨 Начинаю рассылку для {len(USERS)} пользователей...")

            success = send_broadcast(broadcast_text, admin_id=user_id)

            bot.reply_to(
                message,
                f"✅ Рассылка завершена!\n📨 Отправлено: {success} из {len(USERS)} пользователей"
            )

        elif action == "stats":
            bot.reply_to(
                message,
                f"📊 *Статистика*\n\n"
                f"👥 Всего пользователей: {len(USERS)}\n"
                f"👑 Администраторов: {len(ADMINS)}",
                parse_mode="Markdown"
            )

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
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

# ==================== WEBHOOK ====================

@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает запросы от Telegram"""
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
    """Проверка, что бот работает"""
    return "✅ Bot is running!"

# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    # Удаляем старый Webhook
    bot.remove_webhook()

    # Устанавливаем новый Webhook
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"🚀 Webhook установлен: {WEBHOOK_URL}")
    print(f"👑 Админы: {ADMINS}")
    print(f"👥 Пользователей: {len(USERS)}")

    # Запускаем Flask сервер
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
