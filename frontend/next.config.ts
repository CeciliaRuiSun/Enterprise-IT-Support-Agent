import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {
    typedRoutes: true
  },
  async rewrites() {
    const backendApiUrl = process.env.BACKEND_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

    return [
      {
        source: "/backend-api/:path*",
        destination: `${backendApiUrl}/:path*`
      }
    ];
  }
};

export default nextConfig;
