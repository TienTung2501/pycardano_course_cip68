'use client';

import { useState, useEffect } from 'react';
import UpdateModal from './UpdateModal';
import BurnModal from './BurnModal';

interface NFTListProps {
  walletAddress: string;
  scriptInfo: any;
  setTxStatus: (status: any) => void;
}

interface NFTAsset {
  policy_id: string;
  asset_name: string;
  quantity: number;
  token_name?: string;
  type?: 'reference' | 'user';
}

interface NFTMetadata {
  description?: string;
  version?: number;
}

export default function NFTList({ walletAddress, scriptInfo, setTxStatus }: NFTListProps) {
  const [assets, setAssets] = useState<NFTAsset[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedNFT, setSelectedNFT] = useState<{ policyId: string; tokenName: string; description: string } | null>(null);
  const [showUpdateModal, setShowUpdateModal] = useState(false);
  const [showBurnModal, setShowBurnModal] = useState(false);
  const [metadataCache, setMetadataCache] = useState<Record<string, NFTMetadata>>({});
  const [isLoadingMetadata, setIsLoadingMetadata] = useState(false);

  const CIP68_REFERENCE_PREFIX = '000643b0';
  const CIP68_USER_PREFIX = '000de140';
  
  // Fixed Policy ID from platform (from cip68_utils.py)
  const PLATFORM_POLICY_ID = '9a97fb710a29382d31d9d2a40faab64e5c8be912419a806425bfc7d4';

  const fetchAssets = async () => {
    if (!walletAddress) return;

    try {
      setIsLoading(true);
      const response = await fetch(`http://localhost:8000/api/wallet/${walletAddress}`);
      const data = await response.json();

      if (data.success) {
        // Filter CIP-68 assets from this platform only (by policy ID)
        const cip68Assets = data.assets
          .filter((asset: NFTAsset) => {
            // Only show NFTs from this platform's policy ID
            const isFromPlatform = asset.policy_id === PLATFORM_POLICY_ID;
            const isCIP68 = asset.asset_name.startsWith(CIP68_REFERENCE_PREFIX) ||
                           asset.asset_name.startsWith(CIP68_USER_PREFIX);
            return isFromPlatform && isCIP68;
          })
          .map((asset: NFTAsset) => {
            let type: 'reference' | 'user' = 'user';
            let tokenName = asset.asset_name;

            if (asset.asset_name.startsWith(CIP68_REFERENCE_PREFIX)) {
              type = 'reference';
              tokenName = asset.asset_name.slice(CIP68_REFERENCE_PREFIX.length);
            } else if (asset.asset_name.startsWith(CIP68_USER_PREFIX)) {
              type = 'user';
              tokenName = asset.asset_name.slice(CIP68_USER_PREFIX.length);
            }

            // Convert hex to string
            try {
              tokenName = Buffer.from(tokenName, 'hex').toString('utf8');
            } catch {
              // Keep as hex if conversion fails
            }

            return {
              ...asset,
              type,
              token_name: tokenName,
            };
          });

        setAssets(cip68Assets);
        
        // Auto-load metadata for all user tokens
        await loadAllMetadata(cip68Assets);
      }
    } catch (error) {
      console.error('Error fetching assets:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Load metadata for all NFTs automatically
  const loadAllMetadata = async (assetList: NFTAsset[]) => {
    const userTokens = assetList.filter(a => a.type === 'user');
    if (userTokens.length === 0) return;
    
    setIsLoadingMetadata(true);
    const metadataPromises = userTokens.map(async (asset) => {
      const cacheKey = `${asset.policy_id}-${asset.token_name}`;
      if (!metadataCache[cacheKey]) {
        return fetchMetadata(asset.policy_id, asset.token_name || '');
      }
    });
    
    await Promise.all(metadataPromises);
    setIsLoadingMetadata(false);
  };

  useEffect(() => {
    fetchAssets();
    
    // Auto refresh every 30 seconds
    const interval = setInterval(fetchAssets, 30000);
    return () => clearInterval(interval);
  }, [walletAddress]);

  // Fetch metadata for each NFT
  const fetchMetadata = async (policyId: string, tokenName: string) => {
    const cacheKey = `${policyId}-${tokenName}`;
    if (metadataCache[cacheKey]) return metadataCache[cacheKey];

    try {
      // Backend endpoint only needs token_name (uses fixed policy ID)
      const response = await fetch(`http://localhost:8000/api/metadata/${tokenName}`);
      const data = await response.json();
      
      if (data.success && data.metadata) {
        const metadata = { 
          description: data.metadata.description || 'No description', 
          version: data.version || 0 
        };
        setMetadataCache(prev => ({ ...prev, [cacheKey]: metadata }));
        return metadata;
      }
    } catch (error) {
      console.error('Error fetching metadata:', error);
    }
    return { description: 'N/A', version: 0 };
  };

  const handleUpdateClick = async (policyId: string, tokenName: string) => {
    const metadata = await fetchMetadata(policyId, tokenName);
    setSelectedNFT({
      policyId,
      tokenName,
      description: metadata.description || ''
    });
    setShowUpdateModal(true);
  };

  const handleBurnClick = (policyId: string, tokenName: string) => {
    setSelectedNFT({
      policyId,
      tokenName,
      description: ''
    });
    setShowBurnModal(true);
  };

  const handleModalClose = () => {
    setShowUpdateModal(false);
    setShowBurnModal(false);
    setSelectedNFT(null);
  };

  const handleSuccess = () => {
    // Clear metadata cache for refreshed data
    setMetadataCache({});
    // Reload assets and metadata
    fetchAssets();
  };

  const userTokens = assets.filter(a => a.type === 'user');

  return (
    <div className="card h-fit">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-gray-800">
          🖼️ My CIP-68 NFTs
        </h3>
        <button
          onClick={fetchAssets}
          className="text-sm text-cardano-blue hover:underline"
          disabled={isLoading}
        >
          {isLoading ? '⏳' : '🔄'} Refresh
        </button>
      </div>

      {isLoading && assets.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <span className="animate-spin text-2xl">⏳</span>
          <p className="mt-2">Đang tải NFT...</p>
        </div>
      ) : userTokens.length === 0 ? (
        <div className="text-center py-8">
          <div className="text-4xl mb-2">📭</div>
          <p className="text-gray-500">Chưa có CIP-68 NFT nào từ platform này</p>
          <p className="text-sm text-gray-400 mt-1">
            Mint NFT đầu tiên của bạn!
          </p>
        </div>
      ) : (
        <>
          {isLoadingMetadata && (
            <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded text-sm text-blue-700 flex items-center gap-2">
              <span className="animate-spin">⏳</span>
              Đang tải metadata...
            </div>
          )}
          <div className="space-y-3">{userTokens.map((asset, index) => {
            const cacheKey = `${asset.policy_id}-${asset.token_name}`;
            const metadata = metadataCache[cacheKey];
            
            return (
              <div
                key={`${asset.policy_id}-${asset.asset_name}-${index}`}
                className="border border-gray-200 rounded-lg p-4 hover:border-cardano-blue transition-colors"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-800 text-lg">
                      {asset.token_name}
                    </h4>
                    <p className="text-xs text-gray-500 mt-1 font-mono">
                      {asset.policy_id.slice(0, 8)}...{asset.policy_id.slice(-8)}
                    </p>
                    {metadata ? (
                      <div className="mt-2 text-sm text-gray-600">
                        <p className="line-clamp-2">{metadata.description || 'No description'}</p>
                        <p className="text-xs text-gray-400 mt-1">Version: {metadata.version || 0}</p>
                      </div>
                    ) : (
                      <div className="mt-2 text-sm text-gray-400 flex items-center gap-1">
                        <span className="animate-spin">⏳</span>
                        Loading metadata...
                      </div>
                    )}
                  </div>
                  <span className="badge badge-success ml-2">
                    User Token
                  </span>
                </div>
                
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={() => handleUpdateClick(asset.policy_id, asset.token_name || '')}
                    className="flex-1 min-w-[120px] px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                    disabled={!metadata}
                    title={!metadata ? 'Đang tải metadata...' : 'Update metadata'}
                  >
                    ✏️ Update
                  </button>
                  <button
                    onClick={() => handleBurnClick(asset.policy_id, asset.token_name || '')}
                    className="flex-1 min-w-[120px] px-3 py-2 bg-red-500 hover:bg-red-600 text-white text-sm rounded-lg transition-colors font-medium"
                  >
                    🔥 Burn
                  </button>
                </div>
                
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <a
                    href={`https://preprod.cardanoscan.io/token/${asset.policy_id}${asset.asset_name}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-cardano-blue hover:underline"
                  >
                    🔍 View on CardanoScan
                  </a>
                </div>
              </div>
            );
          })}
          </div>
        </>
      )}

      {scriptInfo && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            <span className="font-medium">Policy ID:</span>
            <br />
            <span className="font-mono break-all">{scriptInfo.policy_id}</span>
          </p>
        </div>
      )}

      {/* Modals */}
      {selectedNFT && (
        <>
          <UpdateModal
            isOpen={showUpdateModal}
            onClose={handleModalClose}
            policyId={selectedNFT.policyId}
            tokenName={selectedNFT.tokenName}
            currentDescription={selectedNFT.description}
            onSuccess={handleSuccess}
            setTxStatus={setTxStatus}
          />
          <BurnModal
            isOpen={showBurnModal}
            onClose={handleModalClose}
            policyId={selectedNFT.policyId}
            tokenName={selectedNFT.tokenName}
            onSuccess={handleSuccess}
            setTxStatus={setTxStatus}
          />
        </>
      )}
    </div>
  );
}
