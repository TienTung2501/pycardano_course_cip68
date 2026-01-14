'use client';

import { useState } from 'react';
import Modal from './Modal';
import { useWallet } from '@/context/WalletContext';

interface BurnModalProps {
  isOpen: boolean;
  onClose: () => void;
  policyId: string;
  tokenName: string;
  onSuccess: () => void;
  setTxStatus: (status: any) => void;
}

export default function BurnModal({
  isOpen,
  onClose,
  policyId,
  tokenName,
  onSuccess,
  setTxStatus
}: BurnModalProps) {
  const { signTx, connected, walletAddress } = useWallet();
  const [confirmed, setConfirmed] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleBurn = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!connected || !walletAddress) {
      setTxStatus({ status: 'error', message: 'Vui lòng kết nối ví trước!' });
      return;
    }

    if (!confirmed) {
      setTxStatus({ status: 'error', message: 'Vui lòng xác nhận trước khi burn!' });
      return;
    }

    try {
      setIsLoading(true);
      setTxStatus({ status: 'building', message: 'Đang tạo transaction burn...' });

      // Call backend to convert hex address to bech32
      const addrRes = await fetch(`http://localhost:8000/api/convert-address?hex_address=${walletAddress}`);
      const addrData = await addrRes.json();
      const bech32Address = addrData.bech32_address || walletAddress;

      // Request unsigned transaction from backend (no seed UTxO needed for simplified version)
      const response = await fetch('http://localhost:8000/api/burn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_address: bech32Address,
          policy_id: policyId,
          token_name: tokenName,
        }),
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message);
      }

      setTxStatus({ status: 'signing', message: 'Vui lòng ký transaction trong ví...' });

      // 2. Sign transaction with wallet
      const witnessSet = await signTx(data.tx_cbor);

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
        message: `NFT "${tokenName}" đã được burn thành công!`,
        txHash: txHash,
      });

      // Remove from localStorage
      localStorage.removeItem(`nft_${tokenName}`);

      // Trigger refresh with delay to allow blockchain to process
      setTimeout(() => {
        onSuccess();
      }, 2000);
      
      onClose();

    } catch (error: any) {
      console.error('Burn error:', error);
      setTxStatus({
        status: 'error',
        message: error.message || 'Có lỗi xảy ra khi burn NFT',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="🔥 Burn NFT">
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
        <h4 className="font-medium text-red-800 mb-2">⚠️ Cảnh báo</h4>
        <ul className="text-sm text-red-700 space-y-1">
          <li>• Hành động này KHÔNG THỂ hoàn tác</li>
          <li>• Cả Reference Token và User Token sẽ bị xóa vĩnh viễn</li>
          <li>• Metadata on-chain sẽ bị mất</li>
          <li>• Bạn cần sở hữu cả 2 tokens để burn</li>
        </ul>
      </div>

      <form onSubmit={handleBurn} className="space-y-4">
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

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-800 mb-2">ℹ️ Điều kiện Burn</h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• Bạn phải sở hữu cả Reference Token và User Token</li>
            <li>• Cả 2 tokens sẽ được đốt trong cùng 1 transaction</li>
            <li>• Không cần seed UTxO vì sử dụng fixed policy ID</li>
          </ul>
        </div>

        <div className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
          <input
            type="checkbox"
            id="confirm-burn"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
            className="mt-1 w-4 h-4 text-red-600 rounded focus:ring-red-500"
            disabled={isLoading}
          />
          <label htmlFor="confirm-burn" className="text-sm text-gray-700">
            Tôi hiểu rằng việc burn NFT là vĩnh viễn và không thể hoàn tác. 
            Tôi muốn tiếp tục burn NFT này.
          </label>
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
            className="flex-1 btn-danger flex items-center justify-center gap-2"
            disabled={isLoading || !confirmed}
          >
            {isLoading ? (
              <>
                <span className="animate-spin">⏳</span>
                Đang xử lý...
              </>
            ) : (
              <>
                🔥 Burn NFT
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
