import subprocess
import json
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import requests
from dotenv import load_dotenv
import os
import re
from datetime import datetime
import base64
from .utils import get_nft_metadata_from_contract

load_dotenv()

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Add CORSMiddleware to the app
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of origins that are allowed to access the API
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allow all headers
)

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Data models
class MusicRequest(BaseModel):
    owner_address: str
    symbol: str
    title: str
    lyrics: str
    meta: str
    music_data: str
    svg_template: str


class MusicNFTResponse(BaseModel):
    transaction_hash: str
    block_number: int
    block_hash: str
    contract_address: str
    deployed_at: str
    gas_used: int


# Function to deploy the contract and get the contract address
async def deploy_contract() -> str:
    try:
        project_dir = os.path.join(os.getcwd(), "purrtunes_contract")
        # Run the cargo deploy command asynchronously
        process = await asyncio.create_subprocess_exec(
            "cargo", "stylus", "deploy",
            f"--endpoint={os.getenv('RPC_URL', 'http://localhost:8547')}",
            f"--private-key={os.getenv('PRIVATE_KEY')}",
            cwd=project_dir,  # Running from contract directory, because Cargo.toml resides there
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Timeout settings
        timeout = 300  # Max wait time in seconds
        start_time = asyncio.get_event_loop().time()

        while True:
            if process.returncode is not None:
                break  # Process finished
            if asyncio.get_event_loop().time() - start_time > timeout:
                process.kill()
                raise TimeoutError("Contract deployment timed out.")

            await asyncio.sleep(5)  # Check every 5 seconds

        # Capture the output after deployment
        stdout, stderr = await process.communicate()
        output = stdout.decode() + stderr.decode()
        logger.info(f"Deploy command output: {output}")

        # Extract the contract address from the output
        for line in output.splitlines():
            if "deployed code at address:" in line:
                contract_address = line.split(":")[1].strip()
                logger.info(f"Contract deployed at: {contract_address}")
                return contract_address

        raise ValueError("Contract address not found in deployment output.")

    except Exception as e:
        logger.error(f"Error deploying contract: {e}")
        raise e


# Function to initialize the contract with the provided owner address, image URL, and music URL
async def initialize_contract(
        owner_address: str,
        symbol: str,
        title: str,
        lyrics: str,
        meta: str,
        music_data: str,
        svg_template: str,
        contract_address: str,
):
    try:
        contract_address = contract_address.strip()  # Remove extra spaces
        contract_address = contract_address.replace('\x1b[38;5;183;1m', '').replace('\x1b[0;0m',
                                                                                    '')  # Strip color formatting

        # Base64 encode the SVG
        svg_encoded = base64.b64encode(svg_template.encode()).decode()
        lyrics_encoded = base64.b64encode(lyrics.encode()).decode()
        meta_encoded = base64.b64encode(meta.encode()).decode()

        # Ensure the address starts with '0x' and is valid
        if not contract_address.startswith('0x'):
            raise ValueError("Invalid contract address. Must start with '0x'.")

        # Command components as a list of arguments
        command = [
            "cast", "send", contract_address,
            "--rpc-url", os.getenv("RPC_URL", "http://localhost:8547"),
            "--private-key", os.getenv("PRIVATE_KEY"),
            "initializeContract(address,string,string,string,string,string,string)",  # Adjusted parameters
            owner_address,
            symbol,
            title,
            lyrics_encoded,
            meta_encoded,
            music_data,
            svg_encoded
        ]

        print(f"\n\n\n {command} \n\n\n")

        # Run the cast send command asynchronously
        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()
        output = stdout.decode() + stderr.decode()
        logger.info(f"Initialize contract command output: {output}")

        try:
            # Split the output by lines
            lines = output.splitlines()

            # Initialize variables to store extracted data
            transaction_hash = None
            block_number = None
            gas_used = None
            block_hash = None

            # Iterate over each line to extract relevant information
            for line in lines:
                # Extract transactionHash
                if "transactionHash" in line:
                    transaction_hash = line.strip().split(" ")[-1].strip()

                # Extract blockNumber
                elif "blockNumber" in line:
                    block_number = line.strip().split(" ")[-1].strip()

                # Extract blockHash
                elif "blockHash" in line:
                    block_hash = line.strip().split(" ")[-1].strip()

                # # Extract contractAddress (if provided)
                # elif "contractAddress" in line:
                #     contract_address = line.strip().split(" ")[-1].strip()

                elif "gasUsed" in line:
                    gas_used = line.strip().split(" ")[-1].strip()

            # Check if we have all the required data
            if transaction_hash and block_number:
                # Return the extracted information in a formatted string
                return MusicNFTResponse(
                    transaction_hash=transaction_hash,
                    block_number=block_number,
                    block_hash=block_hash,
                    deployed_at=str(datetime.now()),
                    contract_address=contract_address,
                    gas_used=gas_used
                )
            else:
                raise ValueError("Failed to extract required data.")

        except Exception as e:
            # Log any errors that occur during extraction
            logger.error(f"Error extracting contract data: {e}")
            raise e

    except Exception as e:
        logger.error(f"Error initializing contract: {e}")
        raise e


@app.post("/generate_music")
async def generate_music(request: MusicRequest):
    try:
        # Step 1: Deploy the contract asynchronously
        contract_address = await deploy_contract()

        # Step 2: Initialize the contract asynchronously
        music_url = await initialize_contract(
            owner_address=request.owner_address,
            symbol=request.symbol,
            title=request.title,
            lyrics=request.lyrics,
            meta=request.meta,
            music_data=request.music_data,
            svg_template=request.svg_template,
            contract_address=contract_address
        )

        return music_url

    except Exception as e:
        logger.error(f"Error generating music: {e}")
        return {"error": str(e)}


# A mock database to store linked wallets
linked_wallets = {}


# Define the request model
class LinkWalletRequest(BaseModel):
    user_id: str
    wallet_address: str


@app.post("/link_wallet")
async def link_wallet(request: LinkWalletRequest):
    user_id = request.user_id
    wallet_address = request.wallet_address

    # Check if the wallet address is already linked to another user
    if wallet_address in linked_wallets.values():
        raise HTTPException(
            status_code=400,
            detail="This wallet address is already linked to another user."
        )

    # Check if the user already has a linked wallet
    if user_id in linked_wallets:
        raise HTTPException(
            status_code=400,
            detail=f"User {user_id} already has a linked wallet."
        )

    # Simulating the process of linking a wallet (store it in the dictionary)
    linked_wallets[user_id] = wallet_address

    logger.info(f"Wallet {wallet_address} linked to user {user_id}")

    return {"status": "success", "message": "Wallet linked successfully!"}


# FastAPI route to get NFT metadata
@app.get("/nft_metadata/{contract_address}")
async def get_nft_metadata(contract_address: str):
    """Endpoint to fetch NFT metadata from the blockchain."""
    return await get_nft_metadata_from_contract(contract_address)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
