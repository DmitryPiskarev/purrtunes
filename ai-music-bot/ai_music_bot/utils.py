import logging
import json
import base64
from fastapi import HTTPException
import asyncio
from dotenv import load_dotenv
import os
import requests
import binascii
from eth_abi import decode
import random

load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sanitize_data(data: str) -> str:
    # Replace newline characters with a placeholder (e.g., '\n')
    return data.replace("\n", "\\n")


def restore_data(sanitized_data: str) -> str:
    # Replace the placeholder '\\n' back to actual newlines
    return sanitized_data.replace("\\n", "\n")


async def get_nft_metadata_from_contract(contract_address: str):
    """Calls the smart contract to get NFT metadata using cast call and decodes ABI-encoded response."""
    try:
        # Validate contract address
        if not contract_address.startswith("0x"):
            raise ValueError("Invalid contract address.")

        # Command to fetch tokenURI
        command = [
            "cast", "call", contract_address,
            "--rpc-url", os.getenv("RPC_URL", "http://localhost:8547"),
            "--private-key", os.getenv("PRIVATE_KEY"),
            "tokenURI(uint256)", "1"
        ]

        logger.info(f"Fetching NFT metadata: {command}")

        # Execute the command asynchronously
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        raw_output = stdout.decode().strip() + stderr.decode().strip()

        logger.info(f"Raw NFT Metadata Response: {raw_output}")

        if not raw_output:
            raise HTTPException(status_code=500, detail="Failed to fetch NFT metadata.")

        # Step 1: Remove "0x" prefix if present
        if raw_output.startswith("0x"):
            raw_output = raw_output[2:]

        # Step 2: Convert hex string to bytes
        response_bytes = binascii.unhexlify(raw_output)

        # Step 3: Decode the ABI-encoded `string` response
        decoded_data = decode(["string"], response_bytes)[0]

        # Step 4: Extract Base64 JSON part and fix padding
        metadata_base64 = decoded_data.replace("data:application/json;base64,", "").strip()
        missing_padding = len(metadata_base64) % 4
        if missing_padding:
            metadata_base64 += "=" * (4 - missing_padding)

        # Step 5: Decode Base64 JSON
        metadata_json = base64.b64decode(metadata_base64).decode()
        metadata_dict = json.loads(metadata_json)

        logging.info(f"\n\nnft_data: {metadata_dict}\n\n")

        metadata_dict["lyrics"] = restore_data(metadata_dict["lyrics"])

        return metadata_dict

    except Exception as e:
        logger.error(f"Error fetching NFT metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def upload_to_ipfs(file_path):
    # Load your Pinata API key and secret from environment variables for security
    pinata_api_key = os.getenv("PINATA_API_KEY")
    pinata_api_secret = os.getenv("PINATA_API_SECRET")

    if not pinata_api_key or not pinata_api_secret:
        raise ValueError("Pinata API key and secret are required")

    try:
        with open(file_path, "rb") as f:
            # Prepare the headers with the correct API key and secret
            headers = {
                "pinata_api_key": pinata_api_key,
                "pinata_secret_api_key": pinata_api_secret
            }

            # Send the file to Pinata
            response = requests.post(
                "https://api.pinata.cloud/pinning/pinFileToIPFS",
                files={"file": f},
                headers=headers
            )

            # Check if the request was successful
            if response.status_code == 200:
                ipfs_hash = response.json().get("IpfsHash")
                return f"ipfs://{ipfs_hash}"
            else:
                # Handle errors or unsuccessful response
                raise Exception(f"Error uploading file to IPFS: {response.text}")

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def generate_cosmic_svg(title: str) -> str:
    """Generates a deep-space cosmic NFT with stars, a spaceship, a random drawn cat, and glowing effects."""
    width, height = 400, 400

    # Random deep-space background gradient
    colors = ["#0b0033", "#1a0751", "#2c0e78", "#3f179e", "#5125c2", "#030214", "#9400b2", "#4e1659", "#009ed3",
              "#d30070", "#1e57c9", '#7c0909']
    bg_color1, bg_color2 = random.sample(colors, 2)

    # Generate stars (mix of small sharp ones + blurred ones)
    stars = ""
    for _ in range(random.randint(50, 100)):  # 50 to 100 stars
        x, y = random.randint(5, width-5), random.randint(5, height-5)
        size = random.randint(1, 3)
        opacity = round(random.uniform(0.2, 1.0), 2)
        blur = random.choice(["0", "5", "10"])  # Some stars blurred
        stars += f'<circle cx="{x}" cy="{y}" r="{size}" fill="white" opacity="{opacity}" filter="url(#blur{blur})"/>'

    # Add a spaceship with a glowing engine
    spaceship_x = random.randint(50, 330)
    spaceship_y = random.randint(50, 350)
    spaceship_color = random.choice(["silver", "gray", "darkgray", "lightblue"])

    spaceship = f'''
        <polygon points="{spaceship_x},{spaceship_y} {spaceship_x+20},{spaceship_y+40} {spaceship_x-20},{spaceship_y+40}"
            fill="{spaceship_color}" stroke="white" stroke-width="1" opacity="0.1"/>
        <circle cx="{spaceship_x}" cy="{spaceship_y+50}" r="8" fill="orange" opacity="0.8"/>
        <circle cx="{spaceship_x}" cy="{spaceship_y+50}" r="12" fill="yellow" opacity="0.4"/>
    '''

    # Randomly draw a cat above the spaceship (drawn in SVG)
    cat_x = random.randint(spaceship_x-30, spaceship_x+30)
    cat_y = spaceship_y - random.randint(30, 60)  # Place cat a bit above the spaceship
    cat = f'''
    <!-- Drawn Cat -->
    <g transform="translate({cat_x}, {cat_y})">
        <circle cx="0" cy="0" r="10" fill="gray" /> <!-- Cat's head -->
        <circle cx="-7" cy="-5" r="2" fill="white" /> <!-- Left eye -->
        <circle cx="7" cy="-5" r="2" fill="white" /> <!-- Right eye -->
        <circle cx="-7" cy="-5" r="1" fill="black" /> <!-- Left eye pupil -->
        <circle cx="7" cy="-5" r="1" fill="black" /> <!-- Right eye pupil -->
        <path d="M -4,3 Q 0,7 4,3" stroke="black" fill="transparent" /> <!-- Cat's mouth -->
        <path d="M -7,-2 Q -9,0 -7,2" stroke="black" fill="transparent" /> <!-- Left whisker -->
        <path d="M 7,-2 Q 9,0 7,2" stroke="black" fill="transparent" /> <!-- Right whisker -->
        <path d="M -3,-3 Q -5,-5 -6,-3" stroke="black" fill="transparent" /> <!-- Left ear -->
        <path d="M 3,-3 Q 5,-5 6,-3" stroke="black" fill="transparent" /> <!-- Right ear -->
    </g>
    '''

    # Shooting stars (random streaks)
    shooting_stars = ""
    for _ in range(random.randint(1, 3)):  # 1 to 3 shooting stars
        x1, y1 = random.randint(50, width-50), random.randint(50, height-50)
        x2, y2 = x1 + random.randint(30, 60), y1 - random.randint(30, 60)
        shooting_stars += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="white" stroke-width="2" opacity="0.7"/>'

    # Song title in the center with bigger font and more spacing (capital letters, and letter-spacing)
    # Determine base font size
    max_width = 400  # Adjust based on your SVG width
    base_font_size = 40  # Default font size
    char_width = 25  # Estimated width per character with spacing

    # Calculate font size based on title length
    title_spaced = " ".join(title.upper())  # Adds space between each letter
    title_length = len(title_spaced) * char_width

    if title_length > max_width:
        font_size = max(20, base_font_size * (max_width / title_length))  # Scale down, but not below 20px
    else:
        font_size = base_font_size  # Keep default size

    text = f'''
    <text x="50%" y="50%" font-size="{font_size}" text-anchor="middle" fill="white" dy=".3em" font-family="Lato, Arial, sans-serif" letter-spacing="5" opacity="0.9">
        {title_spaced}
    </text>
    '''

    # Full SVG with filters & deep-space effects
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <radialGradient id="bgGradient" cx="50%" cy="50%" r="100%">
                <stop offset="0%" stop-color="{bg_color1}" />
                <stop offset="100%" stop-color="{bg_color2}" />
            </radialGradient>
            <filter id="blur5"><feGaussianBlur stdDeviation="1"/></filter>
            <filter id="blur10"><feGaussianBlur stdDeviation="2"/></filter>
        </defs>
        <rect width="100%" height="100%" fill="url(#bgGradient)" />
        {stars}
        {shooting_stars}
        {spaceship}
        {text}
    </svg>'''

    return svg


# Function to retrieve user data by user_id from the FastAPI endpoint
def get_user_data(user_id: str):
    url = f"{os.getenv('BASE_URL', 'http://127.0.0.1:8000')}/get_user/{user_id}"  # Replace with your FastAPI server URL
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()  # Return the user data from the API
        else:
            return {"status": "error", "message": "User data not found."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}
