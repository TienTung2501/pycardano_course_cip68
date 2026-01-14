# 📖 Tài liệu Dự án CIP-68 Dynamic Asset Platform

## 🎯 Tổng quan

Dự án này là một nền tảng hoàn chỉnh để tạo, quản lý và cập nhật CIP-68 Dynamic NFT trên Cardano blockchain. Dự án bao gồm smart contract (Aiken), backend API (FastAPI + PyCardano), và frontend web application (Next.js + React).

### Tính năng chính

- ✅ **Mint CIP-68 NFT**: Tạo NFT với metadata động có thể cập nhật
- ✅ **Update Metadata**: Cập nhật mô tả và metadata của NFT
- ✅ **Burn NFT**: Xóa NFT và thu hồi ADA
- ✅ **Auto-refresh**: Tự động cập nhật danh sách NFT sau các thao tác
- ✅ **Filter by Platform**: Chỉ hiển thị NFT từ nền tảng này
- ✅ **Browser Wallet Integration**: Hỗ trợ Nami, Eternl, Lace, Flint

---

## 🏗️ Kiến trúc Hệ thống

### 1. Smart Contract Layer (Aiken)

**Location**: `smart_contract/validators/cip68.ak`

Gồm 2 validators:

#### a) Minting Policy (`cip68_mint`)
- **Chức năng**: Kiểm soát việc mint và burn CIP-68 tokens
- **Redeemers**:
  - `MintToken`: Cho phép mint reference token (000643b0) và user token (000de140)
  - `BurnToken`: Cho phép burn cả 2 tokens
- **Policy ID cố định**: `9a97fb710a29382d31d9d2a40faab64e5c8be912419a806425bfc7d4`

#### b) Spending Validator (`cip68_store`)
- **Chức năng**: Quản lý reference token chứa metadata
- **Redeemers**:
  - `UpdateMetadata`: Cập nhật metadata (tăng version)
  - `BurnReference`: Burn reference token khi burn NFT
- **Store Address cố định**: `addr_test1...` (script address)

### 2. Off-chain Layer (PyCardano)

**Location**: `offchain/`

#### Cấu trúc Datum (CIP68Datum)
```python
@dataclass
class CIP68Datum(PlutusData):
    policy_id: bytes          # 28 bytes
    asset_name: bytes         # Tên token (không có prefix)
    owner: bytes              # Owner PKH (28 bytes)
    metadata: Dict[bytes, Any]  # Key-value metadata
    version: int              # Phiên bản metadata
```

#### Utility Functions (`cip68_utils.py`)
- `create_cip68_asset_names()`: Tạo reference và user token names
- `create_cip68_datum()`: Tạo datum với metadata
- `load_mint_script()`, `load_store_script()`: Load compiled scripts
- `get_fixed_policy_id()`, `get_fixed_store_address()`: Lấy địa chỉ cố định

### 3. Backend API Layer (FastAPI)

**Location**: `backend/main.py`

Cung cấp REST API để tạo unsigned transactions:

#### API Endpoints

##### 1. `GET /api/script-info`
- Trả về thông tin về script (policy ID, network)
- Không cần tham số

##### 2. `POST /api/mint`
- Tạo transaction mint CIP-68 NFT
- **Body**:
  ```json
  {
    "wallet_address": "addr_test1...",
    "token_name": "MyNFT",
    "description": "Description of my NFT"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Transaction built successfully",
    "tx_cbor": "84a400...",
    "policy_id": "9a97fb..."
  }
  ```

##### 3. `POST /api/update`
- Tạo transaction cập nhật metadata
- **Body**:
  ```json
  {
    "wallet_address": "addr_test1...",
    "token_name": "MyNFT",
    "new_description": "Updated description"
  }
  ```

##### 4. `POST /api/burn`
- Tạo transaction burn NFT
- **Body**:
  ```json
  {
    "wallet_address": "addr_test1...",
    "token_name": "MyNFT"
  }
  ```

##### 5. `POST /api/submit`
- Submit signed transaction lên blockchain
- **Body**:
  ```json
  {
    "tx_cbor": "84a400...",
    "witness_set_cbor": "a100..."
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Transaction submitted",
    "tx_hash": "abc123..."
  }
  ```

##### 6. `GET /api/wallet/{address}`
- Lấy thông tin ví và danh sách assets
- **Response**:
  ```json
  {
    "success": true,
    "address": "addr_test1...",
    "balance_lovelace": 10000000,
    "assets": [
      {
        "policy_id": "9a97fb...",
        "asset_name": "000de140...",
        "quantity": 1
      }
    ]
  }
  ```

##### 7. `GET /api/metadata/{token_name}`
- Lấy metadata của NFT
- **Response**:
  ```json
  {
    "success": true,
    "metadata": {
      "description": "My NFT description"
    },
    "version": 2
  }
  ```

### 4. Frontend Layer (Next.js + React)

**Location**: `frontend/src/`

#### Component Architecture

##### Core Components

1. **HomeContent.tsx**
   - Component chính quản lý state
   - Xử lý wallet connection
   - Điều phối các component con

2. **WalletConnect.tsx**
   - Kết nối browser wallet
   - Hiển thị địa chỉ và số dư
   - Xử lý disconnect

3. **MintForm.tsx**
   - Form nhập thông tin mint NFT
   - Validation input
   - Gọi API mint và submit
   - Auto-refresh NFT list sau khi mint thành công

4. **NFTList.tsx**
   - Hiển thị danh sách NFT của user
   - **Auto-load metadata**: Tự động fetch metadata khi load
   - **Filter by platform**: Chỉ hiển thị NFT từ policy ID của platform
   - Hiển thị trạng thái loading khi fetch metadata
   - Buttons: Update, Burn
   - Auto-refresh mỗi 30 giây

5. **UpdateModal.tsx**
   - Modal cập nhật metadata
   - Hiển thị metadata hiện tại
   - Form nhập metadata mới
   - Auto-refresh sau update thành công

6. **BurnModal.tsx**
   - Modal xác nhận burn NFT
   - Cảnh báo về tính không thể hoàn tác
   - Auto-refresh sau burn thành công

7. **TransactionStatus.tsx**
   - Hiển thị trạng thái transaction
   - States: idle, building, signing, submitting, success, error
   - Link tới CardanoScan khi thành công

#### State Management

```typescript
// Transaction status tracking
const [txStatus, setTxStatus] = useState<{
  status: 'idle' | 'building' | 'signing' | 'submitting' | 'success' | 'error';
  message: string;
  txHash?: string;
}>({ status: 'idle', message: '' });

// NFT list refresh trigger
const [refreshNFTList, setRefreshNFTList] = useState(0);
const handleRefreshNFTList = () => setRefreshNFTList(prev => prev + 1);
```

---

## 🔄 Luồng Giao dịch (Transaction Flow)

### 1. Mint NFT Flow

```
┌─────────┐     ┌──────────┐     ┌─────────┐     ┌────────────┐
│ Frontend│────▶│ Backend  │────▶│PyCardano│────▶│Browser     │
│         │     │ (Build)  │     │(Unsigned│     │Wallet (Sign│
└─────────┘     └──────────┘     │  TX)    │     │  TX)       │
     │                                │              │
     │                                ▼              │
     │          ┌──────────────────────────────────┐ │
     │          │ Unsigned Transaction (CBOR)      │ │
     │          │ - Inputs: User UTxOs             │ │
     │          │ - Outputs:                       │ │
     │          │   * Reference Token → Store      │ │
     │          │   * User Token → User            │ │
     │          │ - Mint: +1 ref, +1 user         │ │
     │          │ - Script: Mint redeemer         │ │
     │          └──────────────────────────────────┘ │
     │                                                ▼
     │          ┌──────────────────────────────────┐
     └─────────▶│ Witness Set (CBOR)               │
                │ - Wallet signature                │
                └──────────────────────────────────┘
                         │
                         ▼
                ┌──────────────┐
                │ Submit to    │
                │ Blockchain   │
                └──────────────┘
                         │
                         ▼
                ┌──────────────┐
                │ Wait ~20s    │
                │ Auto Refresh │
                └──────────────┘
```

### 2. Update Metadata Flow

```
Frontend ─────▶ Backend ─────▶ PyCardano
   │              │              │
   │              │              ▼
   │              │     Find Reference Token UTxO
   │              │     Create Update Transaction:
   │              │     - Spend ref token (UpdateMetadata redeemer)
   │              │     - Output ref token with new datum (version++)
   │              │     - Require owner signature
   │              │              │
   │              ◀──────────────┘
   │              │
   │   ◀─────────┘
   │   Unsigned TX CBOR
   │
   ▼
Wallet signs ───▶ Submit ───▶ Blockchain ───▶ Auto Refresh (2s delay)
```

### 3. Burn NFT Flow

```
Frontend ─────▶ Backend ─────▶ PyCardano
   │              │              │
   │              │              ▼
   │              │     Find both tokens (ref & user)
   │              │     Create Burn Transaction:
   │              │     - Spend ref token (BurnReference redeemer)
   │              │     - Burn both tokens (BurnToken redeemer)
   │              │     - Require owner signature
   │              │              │
   │              ◀──────────────┘
   │              │
   │   ◀─────────┘
   │   Unsigned TX CBOR
   │
   ▼
Wallet signs ───▶ Submit ───▶ Blockchain ───▶ Auto Refresh (2s delay)
```

---

## ⚙️ Setup và Cài đặt

### 1. Prerequisites

- **Node.js** >= 18.x
- **Python** >= 3.9
- **Aiken** >= 1.0.0 (optional, chỉ cần nếu compile lại contract)
- **Blockfrost API Key** (Preprod network)
- **Browser Wallet** (Nami, Eternl, Lace, hoặc Flint)

### 2. Backend Setup

```bash
# 1. Tạo virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Cài đặt dependencies
pip install -r ../requirements.txt

# 3. Tạo file .env
cat > .env << EOF
NETWORK=Preprod
BLOCKFROST_URL=https://cardano-preprod.blockfrost.io/api
BLOCKFROST_API_KEY=your_blockfrost_api_key_here
EOF

# 4. Chạy backend
python run_backend.py
# hoặc
uvicorn backend.main:app --reload --port 8000
```

Backend sẽ chạy tại: `http://localhost:8000`

### 3. Frontend Setup

```bash
# 1. Di chuyển vào thư mục frontend
cd frontend

# 2. Cài đặt dependencies
npm install
# hoặc
yarn install

# 3. Chạy development server
npm run dev
# hoặc
yarn dev
```

Frontend sẽ chạy tại: `http://localhost:3000`

### 4. Smart Contract (Optional - nếu cần compile lại)

```bash
cd smart_contract
aiken build
```

File `plutus.json` sẽ được tạo tự động.

---

## 🚀 Cách sử dụng

### 1. Khởi động hệ thống

```bash
# Terminal 1 - Backend
cd d:\Code\pycardano_cip68_course_v0
python run_backend.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### 2. Kết nối ví

1. Mở browser tại `http://localhost:3000`
2. Click nút "Connect Wallet"
3. Chọn ví (Nami, Eternl, Lace, etc.)
4. Approve connection
5. Đảm bảo ví có ít nhất **10 ADA** (Preprod testnet)

### 3. Mint NFT

1. Nhập **Token Name** (tối đa 32 ký tự, không khoảng trắng)
2. Nhập **Description** (tối đa 256 ký tự)
3. Click "🚀 Mint NFT"
4. Chờ transaction được build (status: "building")
5. Ký transaction trong ví (status: "signing")
6. Chờ submit (status: "submitting")
7. Thành công! (status: "success")
8. NFT list sẽ tự động refresh sau 2 giây

**Chi phí**: ~2 ADA cho reference token + ~2 ADA cho user token + ~0.2 ADA phí giao dịch

### 4. Update Metadata

1. NFT list sẽ tự động hiển thị metadata khi load
2. Click nút "✏️ Update" trên NFT muốn cập nhật
3. Nhập description mới
4. Click "✅ Update Metadata"
5. Ký transaction trong ví
6. NFT list sẽ auto-refresh sau update thành công
7. Version number sẽ tăng lên

### 5. Burn NFT

1. Click nút "🔥 Burn" trên NFT muốn xóa
2. Đọc cảnh báo (hành động không thể hoàn tác)
3. Check box "Tôi hiểu và chấp nhận"
4. Click "Burn NFT"
5. Ký transaction trong ví
6. NFT sẽ biến mất khỏi danh sách
7. ADA được thu hồi về ví

---

## 🔧 Cấu hình

### Backend Configuration (`.env`)

```env
# Network: Preprod hoặc Mainnet
NETWORK=Preprod

# Blockfrost API
BLOCKFROST_URL=https://cardano-preprod.blockfrost.io/api
BLOCKFROST_API_KEY=preprodXXXXXXXXXXXXXXXXXXXX

# Optional: Custom port
PORT=8000
```

### Frontend Configuration

Không cần cấu hình đặc biệt. Backend URL được hardcode là `http://localhost:8000`.

Nếu muốn thay đổi, cập nhật trong các file:
- `frontend/src/components/MintForm.tsx`
- `frontend/src/components/UpdateModal.tsx`
- `frontend/src/components/BurnModal.tsx`
- `frontend/src/components/NFTList.tsx`
- `frontend/src/app/HomeContent.tsx`

---

## 🎨 Tính năng UX đã cải thiện

### 1. Auto-load Metadata
- Metadata tự động load khi NFT list được hiển thị
- Không cần click "Update" để xem thông tin
- Hiển thị loading indicator khi đang fetch

### 2. Platform Filtering
- Chỉ hiển thị NFT từ platform này (theo policy ID)
- Ẩn NFT CIP-68 từ các platform khác
- Policy ID cố định: `9a97fb710a29382d31d9d2a40faab64e5c8be912419a806425bfc7d4`

### 3. Transaction Status Tracking
- **Building**: Đang tạo transaction
- **Signing**: Chờ user ký trong ví
- **Submitting**: Đang gửi lên blockchain
- **Success**: Thành công, có link đến CardanoScan
- **Error**: Hiển thị lỗi chi tiết

### 4. Auto-refresh
- Sau mint: Tự động refresh sau 2 giây
- Sau update: Tự động refresh sau 2 giây
- Sau burn: Tự động refresh sau 2 giây
- Auto-refresh định kỳ: Mỗi 30 giây

### 5. Loading States
- Loading spinner khi fetch NFT list
- Loading indicator cho từng metadata đang load
- Disable buttons khi đang xử lý
- Hover tooltips cho disabled states

---

## 📝 Lưu ý quan trọng

### 1. Policy ID và Store Address

Đây là **non-parameterized contracts**, có nghĩa:
- Policy ID **cố định**: `9a97fb710a29382d31d9d2a40faab64e5c8be912419a806425bfc7d4`
- Store address **cố định**: Được tính từ store script hash
- Owner được lưu trong **datum**, không phải tham số script

### 2. CIP-68 Token Names

- **Reference Token**: `000643b0` + token_name_hex (Label 100)
- **User Token**: `000de140` + token_name_hex (Label 222)

Ví dụ: Token "MyNFT" (hex: 4d794e4654)
- Reference: `000643b04d794e4654`
- User: `000de1404d794e4654`

### 3. Minimum ADA Requirements

- Reference Token UTxO: ~2 ADA (chứa datum)
- User Token UTxO: ~2 ADA
- Transaction fee: ~0.2 ADA

**Tổng cần cho 1 lần mint**: ~4-5 ADA

### 4. Preprod Testnet

- Dự án sử dụng **Preprod testnet**
- Lấy test ADA tại: https://docs.cardano.org/cardano-testnet/tools/faucet/
- Không sử dụng mainnet ADA thật

### 5. Browser Wallet Support

Hỗ trợ các ví:
- ✅ Nami
- ✅ Eternl
- ✅ Lace
- ✅ Flint
- ✅ Các ví hỗ trợ CIP-30

---

## 🐛 Troubleshooting

### 1. Backend không kết nối được

```bash
# Kiểm tra backend đang chạy
curl http://localhost:8000/api/script-info

# Kiểm tra Blockfrost API key
# File: .env
BLOCKFROST_API_KEY=preprod...

# Restart backend
python run_backend.py
```

### 2. Frontend không hiển thị NFT

- Kiểm tra wallet có connect chưa
- Kiểm tra backend đang chạy
- Mở Developer Console (F12) xem lỗi
- Click nút "🔄 Refresh" để load lại

### 3. Transaction bị reject

- Kiểm tra số dư ADA đủ chưa (cần ít nhất 10 ADA)
- Kiểm tra wallet đúng network (Preprod)
- Kiểm tra có đủ 2 tokens khi burn không
- Kiểm tra owner có đúng không (chỉ owner mới update/burn được)

### 4. Metadata không load

- Đợi vài giây để blockchain process
- Click "🔄 Refresh"
- Kiểm tra console log
- Kiểm tra backend log

### 5. Wallet không connect

- Kiểm tra extension đã cài chưa
- Reload trang
- Thử ví khác
- Kiểm tra ví đang ở Preprod network

---

## 📚 Tài liệu tham khảo

- [CIP-68 Specification](https://cips.cardano.org/cip/CIP-68)
- [PyCardano Documentation](https://pycardano.readthedocs.io/)
- [Aiken Language](https://aiken-lang.org/)
- [Cardano Developer Portal](https://developers.cardano.org/)
- [Blockfrost API](https://blockfrost.io/)

---

## 🤝 Contributing

Nếu muốn đóng góp:
1. Fork repository
2. Tạo branch mới (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Tạo Pull Request

---

## 📄 License

Dự án này được phát hành dưới MIT License.

---

## 👥 Support

Nếu gặp vấn đề hoặc có câu hỏi:
- Tạo issue trên GitHub
- Liên hệ qua Discord/Telegram
- Email: [your-email@example.com]

---

**Built with ❤️ using PyCardano, Aiken & Next.js**
