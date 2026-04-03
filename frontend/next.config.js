/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "https://socio-inteligente-production.up.railway.app/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
