#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;
use stylus_sdk::{alloy_primitives::{Address, U256}, prelude::*};
use stylus_sdk::{alloy_sol_types::sol, evm};
use stylus_sdk::storage::{StorageAddress, StorageString};
use stylus_sdk::block;
use stylus_sdk::tx;

/// Event emitted when a mint occurs
sol! {
    event Minted(address indexed owner);
    event LogMintingSuccess(string message); // Added custom logging event
}

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

    /// The music file of the NFT
    music_data: StorageString,

    /// SVG Template with placeholders
    svg_template: StorageString,
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

    /// Get the title of the NFT (e.g., "SONG NFT")
    pub fn title(&self) -> String {
        self.title.get_string()
    }

    /// Get the lyrics of the song (Decodes from Base64)
    pub fn lyrics(&self) -> String {
        let encoded_lyrics = self.lyrics.get_string();
        let decoded_lyrics = base64_decode(&encoded_lyrics);
        String::from_utf8(decoded_lyrics).expect("Lyrics not valid UTF-8")
    }

    /// Get the metadata of the song (Decodes from Base64)
    pub fn meta(&self) -> String {
        format!("data:audio/mpeg;base64,{}", self.music_data.get_string())
    }

    /// Get the metadata of the song (Decodes from Base64)
    pub fn music(&self) -> String {
        let encoded_music_data = self.music_data.get_string();
        let decoded_music = base64_decode(&encoded_music_data);
        String::from_utf8(decoded_music).expect("Music not valid UTF-8")
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

    pub fn update_svg_template(&mut self, new_svg_template: String) {
        // Get the address of the caller (msg.sender equivalent in Stylus)
        let caller = tx::origin();  // Get the address of the caller

        // Check if the caller is the contract owner
        assert!(caller == self.owner.get(), "Only the owner can update the SVG template");

        // Update the SVG template
        self.svg_template.set_str(new_svg_template);

        // Emit a log to signal the update
        evm::log(LogMintingSuccess { message: "SVG template updated.".to_string() });
    }


    /// Generate Token URI: Returns a minimalistic JSON representing the NFT
    #[selector(name = "tokenURI")]
    pub fn token_uri(&self, token_id: U256) -> String {
        assert!(token_id == U256::from(1), "Invalid token ID");

        // Decode stored Base64-encoded SVG template
        let encoded_svg = self.svg_template.get_string();
        let svg_bytes = base64_decode(&encoded_svg);
        let svg_decoded = String::from_utf8(svg_bytes).expect("SVG not valid UTF-8");

        // Encode again to Base64 for embedding in data URI
        let svg_data_uri = format!("data:image/svg+xml;base64,{}", base64_encode(svg_decoded.as_bytes()));

        // Decode Base64-encoded metadata
        let encoded_meta = self.meta.get_string();
        let meta_bytes = base64_decode(&encoded_meta);
        let meta_decoded = String::from_utf8(meta_bytes).expect("Meta not valid UTF-8");

        let encoded_lyrics = self.lyrics.get_string();
        let lyrics_bytes = base64_decode(&encoded_lyrics);
        let lyrics_decoded = String::from_utf8(lyrics_bytes).expect("Lyrics not valid UTF-8");
        let music_data_uri = format!("data:audio/mpeg;base64,{}", self.music_data.get_string());

        // Generate JSON metadata dynamically
        let json = format!(
            r#"{{"name":"{}","lyrics":"{}","description":"{}","image":"{}","music":"{}"}}"#,
            self.title.get_string(),
            lyrics_decoded,
            meta_decoded,
            svg_data_uri,
            music_data_uri
        );

        // Return data URI with encoded JSON
        format!("data:application/json;base64,{}", base64_encode(json.as_bytes()))
    }

    /// Initialize the contract with the given data (symbol, title, lyrics, meta, image, and music)
    pub fn initialize_contract(
        &mut self,
        owner: Address,
        symbol: String,
        title: String,
        lyrics: String,
        meta: String,
        music_data: String,
        svg_template: String,  // Expecting SVG template as a string
    ) {
        // Set values for the contract
        self.symbol.set_str(symbol);
        self.title.set_str(title);
        self.lyrics.set_str(lyrics);
        self.meta.set_str(meta);
        self.owner.set(owner);
        self.music_data.set_str(music_data);
        self.svg_template.set_str(svg_template);  // Store SVG template passed off-chain

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

fn base64_decode(encoded: &str) -> Vec<u8> {
    let alphabet = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut output = Vec::new();
    let mut buffer = 0u32;
    let mut bits_collected = 0;

    for byte in encoded.bytes() {
        if byte == b'=' {
            break;
        }

        let value = alphabet.iter().position(|&c| c == byte);
        if let Some(value) = value {
            buffer = (buffer << 6) | (value as u32);
            bits_collected += 6;
            if bits_collected >= 8 {
                bits_collected -= 8;
                output.push((buffer >> bits_collected) as u8);
            }
        }
    }
    output
}
