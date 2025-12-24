import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  turbopack: {}, // ✅ keep turbopack explicit (silences some warnings)
};

export default nextConfig;
