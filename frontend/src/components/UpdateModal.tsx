'use client';

import { useState } from 'react';
import Modal from './Modal';
import { useWallet } from '@/context/WalletContext';

interface UpdateModalProps {
  isOpen: boolean;
  onClose: () => void;
  policyId: string;
  tokenName: string;
  currentDescription: string;
  onSuccess: () => void;
  setTxStatus: (status: any) => void;
}

export default function UpdateModal({
  isOpen,
  onClose,
  policyId,
  tokenName,
  currentDescription,
  onSuccess,
  setTxStatus
}: UpdateModalProps) {
  const { signTx, connected, walletAddress } = useWallet();
  const [newDescription, setNewDescription] = useState(currentDescription);
  const [isLoading, setIsLoading] = useState(false);

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

      // Request unsigned transaction from backend
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

      // Trigger refresh with delay to allow blockchain to process
      setTimeout(() => {
        onSuccess();
      }, 2000);
      
      onClose();

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
    <Modal isOpen={isOpen} onClose={onClose} title="✏️ Update Metadata">
      <form onSubmit={handleUpdate} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Policy ID
          </label>
          <input
            type="text"
            value={policyId}
            readOnly
            className="input bg-gray-50 font-mono text-sm cursor-not-allowed"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tên Token
          </label>
          <input
            type="text"
            value={tokenName}
            readOnly
            className="input bg-gray-50 cursor-not-allowed"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Mô tả hiện tại
          </label>
          <textarea
            value={currentDescription}
            readOnly
            className="input min-h-[80px] bg-gray-50 cursor-not-allowed text-gray-500"
          />
        </div>

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

        <div className="flex gap-3 pt-4">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-lg transition-colors font-medium"
            disabled={isLoading}
          >
            Hủy
          </button>
          <button
            type="submit"
            className="flex-1 btn-primary flex items-center justify-center gap-2"
            disabled={isLoading || !newDescription || newDescription === currentDescription}
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
        </div>
      </form>
    </Modal>
  );
}
