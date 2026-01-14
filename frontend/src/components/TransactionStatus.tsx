'use client';

interface TransactionStatusProps {
  status: {
    status: 'idle' | 'building' | 'signing' | 'submitting' | 'success' | 'error';
    message: string;
    txHash?: string;
  };
}

export default function TransactionStatus({ status }: TransactionStatusProps) {
  if (status.status === 'idle') return null;

  const statusConfig = {
    building: {
      icon: '🔧',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      textColor: 'text-blue-800',
    },
    signing: {
      icon: '✍️',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      textColor: 'text-yellow-800',
    },
    submitting: {
      icon: '📤',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
      textColor: 'text-purple-800',
    },
    success: {
      icon: '✅',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      textColor: 'text-green-800',
    },
    error: {
      icon: '❌',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      textColor: 'text-red-800',
    },
    idle: {
      icon: '',
      bgColor: '',
      borderColor: '',
      textColor: '',
    },
  };

  const config = statusConfig[status.status];

  return (
    <div className={`mt-4 p-4 rounded-lg border ${config.bgColor} ${config.borderColor}`}>
      <div className="flex items-start gap-3">
        <span className="text-2xl">{config.icon}</span>
        <div className="flex-1">
          <p className={`font-medium ${config.textColor}`}>
            {status.message}
          </p>
          
          {status.txHash && (
            <div className="mt-2">
              <p className="text-sm text-gray-600 mb-1">Transaction Hash:</p>
              <div className="flex items-center gap-2">
                <code className="text-xs bg-white px-2 py-1 rounded border font-mono break-all">
                  {status.txHash}
                </code>
                <a
                  href={`https://preprod.cardanoscan.io/transaction/${status.txHash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-cardano-blue hover:underline text-sm whitespace-nowrap"
                >
                  🔗 View
                </a>
              </div>
            </div>
          )}

          {status.status === 'signing' && (
            <p className="text-sm mt-2 text-yellow-700">
              Kiểm tra popup từ ví của bạn để ký transaction.
            </p>
          )}

          {(status.status === 'building' || status.status === 'submitting') && (
            <div className="mt-2 flex items-center gap-2">
              <div className="animate-spin w-4 h-4 border-2 border-current border-t-transparent rounded-full"></div>
              <span className="text-sm">Đang xử lý...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
