'use client';

import { PrivyProvider } from '@privy-io/react-auth';

export default function Providers({ children }: { children: React.ReactNode }) {
  console.log("NEXT_PUBLIC_PRIVY_APP_ID", process.env.NEXT_PUBLIC_PRIVY_APP_ID)
  return (
    <PrivyProvider
      appId={process.env.NEXT_PUBLIC_PRIVY_APP_ID!}
      config={{
        appearance: {
          theme: 'light',
          accentColor: '#676FFF',
        },
        embeddedWallets: {
          createOnLogin: 'users-without-wallets', // Default: 'off'
        },
      }}
    >
      {children}
    </PrivyProvider>
  );
}
