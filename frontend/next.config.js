const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Transpile packages that have ESM issues
  transpilePackages: [
    '@meshsdk/core',
    '@meshsdk/core-cst',
    '@meshsdk/react',
    '@meshsdk/wallet',
    '@cardano-sdk/crypto',
    'libsodium-wrappers-sumo',
    'libsodium-sumo',
  ],
  
  webpack: function (config, { isServer }) {
    config.experiments = {
      ...config.experiments,
      asyncWebAssembly: true,
      topLevelAwait: true,
      layers: true,
    };

    // Fix libsodium ESM resolution issue
    config.resolve.alias = {
      ...config.resolve.alias,
      // Alias libsodium-sumo.mjs to the correct path
      './libsodium-sumo.mjs': path.resolve(
        __dirname,
        'node_modules/libsodium-sumo/dist/modules-sumo-esm/libsodium-sumo.mjs'
      ),
    };

    // Ignore fs and other node modules in browser
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        path: false,
        stream: false,
        crypto: false,
      };
    }

    return config;
  },
}

module.exports = nextConfig