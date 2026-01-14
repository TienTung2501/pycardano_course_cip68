'use client';

import { useState, useEffect } from 'react';
import { useWallet } from '@/context/WalletContext';

interface UpdateFormProps {
  walletAddress: string;
  setTxStatus: (status: any) => void;
  scriptInfo: any;
}

export default function UpdateForm({ walletAddress, setTxStatus, scriptInfo }: UpdateFormProps) {
  const { signTx, connected } = useWallet();
  const [policyId, setPolicyId] = useState('');
  const [tokenName, setTokenName] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [currentMetadata, setCurrentMetadata] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(false);

  useEffect(() => {
    if (scriptInfo?.policy_id) {
      setPolicyId(scriptInfo.policy_id);
    }
  }, [scriptInfo]);

  const fetchCurrentMetadata = async () => {
    if (!policyId || !tokenName) return;

    try {
      setIsFetching(true);
      const response = await fetch(
        `http://localhost:8000/api/metadata/${policyId}/${tokenName}`
      );
      const data = await response.json();
      
      if (data.success) {
        console.log('Fetched metadata:', data);
        setCurrentMetadata(data);
        setNewDescription(data.metadata?.description || '');
      } else {
        setCurrentMetadata(null);
      }
    } catch (error) {
      console.error('Error fetching metadata:', error);
      setCurrentMetadata(null);
    } finally {
      setIsFetching(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!connected || !walletAddress) {
      setTxStatus({ status: 'error', message: 'Vui lòng kết nối ví trước!' });
      return;
    }

    try {
      setIsLoading(true);
      setTxStatus({ status: 'building', message: 'Đang tạo transaction update...' });

      // Call backend to convert hex address to bech32
      const addrRes = await fetch(`http://localhost:8000/api/convert-address?hex_address=${walletAddress}`);
      const addrData = await addrRes.json();
      const bech32Address = addrData.bech32_address || walletAddress;

      // 1. Request unsigned transaction from backend
      const response = await fetch('http://localhost:8000/api/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_address: bech32Address,
          policy_id: policyId,
          token_name: tokenName,
          new_description: newDescription,
        }),
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message);
      }

      setTxStatus({ status: 'signing', message: 'Vui lòng ký transaction trong ví...' });

      // 2. Sign transaction with wallet
      const witnessSet = await signTx(data.tx_cbor,true);

      setTxStatus({ status: 'submitting', message: 'Đang gửi transaction...' });

      // 3. Submit via backend
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

      setTxStatus({
        status: 'success',
        message: `Metadata đã được cập nhật thành công!`,
        txHash: txHash,
      });

      // Refresh metadata
      await fetchCurrentMetadata();

    } catch (error: any) {
      console.error('Update error:', error);
      setTxStatus({
        status: 'error',
        message: error.message || 'Có lỗi xảy ra khi update metadata',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        ✏️ Update Metadata
      </h2>
      <p className="text-gray-600 mb-6">
        Cập nhật metadata của CIP-68 NFT. Metadata được lưu trực tiếp on-chain 
        trong Reference Token, không ảnh hưởng đến định danh của User Token.
      </p>

      <form onSubmit={handleUpdate} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Policy ID
          </label>
          <input
            type="text"
            value={policyId}
            onChange={(e) => setPolicyId(e.target.value)}
            placeholder="Policy ID của NFT"
            className="input font-mono text-sm"
            required
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tên Token
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={tokenName}
              onChange={(e) => setTokenName(e.target.value)}
              placeholder="MyAwesomeNFT"
              className="input flex-1"
              required
              disabled={isLoading}
            />
            <button
              type="button"
              onClick={fetchCurrentMetadata}
              className="btn-secondary"
              disabled={isFetching || !policyId || !tokenName}
            >
              {isFetching ? '...' : '🔍'}
            </button>
          </div>
        </div>

        {currentMetadata && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="font-medium text-gray-800 mb-2">📋 Metadata hiện tại</h4>
            <div className="text-sm text-gray-600 space-y-1">
              <p><span className="font-medium">Description:</span> {currentMetadata.metadata?.description || 'N/A'}</p>
              <p><span className="font-medium">Version:</span> {currentMetadata.version}</p>
            </div>
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Mô tả mới
          </label>
          <textarea
            value={newDescription}
            onChange={(e) => setNewDescription(e.target.value)}
            placeholder="Nhập mô tả mới cho NFT..."
            className="input min-h-[100px]"
            required
            maxLength={256}
            disabled={isLoading}
          />
          <p className="text-xs text-gray-500 mt-1">
            Version sẽ tự động tăng khi update.
          </p>
        </div>

        <button
          type="submit"
          className="btn-primary w-full flex items-center justify-center gap-2"
          disabled={isLoading || !policyId || !tokenName || !newDescription}
        >
          {isLoading ? (
            <>
              <span className="animate-spin">⏳</span>
              Đang xử lý...
            </>
          ) : (
            <>
              ✅ Update Metadata
            </>
          )}
        </button>
      </form>
    </div>
  );
}
