import logging
import json
import base64
from fastapi import HTTPException
import asyncio
from dotenv import load_dotenv
import os
import requests

load_dotenv()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_nft_metadata_from_contract(contract_address: str):
    """Calls the smart contract to get NFT metadata using cast call."""
    try:
        # Validate contract address
        if not contract_address.startswith("0x"):
            raise ValueError("Invalid contract address.")

        # Command to fetch tokenURI
        command = [
            "cast", "call", contract_address,
            "--rpc-url", os.getenv("RPC_URL", "http://localhost:8547"),
            "tokenURI(uint256)", "1"  # Token ID is assumed to be 1
        ]

        logger.info(f"Fetching NFT metadata: {command}")

        # Execute the command asynchronously
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        output = stdout.decode().strip() + stderr.decode().strip()

        if not output:
            raise HTTPException(status_code=500, detail="Failed to fetch NFT metadata.")

        # Extract the base64-encoded JSON metadata
        metadata_base64 = output.split("data:application/json;base64,")[-1].strip()
        metadata_json = base64.b64decode(metadata_base64).decode()

        return json.loads(metadata_json)

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
