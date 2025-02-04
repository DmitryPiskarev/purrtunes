import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

TOKEN = "7617995358:AAETcvbNgkrP4eNkvW4ph9pAcpXy-fRfL3M"
API_URL = "http://127.0.0.1:8000"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome to AI Music Bot! Type /generate_music to create a song.")


async def generate_music(update: Update, context: CallbackContext) -> None:
    response = requests.get(f"{API_URL}/generate_music")
    music_data = response.json()
    await update.message.reply_text(f"Generated Music: {music_data['music_url']}")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate_music", generate_music))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
