import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

from dotenv import load_dotenv
import os
import base64

load_dotenv()


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"{os.getenv('BASE_URL')}/generate_music"  # FastAPI URL for music generation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Storing temp meta data
user_metadata = {}


# Command for starting the bot
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("Welcome to AI Music Bot! Type /generate_music to create a song.")


async def upload_music(update: Update, context: CallbackContext) -> None:
    """
    Handles music file uploads, including voice messages, audio files, and documents.
    """
    message = update.message

    # Check for audio, voice, or document uploads
    file = None
    if message.audio:
        file = message.audio
    elif message.voice:  # 🔥 Now supports voice messages!
        file = message.voice
    elif message.document:
        file = message.document

    if not file:
        await message.reply_text("❌ Please upload an audio file (MP3, WAV, or voice message).")
        return

    # Store the file ID for later use
    file_id = file.file_id
    user_id = message.from_user.id

    # Save user data in a dictionary (assuming 'user_data' exists)
    user_metadata[user_id] = {"file_id": file_id}

    await message.reply_text("✅ Audio file received! Now enter metadata using:\n"
                             "`/set_metadata <owner_address> <symbol> <title> <lyrics> <meta>`")


async def set_metadata(update: Update, context: CallbackContext) -> None:
    """
    Collects metadata after the file is uploaded.
    """
    chat_id = update.message.chat_id

    if chat_id not in user_metadata or "file_id" not in user_metadata[chat_id]:
        await update.message.reply_text("Please upload a music file first.")
        return

    if len(context.args) != 5:
        await update.message.reply_text(
            "Incorrect number of arguments. Use:\n"
            "/set_metadata <owner_address> <symbol> <title> <lyrics> <meta>"
        )
        return

    # Store metadata
    user_metadata[chat_id].update({
        "owner_address": context.args[0],
        "symbol": context.args[1],
        "title": context.args[2],
        "lyrics": context.args[3],
        "meta": context.args[4]
    })

    await update.message.reply_text(
        "Metadata saved! Now, use /generate_music to finalize your music NFT."
    )


# Command to generate music (interact with FastAPI)
async def generate_music(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id

    if chat_id not in user_metadata or "file_id" not in user_metadata[chat_id]:
        await update.message.reply_text("❌ Please upload a music file first.")
        return

    try:
        # Retrieve file from Telegram
        file_id = user_metadata[chat_id]["file_id"]
        file = await context.bot.get_file(file_id)
        file_path = file.file_path

        # Download and encode to base64
        response = requests.get(file_path)
        music_data = base64.b64encode(response.content).decode()

        # Construct metadata
        svg_template = f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="100" r="90" fill="#3498db" stroke="#2980b9" stroke-width="5"/>
            <text x="50%" y="50%" font-size="20" text-anchor="middle" fill="#ffffff" dy=".3em">{user_metadata[chat_id]["title"]}</text>
        </svg>'''

        data = {
            "owner_address": user_metadata[chat_id]["owner_address"],
            "symbol": user_metadata[chat_id]["symbol"],
            "title": user_metadata[chat_id]["title"],
            "lyrics": user_metadata[chat_id]["lyrics"],
            "meta": user_metadata[chat_id]["meta"],
            "music_data": music_data,
            "svg_template": svg_template
        }

        # Send to FastAPI
        response = requests.post(API_URL, json=data, timeout=60)

        if response.status_code == 200:
            music_data = response.json()

            # Extract relevant NFT data from the API response
            transaction_hash = music_data.get("transaction_hash", "N/A")
            block_number = music_data.get("block_number", "N/A")
            block_hash = music_data.get("block_hash", "N/A")
            contract_address = music_data.get("contract_address", "N/A")
            deployed_at = music_data.get("deployed_at", "N/A")
            gas_used = music_data.get("gas_used", "N/A")

            # Format the message with all NFT details
            nft_details = (
                f"✅ **Music NFT Created!** 🎶\n\n"
                f"📜 **Transaction Hash:** `{transaction_hash}`\n"
                f"🔢 **Block Number:** `{block_number}`\n"
                f"🔗 **Block Hash:** `{block_hash}`\n"
                f"🏛 **Contract Address:** `{contract_address}`\n"
                f"📍 **Deployed At:** `{deployed_at}`\n"
                f"⛽ **Gas Used:** `{gas_used}`\n"
            )

            await update.message.reply_text(nft_details, parse_mode="Markdown")

        else:
            await update.message.reply_text("⚠️ Failed to generate music NFT. Try again later.")

    except Exception as e:
        logger.error(f"Error in generate_music: {e}")
        await update.message.reply_text("❌ An error occurred while processing your request.")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.MP3 | filters.VOICE, upload_music))
    app.add_handler(CommandHandler("set_metadata", set_metadata))
    app.add_handler(CommandHandler("generate_music", generate_music))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
