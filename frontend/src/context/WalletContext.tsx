'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { CardanoWalletAPI, CardanoWindow, SUPPORTED_WALLETS, WalletInfo } from '@/types/cardano';

interface WalletContextType {
  // State
  connected: boolean;
  connecting: boolean;
  walletName: string | null;
  walletAddress: string | null;
  walletApi: CardanoWalletAPI | null;
  error: string | null;
  
  // Actions
  connect: (walletId: keyof CardanoWindow) => Promise<void>;
  disconnect: () => void;
  getAvailableWallets: () => WalletInfo[];
  signTx: (txCbor: string, partialSign?: boolean) => Promise<string>;
}

const WalletContext = createContext<WalletContextType | null>(null);

export function useWallet() {
  const context = useContext(WalletContext);
  if (!context) {
    throw new Error('useWallet must be used within a WalletProvider');
  }
  return context;
}

interface WalletProviderProps {
  children: ReactNode;
}

export function WalletProvider({ children }: WalletProviderProps) {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [walletName, setWalletName] = useState<string | null>(null);
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const [walletApi, setWalletApi] = useState<CardanoWalletAPI | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Get available wallets
  const getAvailableWallets = useCallback((): WalletInfo[] => {
    if (typeof window === 'undefined' || !window.cardano) {
      return [];
    }

    return SUPPORTED_WALLETS.map(wallet => ({
      ...wallet,
      available: !!window.cardano?.[wallet.id],
    })).filter(w => w.available);
  }, []);

  // Convert hex to bech32 address (simplified - just return first used address)
  const getAddress = async (api: CardanoWalletAPI): Promise<string> => {
    const addresses = await api.getUsedAddresses();
    if (addresses && addresses.length > 0) {
      // Addresses are returned as hex-encoded CBOR
      // For display, we'll use the raw hex - backend will handle conversion
      return addresses[0];
    }
    
    const unusedAddresses = await api.getUnusedAddresses();
    if (unusedAddresses && unusedAddresses.length > 0) {
      return unusedAddresses[0];
    }
    
    const changeAddress = await api.getChangeAddress();
    return changeAddress;
  };

  // Connect to wallet
  const connect = useCallback(async (walletId: keyof CardanoWindow) => {
    if (typeof window === 'undefined' || !window.cardano) {
      setError('Cardano wallet not found. Please install a wallet extension.');
      return;
    }

    const wallet = window.cardano[walletId];
    if (!wallet) {
      setError(`${walletId} wallet not found. Please install it.`);
      return;
    }

    setConnecting(true);
    setError(null);

    try {
      const api = await wallet.enable();
      const addressHex = await getAddress(api);
      
      setWalletApi(api);
      setWalletName(wallet.name);
      setWalletAddress(addressHex);
      setConnected(true);
      
      // Save to localStorage
      localStorage.setItem('connectedWallet', walletId);
    } catch (err: any) {
      console.error('Failed to connect wallet:', err);
      setError(err.message || 'Failed to connect wallet');
    } finally {
      setConnecting(false);
    }
  }, []);

  // Disconnect wallet
  const disconnect = useCallback(() => {
    setWalletApi(null);
    setWalletName(null);
    setWalletAddress(null);
    setConnected(false);
    setError(null);
    localStorage.removeItem('connectedWallet');
  }, []);

  // Sign transaction (returns witness set CBOR)
  const signTx = useCallback(async (txCbor: string, partialSign: boolean = false): Promise<string> => {
    if (!walletApi) {
      throw new Error('Wallet not connected');
    }

    try {
      // Sign with partialSign: true - returns witness set only
      const witnessSetCbor = await walletApi.signTx(txCbor, partialSign);
      return witnessSetCbor;
    } catch (err: any) {
      console.error('Transaction signing failed:', err);
      throw new Error(err.message || 'Failed to sign transaction');
    }
  }, [walletApi]);

  // Auto-reconnect on mount
  React.useEffect(() => {
    const savedWallet = localStorage.getItem('connectedWallet') as keyof CardanoWindow | null;
    if (savedWallet && typeof window !== 'undefined' && window.cardano?.[savedWallet]) {
      connect(savedWallet);
    }
  }, [connect]);

  const value: WalletContextType = {
    connected,
    connecting,
    walletName,
    walletAddress,
    walletApi,
    error,
    connect,
    disconnect,
    getAvailableWallets,
    signTx,
  };

  return (
    <WalletContext.Provider value={value}>
      {children}
    </WalletContext.Provider>
  );
}
