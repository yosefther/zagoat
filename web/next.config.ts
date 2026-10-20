import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  cacheComponents: true,
  partialPrefetching: true,
  // "Problems" were renamed "tasks"; keep old links working.
  async redirects() {
    return [
      { source: "/problems", destination: "/tasks", permanent: true },
      { source: "/problems/:id", destination: "/tasks/:id", permanent: true },
    ];
  },
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;
