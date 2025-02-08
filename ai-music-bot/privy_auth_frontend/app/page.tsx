'use client';

import { usePrivy } from '@privy-io/react-auth';
import { useEffect } from 'react';
import Image from "next/image";

export default function Home() {
  const { login, logout, authenticated, user } = usePrivy();

  useEffect(() => {
    if (authenticated && user) {
      // Get user details (e.g., userId, wallet address)
      const userId = user.id;
      const walletAddress = user.wallet?.address;

      // Send a POST request to your Telegram bot endpoint to link the wallet
      if (userId && walletAddress) {
        fetch('http://127.0.0.1:8000/link_wallet', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId, wallet_address: walletAddress }),
        }).then(response => {
          if (response.ok) {
            window.location.href = 'https://t.me/purrtunes_bot'; // Redirect to the bot
          }
        }).catch(error => {
          console.error("Error linking wallet:", error);
        });
      }
    }
  }, [authenticated, user]);

  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-8 row-start-2 items-center sm:items-start">
        <Image
          className="dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={180}
          height={38}
          priority
        />
        {authenticated ? (
          <>
            <h2 className="text-xl">Welcome {user?.email}</h2>
            <button
              onClick={logout}
              className="mt-4 px-4 py-2 bg-red-500 text-white rounded"
            >
              Logout
            </button>
          </>
        ) : (
          <button
            onClick={login}
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            Login with Privy
          </button>
        )}
      </main>
    </div>
  );
}
