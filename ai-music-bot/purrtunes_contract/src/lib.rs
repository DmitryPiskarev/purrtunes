#![cfg_attr(not(any(test, feature = "export-abi")), no_main)]
extern crate alloc;

/// Import Stylus SDK and common types
use stylus_sdk::{alloy_primitives::{Address, U256}, prelude::*};
use stylus_sdk::{alloy_sol_types::sol, evm};
use stylus_sdk::storage::{StorageAddress, StorageU32};
use alloy_primitives::U32;


/// Events
sol! {
    event Minted(address indexed owner);
}

#[entrypoint]
#[storage]
pub struct Contract {
    /// The NFT owner
    owner: StorageAddress,
    /// A random seed (can be used for generative art/audio in the future)
    rng_seed: StorageU32,
}

#[public]
impl Contract {

    /// ERC-165 & ERC-721 Interface Support
    pub fn supports_interface(&self, interface: [u8; 4]) -> bool {
        matches!(interface, [0x01, 0xff, 0xc9, 0xa7] | [0x80, 0xac, 0x58, 0xcd] | [0x5b, 0x5e, 0x13, 0x9f])
    }

    /// Mint function (one per address)
    pub fn mint(&mut self, to: Address) {
        assert!(self.owner.get() == Address::ZERO, "Already minted!");
        self.owner.set(to);
        self.rng_seed.set(U32::from(1));  // Future randomness
        evm::log(Minted { owner: to });
    }

    pub fn symbol(&self) -> String {
        "PurrtunesNFT".to_string()
    }

    pub fn name(&self) -> String {
        "SONG NFT".to_string()
    }

    pub fn description(&self) -> String {
        "A unique, cat-inspired music NFT with dynamic visuals.".to_string()
    }

    /// Balance check (1 if owned, 0 otherwise)
    pub fn balance_of(&self, owner: Address) -> U256 {
        if owner == self.owner.get() { U256::from(1) } else { U256::from(0) }
    }

    /// Get owner of the NFT
    pub fn owner_of(&self, token_id: U256) -> Result<Address, Vec<u8>> {
        assert!(token_id == U256::from(1), "Invalid token ID");
        let owner = self.owner.get();
        assert!(owner != Address::ZERO, "Token not minted");
        Ok(owner)
    }

    /// Generate Token URI (Dynamic SVG + JSON)
    #[selector(name = "tokenURI")]
    pub fn token_uri(&self, token_id: U256) -> String {
        assert!(token_id == U256::from(1), "Invalid token ID");

        // Simple music-themed SVG
        let svg = r#"<?xml version="1.0" encoding="UTF-8"?>
        <svg xmlns="http://www.w3.org/2000/svg" width="300" height="300">
            <rect width="100%" height="100%" fill="black"/>
            <text x="50%" y="50%" fill="white" font-size="24" text-anchor="middle">
                Purrtunes 🎶
            </text>
        </svg>"#;

        let svg_base64 = base64_encode(svg.as_bytes());
        let json = format!(
            r#"{{"name":"PurrtunesNFT","description":"A cat-inspired music NFT.","image":"data:image/svg+xml;base64,{}"}}"#,
            svg_base64
        );

        format!("data:application/json;base64,{}", base64_encode(json.as_bytes()))
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
