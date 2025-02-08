import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'https://auth.privy.io/api/v1/:path*', // Proxy to Privy API
      },
    ]
  },
  // Additional config options
};

export default nextConfig;
