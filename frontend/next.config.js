/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    // Lint is handled separately; don't fail Vercel build on ESLint config incompatibilities
    ignoreDuringBuilds: true,
  },
};

module.exports = nextConfig;
