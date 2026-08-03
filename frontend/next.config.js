/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "https://socio-ai-backend.vercel.app";

    return [
      {
        source: "/api/health",
        destination: `${backendUrl}/health`,
      },
      {
        source: "/api/auth/:path*",
        destination: `${backendUrl}/auth/:path*`,
      },
      {
        source: "/api/perfil/:path*",
        destination: `${backendUrl}/perfil/:path*`,
      },
      {
        source: "/api/dashboard/:path*",
        destination: `${backendUrl}/dashboard/:path*`,
      },
      {
        source: "/api/risk-engine/:path*",
        destination: `${backendUrl}/risk-engine/:path*`,
      },
      {
        source: "/api/areas/:path*",
        destination: `${backendUrl}/areas/:path*`,
      },
      {
        source: "/api/chat/:path*",
        destination: `${backendUrl}/chat/:path*`,
      },
      {
        source: "/api/metodologia/:path*",
        destination: `${backendUrl}/metodologia/:path*`,
      },
      {
        source: "/api/workflow/:path*",
        destination: `${backendUrl}/workflow/:path*`,
      },
      {
        source: "/api/papeles-trabajo/:clienteId/tasks/:taskId",
        destination: `${backendUrl}/papeles-trabajo/:clienteId/tasks/:taskId`,
      },
      {
        source: "/api/papeles-trabajo/:clienteId/tasks",
        destination: `${backendUrl}/papeles-trabajo/:clienteId/tasks`,
      },
      {
        source: "/api/papeles-trabajo/:clienteId",
        destination: `${backendUrl}/papeles-trabajo/:clienteId`,
      },
      {
        source: "/api/reportes/papeles-trabajo/:path*",
        destination: `${backendUrl}/api/reportes/papeles-trabajo/:path*`,
      },
      {
        source: "/api/reportes/:clienteId/export/stream",
        destination: `${backendUrl}/api/reportes/:clienteId/export/stream`,
      },
      {
        source: "/api/reportes/:clienteId/export",
        destination: `${backendUrl}/api/reportes/:clienteId/export`,
      },
      {
        source: "/api/reportes/:path*",
        destination: `${backendUrl}/reportes/:path*`,
      },
      {
        source: "/api/papeles-trabajo/:clienteId/plantilla",
        destination: `${backendUrl}/api/papeles-trabajo/:clienteId/plantilla`,
      },
      {
        source: "/api/papeles-trabajo/:clienteId/papeles-por-ls",
        destination: `${backendUrl}/api/papeles-trabajo/:clienteId/papeles-por-ls`,
      },
      {
        source: "/api/papeles-trabajo/:clienteId/upload",
        destination: `${backendUrl}/api/papeles-trabajo/:clienteId/upload`,
      },
      {
        source: "/api/papeles-trabajo/:clienteId/files",
        destination: `${backendUrl}/api/papeles-trabajo/:clienteId/files`,
      },
      {
        source: "/api/papeles-trabajo/:clienteId/:areaCode/:fileId/sign",
        destination: `${backendUrl}/api/papeles-trabajo/:clienteId/:areaCode/:fileId/sign`,
      },
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
