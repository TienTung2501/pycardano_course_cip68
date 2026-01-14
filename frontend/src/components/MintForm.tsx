'use client';

import { useState } from 'react';
import { useWallet } from '@/context/WalletContext';

interface MintFormProps {
  walletAddress: string;
  setTxStatus: (status: any) => void;
  scriptInfo: any;
  onMintSuccess?: () => void;  // Callback to refresh NFT list
}

export default function MintForm({ walletAddress, setTxStatus, scriptInfo, onMintSuccess }: MintFormProps) {
  const { signTx, connected } = useWallet();
  const [tokenName, setTokenName] = useState('');
  const [description, setDescription] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleMint = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!connected || !walletAddress) {
      setTxStatus({ status: 'error', message: 'Vui lòng kết nối ví trước!' });
      return;
    }

    try {
      setIsLoading(true);
      setTxStatus({ status: 'building', message: 'Đang tạo transaction...' });

      // 1. Request unsigned transaction from backend
      const response = await fetch('http://localhost:8000/api/mint', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_address: walletAddress,
          token_name: tokenName,
          description: description,
        }),
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message);
      }

      setTxStatus({ status: 'signing', message: 'Vui lòng ký transaction trong ví...' });

      // 2. Sign transaction with wallet (returns witness set)
      const witnessSet = await signTx(data.tx_cbor);

      setTxStatus({ status: 'submitting', message: 'Đang gửi transaction...' });

      // 3. Submit signed transaction via backend
      const submitResponse = await fetch('http://localhost:8000/api/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          tx_cbor: data.tx_cbor,
          witness_set_cbor: witnessSet 
        }),
      });

      const submitData = await submitResponse.json();

      if (!submitData.success) {
        throw new Error(submitData.message);
      }

      const txHash = submitData.tx_hash;

      // Save mint info to localStorage for burn operation
      const mintInfo = {
        token_name: tokenName,
        policy_id: data.policy_id,
        tx_hash: txHash,
        timestamp: Date.now(),
      };
      localStorage.setItem(`nft_${tokenName}`, JSON.stringify(mintInfo));

      setTxStatus({
        status: 'success',
        message: `NFT "${tokenName}" đã được mint thành công! Policy ID: ${data.policy_id?.slice(0, 16)}...`,
        txHash: txHash,
      });

      // Reset form
      setTokenName('');
      setDescription('');
      
      // Trigger refresh of NFT list after short delay to allow blockchain to process
      if (onMintSuccess) {
        setTimeout(() => {
          onMintSuccess();
        }, 2000);
      }

    } catch (error: any) {
      console.error('Mint error:', error);
      setTxStatus({
        status: 'error',
        message: error.message || 'Có lỗi xảy ra khi mint NFT',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        🎨 Mint CIP-68 Dynamic NFT
      </h2>
      <p className="text-gray-600 mb-6">
        Tạo một NFT mới với metadata có thể cập nhật. NFT sẽ được mint với 2 tokens: 
        Reference Token (lưu metadata) và User Token (cho người dùng).
      </p>

      <form onSubmit={handleMint} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tên Token
          </label>
          <input
            type="text"
            value={tokenName}
            onChange={(e) => setTokenName(e.target.value)}
            placeholder="MyAwesomeNFT"
            className="input"
            required
            maxLength={32}
            disabled={isLoading}
          />
          <p className="text-xs text-gray-500 mt-1">
            Tối đa 32 ký tự, không có khoảng trắng
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Mô tả
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Mô tả về NFT của bạn..."
            className="input min-h-[100px]"
            required
            maxLength={256}
            disabled={isLoading}
          />
          <p className="text-xs text-gray-500 mt-1">
            Tối đa 256 ký tự. Có thể cập nhật sau khi mint.
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2">ℹ️ Chi tiết</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Reference Token sẽ có label: 000643b0 (CIP-68 label 100)</li>
            <li>• User Token sẽ có label: 000de140 (CIP-68 label 222)</li>
            <li>• Policy ID sẽ được tạo từ seed UTxO</li>
            <li>• Chi phí: ~2 ADA cho mỗi token + phí giao dịch</li>
          </ul>
        </div>

        <button
          type="submit"
          className="btn-primary w-full flex items-center justify-center gap-2"
          disabled={isLoading || !tokenName || !description}
        >
          {isLoading ? (
            <>
              <span className="animate-spin">⏳</span>
              Đang xử lý...
            </>
          ) : (
            <>
              🚀 Mint NFT
            </>
          )}
        </button>
      </form>
    </div>
  );
}
