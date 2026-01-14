# CIP-68 Dynamic Asset - Hướng Dẫn Sử Dụng

## Tổng Quan

Dự án này demo việc tạo và quản lý CIP-68 Dynamic NFTs trên Cardano blockchain sử dụng:
- **Backend**: Python với PyCardano
- **Smart Contract**: Aiken (PlutusV3)
- **Frontend**: Next.js với MeshSDK

## Cấu Trúc Dự Án

```
pycardano_cip68_course_v0/
├── backend/              # FastAPI backend server
├── frontend/             # Next.js frontend
├── offchain/             # PyCardano off-chain code
│   ├── cip68_operations.py   # Main operations (mint, update, burn)
│   └── cip68_utils.py        # Utility functions
├── smart_contract/       # Aiken smart contracts
│   ├── validators/       # Aiken source code
│   └── plutus.json       # Compiled blueprint
├── demo_mint.py          # Demo script để mint NFT
├── demo_update.py        # Demo script để update metadata
├── demo_burn.py          # Demo script để burn NFT
├── .env                  # Environment configuration
└── requirements.txt      # Python dependencies
```

## Yêu Cầu Hệ Thống

### Backend (Python)
- Python 3.10+
- pip packages: pycardano, python-dotenv, fastapi, uvicorn

### Frontend (Node.js)
- Node.js 18+
- npm

### Smart Contract
- Aiken CLI (v1.1.x)

## Cấu Hình

### File `.env`

```env
# Network
NETWORK=Preprod

# Blockfrost API
BLOCKFROST_URL=https://cardano-preprod.blockfrost.io/api
BLOCKFROST_API_KEY=your_api_key_here

# Wallet (24-word mnemonic)
SEED_PHRASE=your twenty four word seed phrase goes here ...
```

## Chạy Ứng Dụng

### 1. Backend API

```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy backend server
python run_backend.py
```

Backend sẽ chạy tại `http://localhost:8000`

### 2. Frontend

```bash
cd frontend

# Cài đặt dependencies (lần đầu)
npm install

# Chạy development server
npm run dev
```

Frontend sẽ chạy tại `http://localhost:3000`

### 3. Sử dụng Frontend

1. Mở browser và truy cập `http://localhost:3000`
2. Kết nối ví Cardano (Nami, Eternl, Lace, v.v.)
3. Chọn tab để thực hiện các thao tác:
   - **Mint NFT**: Tạo CIP-68 Dynamic NFT mới
   - **Update Metadata**: Cập nhật metadata của NFT đã mint
   - **Burn NFT**: Đốt NFT

## Demo Scripts (Python)

### Mint NFT

```bash
python demo_mint.py
```

Script này sẽ:
1. Load wallet từ SEED_PHRASE
2. Tạo parameterized scripts
3. Mint một CIP-68 NFT với tên unique
4. Lưu thông tin vào `last_mint.json`

### Update Metadata

```bash
python demo_update.py
```

Script này sẽ:
1. Đọc thông tin từ `last_mint.json`
2. Tìm reference token trên chain
3. Update metadata với description mới

### Burn NFT

```bash
python demo_burn.py
```

Script này sẽ:
1. Đọc thông tin từ `last_mint.json`
2. Burn cả reference token và user token
3. Xóa `last_mint.json`

## CIP-68 Explained

### Cấu trúc CIP-68

CIP-68 sử dụng 2 tokens:

1. **Reference Token (Label 100)**: 
   - Prefix: `0x000643b0`
   - Chứa metadata trong datum
   - Luôn ở script address
   
2. **User Token (Label 222)**:
   - Prefix: `0x000de140`
   - Token người dùng sở hữu
   - Có thể chuyển nhượng

### Lợi ích của CIP-68

- **Dynamic Metadata**: Có thể update metadata mà không cần burn/remint
- **On-chain Metadata**: Metadata được lưu trữ on-chain trong datum
- **Standard Format**: Theo chuẩn CIP-68, tương thích với marketplaces

## Kết Quả Test (Preprod)

Tất cả các operations đã được test thành công trên Preprod testnet:

| Operation | Transaction Hash | Cardanoscan |
|-----------|------------------|-------------|
| **MINT** | `6fccd4266a7596bdde8877817e7b4bfd970fe09704bc0ee4d4b74b3fa2d30aae` | [View](https://preprod.cardanoscan.io/transaction/6fccd4266a7596bdde8877817e7b4bfd970fe09704bc0ee4d4b74b3fa2d30aae) |
| **UPDATE** | `6538fdc7279f8d04553329543f323b97f593a0c541f385f43e89963acb98c34f` | [View](https://preprod.cardanoscan.io/transaction/6538fdc7279f8d04553329543f323b97f593a0c541f385f43e89963acb98c34f) |
| **BURN** | `1a162ecb4168bec3ac2e358f12f0f0b152f8c1c34957d9ac02fa7995784164e6` | [View](https://preprod.cardanoscan.io/transaction/1a162ecb4168bec3ac2e358f12f0f0b152f8c1c34957d9ac02fa7995784164e6) |

## Troubleshooting

### Frontend: Module not found libsodium

Lỗi này đã được fix bằng cách:
1. Sử dụng dynamic imports với `ssr: false`
2. Config webpack aliases trong `next.config.js`
3. Thêm transpilePackages cho MeshSDK

### Backend: PPViewHashesDontMatch

Lỗi này liên quan đến PlutusV3 và PyCardano. Giải pháp:
1. **Upgrade PyCardano lên version 0.19.0+**:
   ```bash
   pip install --upgrade pycardano
   ```
2. Kiểm tra version: `pip show pycardano`

### Không tìm thấy reference token UTxO

Lỗi này xảy ra khi:
1. Transaction mint chưa được confirm - Chờ 30-60 giây rồi thử lại
2. Store script không đúng - Đảm bảo dùng `create_store_script()` với `owner_pkh`

### Không có UTxO

Đảm bảo ví có đủ ADA (ít nhất 10 ADA) để thực hiện transactions.

## API Endpoints

Backend cung cấp các endpoints:

- `GET /api/script-info`: Thông tin về scripts (policy ID, store hash)
- `POST /api/mint`: Mint CIP-68 NFT
- `POST /api/update`: Update metadata
- `POST /api/burn`: Burn NFT
- `GET /api/nfts/{address}`: Lấy danh sách NFTs của address

## Tài Liệu Tham Khảo

- [CIP-68 Specification](https://cips.cardano.org/cip/CIP-68)
- [PyCardano Documentation](https://pycardano.readthedocs.io/)
- [Aiken Documentation](https://aiken-lang.org/)
- [MeshSDK Documentation](https://meshjs.dev/)
