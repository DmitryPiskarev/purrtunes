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
    print(f"Received arguments: {context.args}")

    # Ensure correct number of arguments are passed
    if len(context.args) != 6:  # Adjusted to expect 7 arguments now
        await update.message.reply_text(
            f"Incorrect number of arguments. Expected 7, but received {len(context.args)}.\n"
            "Please provide the owner address, symbol, title, lyrics, meta, music URL.\n"
            "Example: /generate_music 0x123456789 Symbol Title Lyrics Meta http://music.com"
        )
        return

    # Extract user input
    owner_address = context.args[0]
    symbol = context.args[1]
    title = context.args[2]
    lyrics = context.args[3]
    meta = context.args[4]
    music_url = context.args[5]
    # svg_template = context.args[6]

    # Hardcoded SVG template with title dynamically inserted
    svg_template = f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <!-- Background Circle -->
        <circle cx="100" cy="100" r="90" fill="#3498db" stroke="#2980b9" stroke-width="5"/>
        
        <!-- Text in the center -->
        <text x="50%" y="50%" font-size="20" text-anchor="middle" fill="#ffffff" dy=".3em">{title}</text>
    </svg>'''

    # Log the received data for debugging purposes
    logger.info(f"Received data: owner_address={owner_address}, symbol={symbol}, title={title}, "
                f"lyrics={lyrics}, meta={meta}, music_url={music_url}, svg_template={svg_template}")

    # Send a POST request to FastAPI to generate the music
    try:
        response = requests.post(API_URL, json={
            "owner_address": owner_address,
            "symbol": symbol,
            "title": title,
            "lyrics": lyrics,
            "meta": meta,
            "music_url": music_url,
            "svg_template": svg_template  # Include the hardcoded SVG template in the request
        }, timeout=60)  # Timeout after 60 seconds

        # Handle successful response
        if response.status_code == 200:
            music_data = response.json()
            music_url = music_data.get("music_url", "No music URL generated.")
            await update.message.reply_text(f"Generated Music: {music_url}")

        else:
            logger.error(f"Failed to generate music. Response code: {response.status_code}, Response: {response.text}")
            await update.message.reply_text("Failed to generate music. Please try again later.")

    except requests.exceptions.Timeout:
        logger.error("Request to FastAPI timed out.")
        await update.message.reply_text("Request timed out. Please try again later.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        await update.message.reply_text(f"An error occurred: {e}")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("generate_music", generate_music))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
