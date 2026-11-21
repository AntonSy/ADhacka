/** @type {import('next').NextConfig} */
const BACKEND = process.env.BACKEND_URL || "http://127.0.0.1:8000";

module.exports = {
  output: "standalone",
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND}/api/:path*` },
      { source: "/docs", destination: `${BACKEND}/docs` },
      { source: "/openapi.json", destination: `${BACKEND}/openapi.json` },
    ];
  },
};
