'use client';

import dynamic from 'next/dynamic';

// Dynamic imports with ssr: false for all MeshSDK-dependent components
const HomeContent = dynamic(() => import('./HomeContent'), { 
  ssr: false,
  loading: () => (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-cardano-blue mx-auto mb-4"></div>
        <p className="text-gray-600">Loading CIP-68 Demo...</p>
      </div>
    </div>
  ),
});

export default function Home() {
  return <HomeContent />;
}
