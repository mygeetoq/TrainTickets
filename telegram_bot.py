import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from bot_core import TrainTicketBot

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize the core bot
ticket_bot = TrainTicketBot()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    welcome_text = "Привет! 🚂 Я ваш интеллектуальный помощник по ЖД билетам.\n\n" \
                   "Я могу помочь вам:\n" \
                   "- Купить или забронировать билеты\n" \
                   "- Узнать расписание и цены\n" \
                   "- Ответить на общие вопросы о поездках\n\n" \
                   "Просто напишите мне что-нибудь!"
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming text messages."""
    user_text = update.message.text
    response = ticket_bot.get_response(user_text)
    await update.message.reply_text(response)

if __name__ == '__main__':
    # The token should be provided by the user
    TOKEN = '8891053314:AAEMwX4O5oxsPfVa4QrltgdI0LeB9sf1soE'
    
    if not TOKEN:
        print("Ошибка: Переменная окружения TELEGRAM_BOT_TOKEN не задана.")
        print("Пожалуйста, установите её перед запуском: export TELEGRAM_BOT_TOKEN='ваш_токен'")
    else:
        application = ApplicationBuilder().token(TOKEN).build()
        
        start_handler = CommandHandler('start', start)
        msg_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
        
        application.add_handler(start_handler)
        application.add_handler(msg_handler)
        
        print("Бот запускается в Telegram...")
        application.run_polling()
