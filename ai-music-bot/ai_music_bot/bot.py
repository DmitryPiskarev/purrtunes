import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

from dotenv import load_dotenv
import os

load_dotenv()


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"{os.getenv('BASE_URL')}/generate_music"  # FastAPI URL for music generation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Command for starting the bot
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome to AI Music Bot! Type /generate_music to create a song.")


# Command to generate music (interact with FastAPI)
async def generate_music(update: Update, context: CallbackContext) -> None:
    # Get the user input (owner_address, image_url, and music_url)
    if len(context.args) != 3:
        await update.message.reply_text("Please provide the owner address, image URL, and music URL. Example: "
                                        "/generate_music 0x123456789 ...")
        return

    owner_address = context.args[0]
    image_url = context.args[1]
    music_url = context.args[2]

    # Send a POST request to FastAPI to generate the music
    response = requests.post(API_URL, json={
        "owner_address": owner_address,
        "image_url": image_url,
        "music_url": music_url
    })

    if response.status_code == 200:
        music_data = response.json()
        music_url = music_data.get("music_url", "No music URL generated.")
        await update.message.reply_text(f"Generated Music: {music_url}")
    else:
        await update.message.reply_text("Failed to generate music. Try again later.")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate_music", generate_music))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
