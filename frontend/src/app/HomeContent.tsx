'use client';

import { useState, useEffect } from 'react';
import { useWallet } from '@/context/WalletContext';
import WalletConnect from '@/components/WalletConnect';
import MintForm from '@/components/MintForm';
import NFTList from '@/components/NFTList';
import TransactionStatus from '@/components/TransactionStatus';

export default function HomeContent() {
  const { connected, walletAddress: rawWalletAddress } = useWallet();
  const [txStatus, setTxStatus] = useState<{
    status: 'idle' | 'building' | 'signing' | 'submitting' | 'success' | 'error';
    message: string;
    txHash?: string;
  }>({ status: 'idle', message: '' });

  const [walletAddress, setWalletAddress] = useState<string>('');
  const [scriptInfo, setScriptInfo] = useState<any>(null);
  const [error, setError] = useState<string>('');
  const [refreshNFTList, setRefreshNFTList] = useState(0);

  // Function to trigger NFT list refresh
  const handleRefreshNFTList = () => {
    setRefreshNFTList(prev => prev + 1);
  };

  useEffect(() => {
    const fetchScriptInfo = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/script-info');
        const data = await res.json();
        setScriptInfo(data);
      } catch (error) {
        console.error('Failed to fetch script info:', error);
        setError('Không thể kết nối với backend. Vui lòng kiểm tra backend đang chạy.');
      }
    };

    fetchScriptInfo();
  }, []);

  // Convert hex address to bech32 via backend
  useEffect(() => {
    const convertAddress = async () => {
      if (connected && rawWalletAddress) {
        try {
          // Call backend to convert hex address to bech32
          const res = await fetch(`http://localhost:8000/api/convert-address?hex_address=${rawWalletAddress}`);
          const data = await res.json();
          if (data.success && data.bech32_address) {
            setWalletAddress(data.bech32_address);
          } else {
            // Fallback: use raw address if conversion fails
            setWalletAddress(rawWalletAddress);
          }
        } catch (err) {
          console.error('Failed to convert wallet address:', err);
          setWalletAddress(rawWalletAddress);
        }
      }
    };

    convertAddress();
  }, [connected, rawWalletAddress]);

  const tabs = [
    { id: 'mint', label: '🎨 Mint NFT', description: 'Tạo CIP-68 Dynamic NFT mới' },
  ];

  return (
    <main className="min-h-screen py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-4xl font-bold text-cardano-blue mb-4">
            CIP-68 Dynamic Asset Demo
          </h1>
          <p className="text-gray-600 max-w-2xl mx-auto">
            Demo ứng dụng CIP-68 Dynamic NFT sử dụng PyCardano. 
            Mint NFT và quản lý metadata trực tiếp từ browser wallet.
          </p>
          
          {error && (
            <div className="mt-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded-lg text-sm">
              ⚠️ {error}
            </div>
          )}

          {scriptInfo && (
            <div className="mt-4 text-sm text-gray-500">
              <span className="font-medium">Network:</span> {scriptInfo.network}
              {scriptInfo.info && (
                <span className="ml-2 text-xs">• {scriptInfo.info}</span>
              )}
            </div>
          )}
        </header>

        {/* Wallet Connect */}
        <div className="flex justify-center mb-8">
          <WalletConnect />
        </div>

        {connected ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Panel - Mint Form */}
            <div className="lg:col-span-2">
              {/* Single Tab - Mint Only */}
              <div className="card">
                <MintForm 
                  walletAddress={walletAddress}
                  setTxStatus={setTxStatus}
                  scriptInfo={scriptInfo}
                  onMintSuccess={handleRefreshNFTList}
                />
              </div>

              {/* Transaction Status */}
              <TransactionStatus status={txStatus} />
            </div>

            {/* Right Panel - NFT List with Update/Burn buttons */}
            <div className="lg:col-span-1">
              <NFTList 
                key={refreshNFTList}
                walletAddress={walletAddress}
                scriptInfo={scriptInfo}
                setTxStatus={setTxStatus}
              />
            </div>
          </div>
        ) : (
          <div className="card text-center py-16">
            <div className="text-6xl mb-4">🔐</div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">
              Kết nối ví để bắt đầu
            </h2>
            <p className="text-gray-500">
              Hỗ trợ Nami, Eternl, Lace và các ví Cardano phổ biến khác
            </p>
          </div>
        )}

        {/* Footer */}
        <footer className="mt-16 text-center text-gray-500 text-sm">
          <p>
            Built with ❤️ using PyCardano & Aiken | 
            <a 
              href="https://cips.cardano.org/cip/CIP-68" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-cardano-blue hover:underline ml-1"
            >
              CIP-68 Specification
            </a>
          </p>
        </footer>
      </div>
    </main>
  );
}
