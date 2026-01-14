'use client';

import { ReactNode, useState, useEffect } from 'react';
import { WalletProvider } from '@/context/WalletContext';

export default function Providers({ children }: { children: ReactNode }) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Don't render WalletProvider on server side (CIP-30 needs window.cardano)
  if (!isClient) {
    return <>{children}</>;
  }

  return (
    <WalletProvider>
      {children}
    </WalletProvider>
  );
}
