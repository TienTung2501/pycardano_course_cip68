/**
 * CIP-30 Wallet API Types
 * https://cips.cardano.org/cips/cip30/
 */

export interface CardanoWalletAPI {
  getNetworkId(): Promise<number>;
  getUtxos(amount?: string, paginate?: { page: number; limit: number }): Promise<string[] | undefined>;
  getBalance(): Promise<string>;
  getUsedAddresses(paginate?: { page: number; limit: number }): Promise<string[]>;
  getUnusedAddresses(): Promise<string[]>;
  getChangeAddress(): Promise<string>;
  getRewardAddresses(): Promise<string[]>;
  signTx(tx: string, partialSign?: boolean): Promise<string>;
  signData(addr: string, payload: string): Promise<{ signature: string; key: string }>;
  submitTx(tx: string): Promise<string>;
  getCollateral(params?: { amount?: string }): Promise<string[] | undefined>;
}

export interface CardanoWallet {
  name: string;
  icon: string;
  apiVersion: string;
  enable(): Promise<CardanoWalletAPI>;
  isEnabled(): Promise<boolean>;
}

export interface CardanoWindow {
  nami?: CardanoWallet;
  eternl?: CardanoWallet;
  lace?: CardanoWallet;
  flint?: CardanoWallet;
  yoroi?: CardanoWallet;
  gerowallet?: CardanoWallet;
  typhoncip30?: CardanoWallet;
  nufi?: CardanoWallet;
}

declare global {
  interface Window {
    cardano?: CardanoWindow;
  }
}

export interface WalletInfo {
  name: string;
  id: keyof CardanoWindow;
  icon: string;
  available: boolean;
}

// Supported wallets configuration
export const SUPPORTED_WALLETS: Omit<WalletInfo, 'available'>[] = [
  { name: 'Nami', id: 'nami', icon: '🦊' },
  { name: 'Eternl', id: 'eternl', icon: '🔮' },
  { name: 'Lace', id: 'lace', icon: '💎' },
  { name: 'Flint', id: 'flint', icon: '🔥' },
  { name: 'Yoroi', id: 'yoroi', icon: '🦋' },
  { name: 'Gero', id: 'gerowallet', icon: '🦍' },
  { name: 'Typhon', id: 'typhoncip30', icon: '🌪️' },
  { name: 'NuFi', id: 'nufi', icon: '🌟' },
];
