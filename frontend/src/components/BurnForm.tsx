'use client';

import { useState, useEffect } from 'react';
import { useWallet } from '@/context/WalletContext';

interface BurnFormProps {
  walletAddress: string;
  setTxStatus: (status: any) => void;
  scriptInfo: any;
}

export default function BurnForm({ walletAddress, setTxStatus, scriptInfo }: BurnFormProps) {
  const { signTx, connected } = useWallet();
  const [policyId, setPolicyId] = useState('');
  const [tokenName, setTokenName] = useState('');
  const [seedUtxoTxId, setSeedUtxoTxId] = useState('');
  const [seedUtxoIndex, setSeedUtxoIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [confirmed, setConfirmed] = useState(false);

  // Auto-fill from localStorage when token name changes
  useEffect(() => {
    if (tokenName) {
      const savedInfo = localStorage.getItem(`nft_${tokenName}`);
      if (savedInfo) {
        try {
          const info = JSON.parse(savedInfo);
          setPolicyId(info.policy_id || '');
          // Try to get seed_utxo from transaction (first input)
          // Note: This is a simplification - in production you'd query the tx
        } catch (e) {
          console.error('Failed to parse saved NFT info:', e);
        }
      }
    }
  }, [tokenName]);

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

      // Validate seed_utxo info
      if (!seedUtxoTxId || seedUtxoTxId.length !== 64) {
        throw new Error('Seed UTxO TX ID không hợp lệ (cần 64 ký tự hex)');
      }

      // Call backend to convert hex address to bech32
      const addrRes = await fetch(`http://localhost:8000/api/convert-address?hex_address=${walletAddress}`);
      const addrData = await addrRes.json();
      const bech32Address = addrData.bech32_address || walletAddress;

      // 1. Request unsigned transaction from backend
      const response = await fetch('http://localhost:8000/api/burn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          wallet_address: bech32Address,
          policy_id: policyId,
          token_name: tokenName,
          seed_utxo_tx_id: seedUtxoTxId,
          seed_utxo_index: seedUtxoIndex,
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

      // Reset form
      setTokenName('');
      setConfirmed(false);

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
    <div>
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        🔥 Burn CIP-68 NFT
      </h2>
      <p className="text-gray-600 mb-6">
        Đốt NFT vĩnh viễn. Cả Reference Token và User Token sẽ bị burn. 
        Hành động này không thể hoàn tác.
      </p>

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
          <input
            type="text"
            value={tokenName}
            onChange={(e) => setTokenName(e.target.value)}
            placeholder="MyAwesomeNFT"
            className="input"
            required
            disabled={isLoading}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Seed UTxO TX ID
          </label>
          <input
            type="text"
            value={seedUtxoTxId}
            onChange={(e) => setSeedUtxoTxId(e.target.value)}
            placeholder="Transaction ID của seed UTxO (64 ký tự hex)"
            className="input font-mono text-sm"
            required
            maxLength={64}
            disabled={isLoading}
          />
          <p className="text-xs text-gray-500 mt-1">
            TX ID của UTxO đầu tiên được dùng khi mint. Kiểm tra transaction mint trên explorer.
          </p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Seed UTxO Index
          </label>
          <input
            type="number"
            value={seedUtxoIndex}
            onChange={(e) => setSeedUtxoIndex(parseInt(e.target.value) || 0)}
            placeholder="0"
            className="input"
            required
            min={0}
            disabled={isLoading}
          />
          <p className="text-xs text-gray-500 mt-1">
            Thường là 0 (output đầu tiên)
          </p>
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

        <button
          type="submit"
          className="btn-danger w-full flex items-center justify-center gap-2"
          disabled={isLoading || !policyId || !tokenName || !confirmed}
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
      </form>
    </div>
  );
}
