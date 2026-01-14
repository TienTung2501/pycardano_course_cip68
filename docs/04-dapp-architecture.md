# Bài 4: Kiến trúc dApp

## 🏗️ Tổng quan kiến trúc

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                          │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌────────────────┐     │
│  │ MintForm  │ │UpdateForm │ │ BurnForm  │ │    NFTList     │     │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └───────┬────────┘     │
│        │             │             │               │               │
│        └─────────────┴─────────────┴───────────────┘               │
│                              │                                      │
│                    ┌─────────▼─────────┐                           │
│                    │   Wallet (Mesh)   │                           │
│                    └─────────┬─────────┘                           │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │    Backend (FastAPI) │
                    │                      │
                    │  /api/mint           │
                    │  /api/update         │
                    │  /api/burn           │
                    │  /api/submit         │
                    │  /api/metadata       │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
     ┌────────▼────────┐ ┌─────▼─────┐ ┌───────▼───────┐
     │   Blockfrost    │ │ PyCardano │ │ Smart Contract│
     │   (Queries)     │ │ (Tx Build)│ │ (On-chain)    │
     └────────┬────────┘ └─────┬─────┘ └───────────────┘
              │                │
              └────────┬───────┘
                       │
              ┌────────▼────────┐
              │     Cardano     │
              │    Blockchain   │
              │    (Preprod)    │
              └─────────────────┘
```

## 🔄 Luồng hoạt động

### 1. Mint Flow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Frontend │     │ Backend  │     │ Wallet   │     │Blockchain│
└────┬─────┘     └────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │                │
     │ 1. User fills  │                │                │
     │    mint form   │                │                │
     │                │                │                │
     │ 2. POST /api/mint               │                │
     │ (token_name,   │                │                │
     │  metadata,     │                │                │
     │  wallet_addr)  │                │                │
     ├───────────────►│                │                │
     │                │                │                │
     │                │ 3. Build       │                │
     │                │    unsigned tx │                │
     │                │                │                │
     │ 4. Return      │                │                │
     │    unsigned tx │                │                │
     │◄───────────────┤                │                │
     │                │                │                │
     │ 5. Sign tx     │                │                │
     │    with wallet │                │                │
     ├────────────────────────────────►│                │
     │                │                │                │
     │ 6. Signed tx   │                │                │
     │◄────────────────────────────────┤                │
     │                │                │                │
     │ 7. POST /api/submit             │                │
     │    (signed_tx) │                │                │
     ├───────────────►│                │                │
     │                │                │                │
     │                │ 8. Submit tx   │                │
     │                ├───────────────────────────────►│
     │                │                │                │
     │                │ 9. Tx hash     │                │
     │                │◄───────────────────────────────┤
     │                │                │                │
     │ 10. Success    │                │                │
     │◄───────────────┤                │                │
     │                │                │                │
```

### 2. Update Flow

```
1. Frontend: GET /api/metadata/{policy_id}/{token_name}
   → Lấy metadata hiện tại

2. Frontend: Hiển thị form với metadata cũ

3. User: Chỉnh sửa metadata

4. Frontend: POST /api/update
   → Backend tạo update transaction

5. Wallet: Sign transaction

6. Frontend: POST /api/submit
   → Submit lên blockchain
```

## 📁 Cấu trúc Frontend

```
frontend/
├── src/
│   ├── app/
│   │   ├── globals.css      # Tailwind styles
│   │   ├── layout.tsx       # Root layout
│   │   └── page.tsx         # Main page
│   │
│   └── components/
│       ├── Providers.tsx        # Mesh providers
│       ├── WalletConnect.tsx    # Wallet button
│       ├── MintForm.tsx         # Mint NFT form
│       ├── UpdateForm.tsx       # Update metadata
│       ├── BurnForm.tsx         # Burn NFT
│       ├── NFTList.tsx          # Display NFTs
│       └── TransactionStatus.tsx # Tx status
│
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── next.config.js
```

## 🔌 Mesh SDK Integration

### Providers

```tsx
'use client';
import { MeshProvider } from "@meshsdk/react";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <MeshProvider>
      {children}
    </MeshProvider>
  );
}
```

### Wallet Connection

```tsx
import { CardanoWallet, useWallet } from "@meshsdk/react";

export function WalletConnect() {
  const { connected, wallet } = useWallet();
  
  return (
    <div>
      {!connected && <CardanoWallet />}
      {connected && <p>Connected!</p>}
    </div>
  );
}
```

### Sign Transaction

```tsx
import { useWallet } from "@meshsdk/react";
import { Transaction } from "@meshsdk/core";

async function signAndSubmit(unsignedTx: string) {
  const { wallet } = useWallet();
  
  // Deserialize transaction
  const tx = Transaction.fromCBOR(unsignedTx);
  
  // Sign with wallet
  const signedTx = await wallet.signTx(tx);
  
  // Submit via backend
  const response = await fetch('/api/submit', {
    method: 'POST',
    body: JSON.stringify({ signed_tx: signedTx }),
  });
  
  return await response.json();
}
```

## 🖥️ Backend API

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/mint | Tạo mint transaction |
| POST | /api/update | Tạo update transaction |
| POST | /api/burn | Tạo burn transaction |
| POST | /api/submit | Submit signed tx |
| GET | /api/metadata/{policy_id}/{token_name} | Query metadata |

### Request/Response Format

**Mint Request:**
```json
{
  "wallet_address": "addr_test1...",
  "token_name": "MyNFT",
  "description": "My first CIP-68 NFT",
  "metadata": {
    "name": "MyNFT",
    "image": "ipfs://..."
  }
}
```

**Response:**
```json
{
  "success": true,
  "unsigned_tx": "84a4...",
  "policy_id": "18b1e6ec...",
  "ref_asset": "000643b04d794e4654",
  "user_asset": "000de1404d794e4654"
}
```

## 📦 Smart Contract Integration

### Load Script from Blueprint

```python
import json

def load_scripts():
    with open("smart_contract/plutus.json", "r") as f:
        blueprint = json.load(f)
    
    validators = blueprint["validators"]
    
    mint_script = None
    store_script = None
    
    for v in validators:
        if "mint" in v["title"]:
            compiled = v["compiledCode"]
            mint_script = PlutusV3Script(bytes.fromhex(compiled))
        elif "store" in v["title"]:
            compiled = v["compiledCode"]
            store_script = PlutusV3Script(bytes.fromhex(compiled))
    
    return mint_script, store_script
```

### Policy ID Calculation

```python
from pycardano import plutus_script_hash

policy_id = plutus_script_hash(mint_script)
print(f"Policy ID: {policy_id.to_primitive().hex()}")
```

## 🛠️ Development Setup

### 1. Backend

```bash
# Cài đặt dependencies
cd backend
pip install -r ../requirements.txt

# Chạy server
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
# Cài đặt dependencies
cd frontend
npm install

# Chạy dev server
npm run dev
```

### 3. Truy cập

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 🔒 Security Considerations

1. **Private Keys**: Never expose private keys to frontend
2. **Transaction Building**: Always build on backend
3. **Validation**: Validate all inputs on backend
4. **CORS**: Configure properly for production
5. **Rate Limiting**: Implement for API endpoints

## 🧪 Testing Checklist

- [ ] Connect wallet (Nami, Eternl, Flint)
- [ ] Mint new CIP-68 token
- [ ] View minted tokens
- [ ] Update token metadata
- [ ] Burn token
- [ ] Error handling

## 📚 Resources

- [MeshSDK Docs](https://meshjs.dev/apis)
- [PyCardano Docs](https://pycardano.readthedocs.io/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Next.js Docs](https://nextjs.org/docs)

---

*Đây là bài cuối của series. Chúc bạn thành công với dApp CIP-68!*
