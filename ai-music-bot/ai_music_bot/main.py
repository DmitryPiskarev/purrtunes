import subprocess
import json
from fastapi import FastAPI
from pydantic import BaseModel
import logging
import requests
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Data models
class MusicRequest(BaseModel):
    owner_address: str
    image_url: str
    music_url: str


# Function to deploy the contract and get the contract address
def deploy_contract() -> str:
    try:
        # Run the cargo deploy command
        result = subprocess.run(
            ["cargo", "stylus", "deploy", f"--endpoint={os.getenv('RPC_URL', 'http://localhost:8547')}",
             f"--private-key={os.getenv('PRIVATE_KEY')}"],
            capture_output=True, text=True
        )
        # Find the contract address from the output
        output = result.stdout
        logger.info(f"Deploy command output: {output}")

        # Extract the contract address from the output
        for line in output.splitlines():
            if "deployed code at address:" in line:
                contract_address = line.split(":")[1].strip()
                logger.info(f"Contract deployed at: {contract_address}")
                return contract_address

        # In case no contract address was found
        raise ValueError("Contract address not found in deployment output.")

    except Exception as e:
        logger.error(f"Error deploying contract: {e}")
        raise e


# Function to initialize the contract with the provided owner address, image URL, and music URL
def initialize_contract(owner_address: str, image_url: str, music_url: str, contract_address: str) -> str:
    try:
        # Run the cast send command to initialize the contract
        result = subprocess.run(
            [
                "cast", "send", contract_address,
                "--rpc-url", os.getenv("RPC_URL", "http://localhost:8547"),
                "--private-key", os.getenv("PRIVATE_KEY"),
                "initializeContract(address,string,string)",
                owner_address,
                image_url,
                music_url
            ],
            capture_output=True, text=True
        )
        # Log the output from the cast send command
        output = result.stdout
        logger.info(f"Initialize contract command output: {output}")

        # Look for success message in the output
        if "success" in output.lower():
            return music_url  # Return the music URL if successful

        raise ValueError("Failed to initialize contract with provided parameters.")

    except Exception as e:
        logger.error(f"Error initializing contract: {e}")
        raise e


@app.post("/generate_music")
def generate_music(request: MusicRequest):
    try:
        # Step 1: Deploy the contract and get the address
        contract_address = deploy_contract()

        # Step 2: Initialize the contract with user-provided data
        music_url = initialize_contract(
            owner_address=request.owner_address,
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
