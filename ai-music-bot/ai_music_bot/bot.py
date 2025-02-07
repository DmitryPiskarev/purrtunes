import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

from dotenv import load_dotenv
import os
import base64
from utils import upload_to_ipfs

load_dotenv()


TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = f"{os.getenv('BASE_URL')}/generate_music"  # FastAPI URL for music generation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Storing temp meta data
user_metadata = {}


# Command for starting the bot
async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("🎵 Welcome to AI Music Bot! Upload an audio file to begin.")


async def upload_music(update: Update, context: CallbackContext) -> None:
    """Handles music file uploads."""
    message = update.message
    file = message.audio or message.voice or message.document

    if not file:
        await message.reply_text("❌ Please upload an audio file (MP3, WAV, or voice message).")
        return

    user_id = message.from_user.id
    user_metadata[user_id] = {"file_id": file.file_id}

    await message.reply_text("✅ Audio received! Now, set:\n"
                             "🎶 Lyrics: `/set_lyrics <your lyrics>`\n"
                             "🎵 Title: `/set_title <song title>`\n"
                             "💰 Address: `/set_address <wallet>`")


async def set_lyrics(update: Update, context: CallbackContext) -> None:
    """Stores song lyrics."""
    user_id = update.message.from_user.id
    if user_id not in user_metadata:
        await update.message.reply_text("❌ Please upload music first.")
        return

    lyrics = " ".join(context.args)
    if not lyrics:
        await update.message.reply_text("⚠️ Usage: `/set_lyrics <your lyrics>`")
        return

    user_metadata[user_id]["lyrics"] = lyrics
    await update.message.reply_text("✅ Lyrics set!")


async def set_title(update: Update, context: CallbackContext) -> None:
    """Stores song title."""
    user_id = update.message.from_user.id
    if user_id not in user_metadata:
        await update.message.reply_text("❌ Please upload music first.")
        return

    title = " ".join(context.args)
    if not title:
        await update.message.reply_text("⚠️ Usage: `/set_title <song title>`")
        return

    user_metadata[user_id]["title"] = title
    await update.message.reply_text("✅ Title set!")


async def set_address(update: Update, context: CallbackContext) -> None:
    """Stores wallet address."""
    user_id = update.message.from_user.id
    if user_id not in user_metadata:
        await update.message.reply_text("❌ Please upload music first.")
        return

    address = " ".join(context.args)
    if not address.startswith("0x") or len(address) != 42:
        await update.message.reply_text("⚠️ Invalid address! Example: `/set_address 0x123...456`")
        return

    user_metadata[user_id]["owner_address"] = address
    await update.message.reply_text("✅ Address set!")


async def verify_data(update: Update, context: CallbackContext) -> None:
    """Displays stored metadata for user confirmation."""
    user_id = update.message.from_user.id
    if user_id not in user_metadata or "file_id" not in user_metadata[user_id]:
        await update.message.reply_text("❌ Please upload a music file first.")
        return

    data = user_metadata[user_id]
    missing = [key for key in ["title", "lyrics", "owner_address"] if key not in data]

    if missing:
        await update.message.reply_text(f"⚠️ Missing data: {', '.join(missing)}")
        return

    verification_msg = (
        f"✅ **Verify Your Data:**\n\n"
        f"🎵 **Title:** {data['title']}\n"
        f"🎶 **Lyrics:** {data['lyrics']}\n"
        f"💰 **Address:** `{data['owner_address']}`\n\n"
        f"🚀 If correct, use `/generate_music` to mint your NFT!"
    )
    await update.message.reply_text(verification_msg, parse_mode="Markdown")


# Command to generate music (interact with FastAPI)
async def generate_music(update: Update, context: CallbackContext) -> None:
    """Sends the final request to mint NFT."""
    user_id = update.message.from_user.id
    if user_id not in user_metadata or "file_id" not in user_metadata[user_id]:
        await update.message.reply_text("❌ Please upload a music file first.")
        return

    try:
        # Download music from Telegram
        file_id = user_metadata[user_id]["file_id"]
        file = await context.bot.get_file(file_id)
        file_path = file.file_path

        response = requests.get(file_path)
        if response.status_code != 200:
            raise Exception("Failed to download the file from Telegram.")

        local_file_path = f"/tmp/{file_id}.oga"  # Save the file locally
        with open(local_file_path, "wb") as f:
            f.write(response.content)  # Save the downloaded file

        # Now upload the **local file** to IPFS
        music_data = upload_to_ipfs(local_file_path)

        print(f"\n\n{music_data}\n\n")
        # response = requests.get(file_path)
        # music_data = base64.b64encode(response.content).decode()

        # Generate metadata
        user_metadata[user_id]["meta"] = "Auto-generated metadata"

        # Generate SVG template
        title = user_metadata[user_id]["title"]
        svg_template = f'''<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <circle cx="100" cy="100" r="90" fill="#3498db" stroke="#2980b9" stroke-width="5"/>
            <text x="50%" y="50%" font-size="20" text-anchor="middle" fill="#ffffff" dy=".3em">{title}</text>
        </svg>'''

        data = {
            "owner_address": user_metadata[user_id]["owner_address"],
            "symbol": "MUSICNFT",
            "title": title,
            "lyrics": user_metadata[user_id]["lyrics"],
            "meta": user_metadata[user_id]["meta"],
            "music_data": music_data,
            "svg_template": svg_template
        }

        # Send to FastAPI
        response = requests.post(API_URL, json=data, timeout=60)

        if response.status_code == 200:
            music_data = response.json()

            # Extract NFT data
            contract_address = music_data.get("contract_address", "N/A")
            user_metadata[user_id]["nft_address"] = contract_address  # Save contract address

            # Extract relevant NFT data
            nft_details = (
                f"✅ **Music NFT Created!** 🎶\n\n"
                f"📜 **Transaction Hash:** `{music_data.get('transaction_hash', 'N/A')}`\n"
                f"🔢 **Block Number:** `{music_data.get('block_number', 'N/A')}`\n"
                f"🔗 **Block Hash:** `{music_data.get('block_hash', 'N/A')}`\n"
                f"🏛 **Contract Address:** `{contract_address}`\n"
                f"⛽ **Gas Used:** `{music_data.get('gas_used', 'N/A')}`\n"
            )

            await update.message.reply_text(nft_details, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ Failed to generate music NFT. Try again later.")

    except Exception as e:
        logger.error(f"Error in generate_music: {e}")
        await update.message.reply_text("❌ An error occurred while processing your request.")


async def get_nft(update: Update, context: CallbackContext) -> None:
    """Fetches NFT metadata from the contract."""
    user_id = update.message.from_user.id
    if user_id not in user_metadata or "nft_address" not in user_metadata[user_id]:
        await update.message.reply_text("❌ No NFT found. Use `/generate_music` first.")
        return

    contract_address = user_metadata[user_id]["nft_address"]
    nft_api_url = f"{os.getenv('BASE_URL')}/nft_metadata/{contract_address}"

    try:
        response = requests.get(nft_api_url, timeout=30)
        if response.status_code == 200:
            nft_data = response.json()

            nft_info = (
                f"🎵 **Your NFT Metadata:**\n\n"
                f"📛 **Title:** {nft_data.get('name', 'N/A')}\n"
                f"📜 **Lyrics:** {nft_data.get('lyrics', 'N/A')}\n"
                f"📝 **Description:** {nft_data.get('description', 'N/A')}\n"
                f"🎨 **NFT Image:** [Click to View]({nft_data.get('image', '')})\n"
                f"🎶 **Music:** [Listen Here]({nft_data.get('music', '')})\n"
            )

            await update.message.reply_text(nft_info, parse_mode="Markdown", disable_web_page_preview=False)

        else:
            await update.message.reply_text("⚠️ Failed to fetch NFT data.")

    except Exception as e:
        logger.error(f"Error fetching NFT metadata: {e}")
        await update.message.reply_text("❌ An error occurred while retrieving your NFT.")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.AUDIO | filters.Document.MP3 | filters.VOICE, upload_music))
    app.add_handler(CommandHandler("set_lyrics", set_lyrics))
    app.add_handler(CommandHandler("set_title", set_title))
    app.add_handler(CommandHandler("set_address", set_address))
    app.add_handler(CommandHandler("verify_data", verify_data))
    app.add_handler(CommandHandler("generate_music", generate_music))
    app.add_handler(CommandHandler("get_nft", get_nft))

    logger.info("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
