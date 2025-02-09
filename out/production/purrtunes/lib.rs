#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;
use stylus_sdk::{alloy_primitives::{Address, U256}, prelude::*};
use stylus_sdk::{alloy_sol_types::sol, evm};
use stylus_sdk::storage::{StorageAddress, StorageString};

/// Event emitted when a mint occurs
sol! {
    event Minted(address indexed owner);
    event LogMintingSuccess(string message); // Added custom logging event
}

#[entrypoint]
#[storage]
pub struct Contract {
    /// The NFT owner address
    owner: StorageAddress,

    /// The symbol of the NFT
    symbol: StorageString,

    /// The name of the NFT
    name: StorageString,

    /// The description of the NFT
    description: StorageString,

    /// The image URL of the NFT
    image_url: StorageString,

    /// The music file URL of the NFT
    music_url: StorageString,
}

#[public]
impl Contract {
    /// ERC-165 & ERC-721 Interface Support
    pub fn supports_interface(&self, interface: [u8; 4]) -> bool {
        matches!(interface, [0x01, 0xff, 0xc9, 0xa7] | [0x80, 0xac, 0x58, 0xcd] | [0x5b, 0x5e, 0x13, 0x9f])
    }

    /// Mint function: Mints the NFT to the specified address
    pub fn mint(&mut self, to: Address) {
        // Check if the NFT has already been minted
        assert!(self.owner.get() == Address::ZERO, "Already minted!");

        // Set the owner to the given address
        self.owner.set(to);

        // Emit the Minted event
        evm::log(Minted { owner: to });

        // Emit a custom log event indicating success
        evm::log(LogMintingSuccess { message: "Minting successful, owner set.".to_string() });
    }

    /// Get the symbol of the NFT (e.g., "PurrtunesNFT")
    pub fn symbol(&self) -> String {
        self.symbol.get_string()
    }

    /// Get the name of the NFT (e.g., "SONG NFT")
    pub fn name(&self) -> String {
        self.name.get_string()
    }

    /// Get the description of the NFT (e.g., "A unique, cat-inspired music NFT with dynamic visuals.")
    pub fn description(&self) -> String {
        self.description.get_string()
    }

    /// Balance check function to see if the provided owner holds the NFT (1 if owned, 0 otherwise)
    pub fn balance_of(&self, owner: Address) -> U256 {
        if owner == self.owner.get() {
            U256::from(1)
        } else {
            U256::from(0)
        }
    }

    /// Get the owner of a specific token ID (only supports token ID 1)
    pub fn owner_of(&self, token_id: U256) -> Result<Address, Vec<u8>> {
        // Check if the token_id is valid (only token ID 1 is allowed)
        assert!(token_id == U256::from(1), "Invalid token ID");

        // Retrieve the current owner of the token
        let owner = self.owner.get();

        // Ensure the token has been minted (owner should not be Address::ZERO)
        assert!(owner != Address::ZERO, "Token not minted");

        // Return the owner's address
        Ok(owner)
    }

    /// Generate Token URI: Returns a dynamic SVG and JSON representing the NFT
    #[selector(name = "tokenURI")]
    pub fn token_uri(&self, token_id: U256) -> String {
        // Ensure the token ID is valid (only token ID 1 is supported)
        assert!(token_id == U256::from(1), "Invalid token ID");

        // Hardcoded song-related SVG for "heavy metal"
        let svg = r#"<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">
            <rect width="100%" height="100%" fill="black"/>
            <text x="50%" y="50%" fill="white" font-size="24" text-anchor="middle">
                Heavy Metal Anthem 🎸
            </text>
        </svg>"#;

        // Base64-encoded image mock-up
        let svg_base64 = base64_encode(svg.as_bytes());

        // Hardcoded JSON metadata with the base64-encoded image and URLs for the image and music
        let json = format!(
            r#"{{"name":"Heavy Metal Anthem","description":"A hard-hitting, high-energy NFT inspired by heavy metal music.","image":"{}","music":"{}"}}"#,
            self.image_url.get_string(),
            self.music_url.get_string()
        );

        // Return the full data URI for the token
        format!("data:application/json;base64,{}", base64_encode(json.as_bytes()))
    }

    /// Initialize the contract with the given data (symbol, name, description, image, and music)
    pub fn initialize_contract(&mut self, owner: Address, image_url: String, music_url: String) {
        // Set hardcoded values for the contract
        self.symbol.set_str("HeavyMetalNFT");
        self.name.set_str("Heavy Metal Anthem");
        self.description.set_str("A hard-hitting, high-energy NFT inspired by heavy metal music.");
        self.owner.set(owner);
        self.image_url.set_str(image_url);
        self.music_url.set_str(music_url);

        // Emit a log event indicating successful initialization
        evm::log(LogMintingSuccess { message: "Contract initialized successfully.".to_string() });
    }
}

/// Helper function for Base64 encoding
fn base64_encode(input: &[u8]) -> String {
    const ALPHABET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut result = String::with_capacity((input.len() + 2) / 3 * 4);
    for chunk in input.chunks(3) {
        let b = match chunk.len() {
            3 => ((chunk[0] as u32) << 16) | ((chunk[1] as u32) << 8) | (chunk[2] as u32),
            2 => ((chunk[0] as u32) << 16) | ((chunk[1] as u32) << 8),
            1 => (chunk[0] as u32) << 16,
            _ => unreachable!(),
        };
        result.push(ALPHABET[(b >> 18 & 0x3F) as usize] as char);
        result.push(ALPHABET[(b >> 12 & 0x3F) as usize] as char);
        if chunk.len() > 1 {
            result.push(ALPHABET[(b >> 6 & 0x3F) as usize] as char);
        } else {
            result.push('=');
        }
        if chunk.len() > 2 {
            result.push(ALPHABET[(b & 0x3F) as usize] as char);
        } else {
            result.push('=');
        }
    }
    result
}
