import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
  experimental: {
    proxyTimeout: 300000, // 5 minutes timeout for backend proxy
  },
};

export default nextConfig;
