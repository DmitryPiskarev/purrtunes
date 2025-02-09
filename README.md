
# PurrTunes
### 🎤 MVP 1.0
This MVP 1.0 PurrTunes (https://t.me/purrtunes_bot) is a Telegram Bot that allows you to mint music NFTs. You can add music as MP3, WAV, or even record a voice message! The artwork for each NFT is randomly generated with the title of the song displayed in the center, paired with a cosmic SVG background.
- [NOTE] To test the concept I'm utilizing mock AI-agents for music image and lyrics generation.
- Arbitrum Testnode for NFT issuance
- Privy for users onboarding (APP ID: cm6wjk3u80242hhau1lxi1xqa)
- Pinata to store music

### Features
- **Mint NFTs**: Allows users to mint music NFTs based on their uploaded music files.
- **Music Formats Supported**: MP3, WAV, and voice 🎤 message recordings.
- **Randomized Artwork**: Cosmic-themed SVG background with song title in the center.
- **NFT Minting**: Powered by Arbitrum's Stylus + Rust smart contract.
- **User Onboarding**: Powered by Privy, which allows users to log in with existing wallets (like MetaMask) or via email. Privy will generate a wallet address for users without one.
- **Easy Setup**: Use a simple local setup with FastAPI backend and Next.js frontend.

---
## <img src="ah.png" alt="Project Logo" width="30"> Agentic Ethereum Partners techs
![Project Logo](Arbitrum.png)
<img src="Privy.png" alt="Privy" width="208">

---

### Technology Stack
- **Backend**: FastAPI
- **Bot**: Telegram Bot API (Python)
- **Frontend**: Next.js (Privy integration for user onboarding)
- **Blockchain**: Arbitrum's Stylus + Rust Smart Contract for minting NFTs
- **Hosting**: Local development hosted with Ngrok for testing

---

### Contract Code

The contract to mint NFTs is written in Rust, utilizing Arbitrum's Stylus framework.

```rust
#[entrypoint]
#[storage]
pub struct Contract {
    /// The NFT song owner address
    owner: StorageAddress,

    /// The symbol of the song NFT
    symbol: StorageString,

    /// The name / title of the NFT
    title: StorageString,

    /// Lyrics of the song
    lyrics: StorageString,

    /// Additional meta data
    meta: StorageString,

    /// URL to the music file of the NFT
    music_data: StorageString,

    /// Music image
    svg_template: StorageString,
}
```

The contract is currently set up to use a test node RPC URL (`http://localhost:8547`) with a pre-funded development account, making it easy to mint NFTs without worrying about gas fees.

---

---

### 🎵🚀🎤 MVP 1.5 Future Plans for PurrTunes Bot 🎵🚀🎤
🚀 Music, Lyrics, and Image Generation with AI
Leverage the power of AI agents to autonomously generate music, lyrics, and album artwork. This will enhance the creative possibilities for our users and allow for even more dynamic NFTs.

🔑 Private Key Support & RPC Upgrade
Provide users with the ability to use their own private keys instead of relying on the testnet RPC. This will allow interactions with the official Arbitrum Sepolia Rollup network, providing greater flexibility and security.
RPC URL: Arbitrum Sepolia RPC

👥 Enhanced User Management
Implement improved user management systems, allowing for a better onboarding experience, account recovery, and other features that ensure users’ smooth journey with the bot.

🎶 Music Mixing and Mastering with AI
Allow users to send raw music tracks and have them processed by our AI, providing high-quality mixing and mastering services. This will elevate user-created music and make it ready for professional-level releases.

---

### Project Structure

```bash
purrtunes
├── ai-music-bot
│   ├── ai_music_bot (FastAPI backend + Telegram bot logic)
│   ├── purrtunes_contract (Arbitrum smart contract)
│   ├── privy_auth_frontend (Next.js frontend for Privy onboarding)
├── nitro-devnode (Pre-funded dev node for Arbitrum)
```

---

### Getting Started

1. **Create a `.env` file**  
In the root directory, create a `.env` file with the following content:

```env
TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
BASE_URL=http://127.0.0.1:8000
RPC_URL=http://localhost:8547
PRIVATE_KEY=YOUR_PRIVATE_KEY
PINATA_API_KEY=YOUR_PINATA_API_KEY
PINATA_API_SECRET=YOUR_PINATA_API_SECRET
PRIVY_APP_ID=YOUR_PRIVY_APP_ID
PRIVY_APP_SECRET=YOUR_PRIVY_APP_SECRET
```

2. **Poetry Package Management**  
Poetry is used for dependency management. Install it if you haven’t already, then follow these steps:

```bash
cd ai-music-bot
poetry --version # Make sure poetry is installed
export PATH="/Library/Application Support/poetry/bin:$PATH" # For UNIX users
poetry install
poetry shell
```

3. **Start FastAPI Backend**  
The backend is powered by FastAPI. Start the backend with the following commands:

```bash
cd ai-music-bot
activate poetry shell
poetry run uvicorn ai_music_bot.main:app --reload --host 0.0.0.0 --port 8000
```

4. **Start Telegram Bot**  
Run the Telegram bot script:

```bash
cd ai-music-bot
activate poetry shell
poetry run python ai_music_bot/bot.py
```

5. **Start Frontend**  
The frontend handles user authentication via Privy. Start the frontend with:

```bash
# Navigate to the Privy frontend directory
cd privy_auth_frontend
npm install
npm run dev
```

- Create a `.env.local` file with the following variables:

```env
NEXT_PUBLIC_PRIVY_APP_ID=YOUR_PRIVY_APP_ID
NEXT_PUBLIC_TG_ID=YOUR_TELEGRAM_BOT_ID
```

6. **Start Nitro Devnode (Arbitrum Test Node)**  
To test the minting functionality, we use Arbitrum’s pre-funded devnode. Install and start the devnode:

```bash
# Clone the Nitro devnode repository
git clone https://github.com/OffchainLabs/nitro-devnode.git
cd nitro-devnode

# Launch the devnode
./run-dev-node.sh
```

7. **Use Pinata to Store Music Files**  
For storing music files, use Pinata. Set up your account on [Pinata](https://pinata.cloud/) and use the provided `PINATA_API_KEY` and `PINATA_API_SECRET` for uploading files.

---

### Hosting

The app is currently hosted using Ngrok, so you can access it via a local tunnel:

- **Web Interface (localhost)**: `http://127.0.0.1:4040`
- **Ngrok Forwarding URL**: `https://d02c-81-177-214-101.ngrok-free.app -> http://localhost:3000`

---

### How to Use PurrTunes

1. **Login**: Users can log in via MetaMask or using email via Privy.
2. **Generate Music**: Use the Telegram bot or frontend to generate music NFTs.
3. **Mint NFT**: Once music is generated, mint the NFT through the backend. The bot will handle minting using the smart contract.
4. **View NFT**: Use `/get_nft` in the Telegram bot to fetch metadata and view the generated NFT.

---

### Troubleshooting

If you run into any issues, ensure the following:
- Make sure Poetry installed
- The correct `.env` and `.env.local` file configuration.
- The Nitro devnode is running for testing.
- Ensure that the Telegram bot token and Privy credentials are correct.

For any bugs or issues, please create an issue in the [GitHub repository](https://github.com/DmitryPiskarev/purrtunes).

---

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
