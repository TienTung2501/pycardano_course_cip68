'use client';

import { useState } from 'react';
import { useWallet } from '@/context/WalletContext';
import { CardanoWindow } from '@/types/cardano';

export default function WalletConnect() {
  const { 
    connected, 
    connecting, 
    walletName, 
    walletAddress, 
    error,
    connect, 
    disconnect, 
    getAvailableWallets 
  } = useWallet();
  
  const [showDropdown, setShowDropdown] = useState(false);

  const availableWallets = getAvailableWallets();

  const handleConnect = async (walletId: keyof CardanoWindow) => {
    await connect(walletId);
    setShowDropdown(false);
  };

  // Format address for display (first 8 + ... + last 8)
  const formatAddress = (address: string): string => {
    if (address.length <= 20) return address;
    return `${address.slice(0, 8)}...${address.slice(-8)}`;
  };

  if (connected) {
    return (
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 bg-green-100 text-green-800 px-4 py-2 rounded-lg">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          <span className="font-medium">{walletName}</span>
          {walletAddress && (
            <span className="text-xs text-green-600 hidden sm:inline">
              ({formatAddress(walletAddress)})
            </span>
          )}
        </div>
        <button
          onClick={disconnect}
          className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors text-sm font-medium"
        >
          Ngắt kết nối
        </button>
      </div>
    );
  }

  return (
    <div className="relative">
      {error && (
        <div className="absolute top-full left-0 mt-2 p-2 bg-red-100 text-red-700 rounded text-sm max-w-xs">
          {error}
        </div>
      )}
      
      {availableWallets.length === 0 ? (
        <div className="px-4 py-2 bg-yellow-100 text-yellow-800 rounded-lg text-sm">
          Không tìm thấy ví Cardano. Vui lòng cài đặt Nami, Eternl, hoặc Lace.
        </div>
      ) : (
        <div className="relative">
          <button
            onClick={() => setShowDropdown(!showDropdown)}
            disabled={connecting}
            className={`px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2
              ${connecting 
                ? 'bg-gray-300 text-gray-500 cursor-wait' 
                : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
          >
            {connecting ? (
              <>
                <span className="animate-spin">⏳</span>
                Đang kết nối...
              </>
            ) : (
              <>
                <span>🔗</span>
                Kết nối ví
              </>
            )}
          </button>
          
          {showDropdown && !connecting && (
            <div className="absolute top-full left-0 mt-2 bg-white border border-gray-200 rounded-lg shadow-lg z-50 min-w-[200px]">
              {availableWallets.map(wallet => (
                <button
                  key={wallet.id}
                  onClick={() => handleConnect(wallet.id)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-100 flex items-center gap-3 first:rounded-t-lg last:rounded-b-lg transition-colors"
                >
                  <span className="text-xl">{wallet.icon}</span>
                  <span className="font-medium text-gray-800">{wallet.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Click outside to close dropdown */}
      {showDropdown && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
}
