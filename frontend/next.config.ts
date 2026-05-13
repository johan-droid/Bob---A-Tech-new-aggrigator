import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  eslint: {
    // Lint is handled separately; don't fail build on ESLint errors
    ignoreDuringBuilds: true,
  },
  typescript: {
    // Fail on TS errors during build
    ignoreBuildErrors: false,
  },
};

export default nextConfig;
