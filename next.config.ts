import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  transpilePackages: [
    "three",
    "@takram/three-atmosphere",
    "@takram/three-clouds",
    "@takram/three-geospatial",
    "@takram/three-geospatial-effects",
  ],
  turbopack: {
    rules: {
      "*.glsl": {
        loaders: ["raw-loader"],
        as: "*.js",
      },
    },
  },
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "catalog.carbonmapper.org" },
      { protocol: "https", hostname: "api.carbonmapper.org" },
    ],
  },
};

export default nextConfig;
