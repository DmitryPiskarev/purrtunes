import subprocess
import json
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
import logging
import requests
from dotenv import load_dotenv
import os
import re

load_dotenv()

app = FastAPI()

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
    image_url: str
    music_url: str
    svg_template: str


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
        music_url: str,
        svg_template: str,
        contract_address: str,
) -> str:
    try:
        contract_address = contract_address.strip()  # Remove extra spaces
        contract_address = contract_address.replace('\x1b[38;5;183;1m', '').replace('\x1b[0;0m',
                                                                                    '')  # Strip color formatting

        # Ensure the address starts with '0x' and is valid
        if not contract_address.startswith('0x'):
            raise ValueError("Invalid contract address. Must start with '0x'.")

        # Command components as a list of arguments
        command = [
            "cast", "send", contract_address,
            "--rpc-url", os.getenv("RPC_URL", "http://localhost:8547"),
            "--private-key", os.getenv("PRIVATE_KEY"),
            "initialize_contract(address,string,string,string,string,string,string)",  # Adjusted parameters
            owner_address,
            symbol,  # symbol to be passed dynamically
            title,  # title to be passed dynamically
            lyrics,  # lyrics to be passed dynamically
            meta,  # meta to be passed dynamically
            music_url,  # music_url to be passed dynamically
            svg_template  # svg_template to be passed dynamically (string)
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
            block_hush = None

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
                    block_hush = line.strip().split(" ")[-1].strip()

                # # Extract contractAddress (if provided)
                # elif "contractAddress" in line:
                #     contract_address = line.strip().split(" ")[-1].strip()

                elif "gasUsed" in line:
                    gas_used = line.strip().split(" ")[-1].strip()

            # Check if we have all the required data
            if transaction_hash and block_number:
                # Return the extracted information in a formatted string
                return (
                    f"\nTransaction Hash: {transaction_hash}\n"
                    f"Block Number: {block_number}\n"
                    f"Block Hush: {block_hush}\n"
                    f"Contract Address: {contract_address if contract_address else 'Not provided'}\n"
                    f"Deployed at: {contract_address}\n"
                    f"Gas used: {gas_used}"
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
            name=request.name,
            description=request.description,
            image_url=request.image_url,
            music_url=request.music_url,
            contract_address=contract_address
        )

        return {"music_url": music_url}

    except Exception as e:
        logger.error(f"Error generating music: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
