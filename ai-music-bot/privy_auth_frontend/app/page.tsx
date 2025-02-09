'use client';

import { usePrivy } from '@privy-io/react-auth';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

export default function Home() {
  const { login, logout, authenticated, user } = usePrivy();
  const router = useRouter();
  const [userTgId, setUserTgId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false); // Track loading state

  // Extract userId from the URL query parameters
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const userIdFromUrl = params.get('userId');
    if (userIdFromUrl) {
      setUserTgId(userIdFromUrl); // Store the userId from the URL
    }
  }, []);

  useEffect(() => {
    if (authenticated && user) {
      // Get user details (e.g., userId, wallet address)
      const email = user?.email?.address;
      const userId = user.id;
      const walletAddress = user.wallet?.address || '';
      const chainType = user.wallet?.chainType || '';

      // Send a POST request to your backend to add the user to the mock database
      if (userId) {
        fetch('http://127.0.0.1:8000/add_user', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            email: email || userId,
            user_id_tg: userTgId || "not_from_tg",  // for testing for now
            user_id: userId,
            wallet_address: walletAddress,
            chain_type: chainType,
          }),
        }).then(response => {
          if (response.ok) {
            // Send Telegram message and wait for a successful response before redirecting
            setIsLoading(true);

            sendTelegramMessage(userTgId, walletAddress).then(() => {
              setIsLoading(false);

              // Let's add a small delay before redirecting
              setTimeout(() => {
                router.push(`https://t.me/purrtunes_bot?start=${userId}`);
              }, 1000);
            });
          }
        }).catch(error => {
          console.error('Error adding user to backend:', error);
        });
      }
    }
  }, [authenticated, user]);

  const sendTelegramMessage = async (userId, walletAddress) => {
    try {
      const botToken = process.env.NEXT_PUBLIC_TG_ID;
      const message = `🎉 **Thank you for registering!**\n\n`
                  + `✅ **Your wallet address has been successfully linked.**\n\n`
                  + `💰 **Address:** \`${walletAddress}\`\n\n`
                  + `🚀 **Now you're ready to mint your music NFT!**\n\n`
                  + `🎶 **Get started by approving the address pushing the button below.**\n\n`
                  + `🔥 Let's make some magic happen! 🎵`;

      const response = await fetch('/api/sendMessage', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          userId: userId,
          message: message,
          walletAddress: walletAddress,
        }),
      });

      const data = await response.json();

      if (response.ok) {
        console.log('Telegram message sent successfully:', data);
      } else {
        console.error('Error sending message:', data.error);
      }
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

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
            <h2 className="text-xl">Welcome onboard!</h2>
            <p>{user?.email?.address || user.id}</p>
            <h2>
              {user?.wallet?.address ? (
                <>
                  <span>Wallet Address: {user.wallet?.address}</span>
                  <span>Chain type: {user.wallet?.chainType}</span>
                </>
              ) : (
                <span>No wallet linked</span>
              )}
            </h2>

            {/* Loading UI */}
            {isLoading ? (
              <div className="mt-4 text-center">
                <p>Sending your wallet address...</p>
                <div className="spinner"></div> {/* Add your spinner here */}
              </div>
            ) : null}

            <button
              onClick={logout}
              className="mt-4 px-4 py-2 bg-red-500 text-white rounded"
            >
              Logout
            </button>
          </>
        ) : (
          <button
            onClick={() => login({ prefill: { type: 'email', value: '' } })} // You can prefill if needed
            className="px-4 py-2 bg-blue-500 text-white rounded"
          >
            Login with Email
          </button>
        )}
      </main>
    </div>
  );
}
