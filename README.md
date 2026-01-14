# CIP-68 Dynamic Asset - Khóa học PyCardano

## 📚 Giới thiệu

Đây là dự án demo cho khóa học **PyCardano CIP-68 Dynamic Asset**. Dự án minh họa cách xây dựng một dApp Cardano hoàn chỉnh với:

- **Smart Contract** (Aiken): Minting policy và spending validator cho CIP-68
- **Off-chain Code** (PyCardano): Xử lý transactions
- **Backend** (FastAPI): API để tạo unsigned transactions
- **Frontend** (Next.js): Giao diện người dùng với browser wallet integration

## ✨ Tính năng mới (v0.2)

- ✅ **Auto-load Metadata**: Tự động hiển thị thông tin NFT khi load, không cần click Update
- ✅ **Platform Filtering**: Chỉ hiển thị NFT từ nền tảng này (theo Policy ID)
- ✅ **Auto-refresh**: Tự động cập nhật danh sách sau mint/update/burn
- ✅ **Transaction Status Tracking**: Hiển thị rõ ràng trạng thái giao dịch
- ✅ **Loading Indicators**: Loading states cho mọi thao tác
- ✅ **Improved UX**: Trải nghiệm người dùng mượt mà hơn

## 🎯 Mục tiêu khóa học

1. Hiểu rõ cơ chế hoạt động của **CIP-68** (Dynamic NFT Standard)
2. Nắm được luồng triển khai từ on-chain đến off-chain
3. Hiểu cách các thành phần frontend, backend và ví trình duyệt phối hợp với nhau

## 📁 Cấu trúc dự án

```
pycardano_cip68_course_v0/
├── smart_contract/          # Aiken smart contracts
│   ├── validators/
│   │   └── cip68.ak        # CIP-68 minting policy & spending validator
│   ├── aiken.toml          # Aiken project config
│   └── plutus.json         # Compiled blueprint
│
├── offchain/               # PyCardano off-chain code
│   ├── __init__.py
│   ├── cip68_utils.py      # Utility functions
│   └── cip68_operations.py # Main operations (mint, update, burn)
│
├── backend/                # FastAPI backend
│   ├── main.py             # API endpoints
│   └── README.md
│
├── frontend/               # Next.js frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx    # Main page
│   │   │   └── HomeContent.tsx  # ✨ Improved with auto-refresh
│   │   └── components/
│   │       ├── MintForm.tsx      # ✨ Auto-refresh on success
│   │       ├── NFTList.tsx       # ✨ Auto-load metadata + filtering
│   │       ├── UpdateModal.tsx   # ✨ Auto-refresh on success
│   │       ├── BurnModal.tsx     # ✨ Auto-refresh on success
│   │       └── ...
│   └── package.json
│
├── docs/                   # Documentation
│   ├── 01-cip68-overview.md
│   ├── 02-smart-contract.md
│   ├── 03-off-chain-code.md
│   └── 04-dapp-architecture.md
│
├── DOCUMENTATION.md        # 📖 Tài liệu chi tiết đầy đủ
├── QUICKSTART.md          # 🚀 Hướng dẫn nhanh
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables
├── .gitignore             # ✨ Improved
└── README.md              # This file
```

## 🚀 Hướng dẫn cài đặt

> 💡 **Quick Start**: Xem [QUICKSTART.md](./QUICKSTART.md) để bắt đầu nhanh!  
> 📖 **Full Documentation**: Xem [DOCUMENTATION.md](./DOCUMENTATION.md) cho tài liệu chi tiết!

### Yêu cầu

- Python 3.9+
- Node.js 18+
- Blockfrost API Key (Preprod)
- Browser Wallet (Nami/Eternl/Lace)
- Git

### 1. Clone repository

```bash
git clone <repository-url>
cd pycardano_cip68_course_v0
```

### 2. Cài đặt Python dependencies

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
```

### 3. Cài đặt Node.js dependencies

```bash
cd frontend
npm install
cd ..
```

### 4. Cấu hình environment

Tạo file `.env` ở thư mục gốc:

```env
NETWORK=Preprod
BLOCKFROST_API_KEY=preprodXXXXXXXXXXXXXXXX
BLOCKFROST_URL=https://cardano-preprod.blockfrost.io/api
```

### 5. Chạy Backend

```bash
python run_backend.py
# Server chạy tại http://localhost:8000
```

### 6. Chạy Frontend (terminal khác)

```bash
cd frontend
npm run dev
# App chạy tại http://localhost:3000
```

### 7. Sử dụng

1. Mở http://localhost:3000
2. Click "Connect Wallet"
3. Chọn ví (Nami/Eternl/Lace)
4. Mint NFT đầu tiên! 🎨

## 📖 CIP-68 là gì?

**CIP-68** là tiêu chuẩn Cardano cho **Dynamic NFTs** - NFT có metadata có thể cập nhật.

### Cơ chế hoạt động

CIP-68 sử dụng **2 tokens** cho mỗi NFT:

1. **Reference Token (label 100)**: 
   - Prefix: `0x000643b0`
   - Lưu trữ metadata on-chain trong datum
   - Luôn nằm ở script address
   - Có thể update metadata bằng cách spend và tạo UTxO mới

2. **User Token (label 222)**:
   - Prefix: `0x000de140`
   - Token mà người dùng sở hữu
   - Dùng để chứng minh quyền sở hữu NFT
   - Có thể transfer như token thông thường

### Ưu điểm của CIP-68

- ✅ Metadata on-chain có thể cập nhật
- ✅ User token không bị ảnh hưởng khi update metadata
- ✅ Tiêu chuẩn được cộng đồng chấp nhận rộng rãi
- ✅ Phù hợp cho gaming, ticketing, dynamic art

## 🎨 Cải tiến Frontend (v0.2)

### Auto-load Metadata
- Metadata tự động hiển thị ngay khi load NFT list
- Không cần click "Update" để xem thông tin
- Hiển thị loading indicator khi đang fetch
- Cache metadata để giảm API calls

### Platform Filtering
- Chỉ hiển thị NFT từ platform này
- Lọc theo Policy ID: `9a97fb710a29382d31d9d2a40faab64e5c8be912419a806425bfc7d4`
- Ẩn NFT CIP-68 từ các nền tảng khác
- Giúp trải nghiệm người dùng sạch sẽ hơn

### Auto-refresh
- **Sau mint**: Tự động refresh sau 2 giây
- **Sau update**: Tự động refresh sau 2 giây  
- **Sau burn**: Tự động refresh sau 2 giây
- **Định kỳ**: Auto-refresh mỗi 30 giây
- Đảm bảo data luôn up-to-date

### Transaction Status
- **Building**: Đang tạo transaction
- **Signing**: Chờ user ký trong ví
- **Submitting**: Đang gửi lên blockchain
- **Success**: Thành công với link CardanoScan
- **Error**: Hiển thị lỗi chi tiết


## 🔧 Smart Contract

### Minting Policy (`cip68_mint`)

```aiken
validator cip68_mint(utxo_ref: OutputReference) {
  mint(redeemer: MintRedeemer, policy_id: PolicyId, tx: Transaction) {
    when redeemer is {
      MintToken { token_name } -> {
        // Kiểm tra UTxO one-shot
        // Mint 1 reference token và 1 user token
      }
      BurnToken { token_name } -> {
        // Burn cả 2 tokens
      }
    }
  }
}
```

### Spending Validator (`cip68_store`)

```aiken
validator cip68_store(owner_pkh: ByteArray) {
  spend(datum: Option<CIP68Datum>, redeemer: SpendRedeemer, ...) {
    when redeemer is {
      UpdateMetadata -> {
        // Kiểm tra owner ký
        // Kiểm tra có output trở về script address
      }
      BurnReference -> {
        // Kiểm tra owner ký để cho phép burn
      }
    }
  }
}
```

## 🌐 API Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/` | Health check |
| GET | `/api/script-info` | Thông tin smart contracts |
| GET | `/api/wallet/{address}` | Thông tin ví |
| POST | `/api/mint` | Tạo transaction mint NFT |
| POST | `/api/update` | Tạo transaction update metadata |
| POST | `/api/burn` | Tạo transaction burn NFT |
| POST | `/api/submit` | Submit signed transaction |
| GET | `/api/metadata/{policy_id}/{token_name}` | Lấy metadata NFT |

## 📱 Frontend Flow

1. **Kết nối ví**: Người dùng kết nối Nami/Eternl/Lace
2. **Tạo transaction**: Frontend gửi request đến backend
3. **Backend tạo unsigned tx**: Backend build transaction với PyCardano
4. **Ký transaction**: Frontend gửi tx đến ví để người dùng ký
5. **Submit**: Transaction được submit lên blockchain

```
┌────────────┐     ┌────────────┐     ┌────────────┐
│  Frontend  │────▶│  Backend   │────▶│ Blockchain │
│  (Next.js) │     │ (FastAPI)  │     │ (Cardano)  │
└────────────┘     └────────────┘     └────────────┘
      │                  │                   
      │                  │                   
      ▼                  ▼                   
┌────────────┐     ┌────────────┐            
│   Wallet   │     │ PyCardano  │            
│  (Browser) │     │ (Off-chain)│            
└────────────┘     └────────────┘            
```

## 🧪 Test trên Preprod

1. Lấy test ADA từ [Cardano Faucet](https://docs.cardano.org/cardano-testnets/tools/faucet/)
2. Kết nối ví đã có test ADA
3. Thử mint một NFT
4. Thử update metadata
5. Thử burn NFT

## 📚 Tài liệu bổ sung

- [CIP-68 Specification](https://cips.cardano.org/cip/CIP-68)
- [PyCardano Documentation](https://pycardano.readthedocs.io/)
- [Aiken Language Guide](https://aiken-lang.org/)
- [Mesh SDK Documentation](https://meshjs.dev/)

## ⚠️ Lưu ý

- Đây là code demo cho mục đích học tập
- Smart contract được thiết kế tối giản để minh họa
- **KHÔNG** sử dụng cho production
- Luôn kiểm tra kỹ trên testnet trước

## 📝 License

MIT License - Sử dụng tự do cho mục đích học tập và nghiên cứu.

---

*Built with ❤️ for PyCardano Course*
