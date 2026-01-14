# 🚀 Hướng dẫn Nhanh - CIP-68 Dynamic NFT Platform

## 📋 Yêu cầu

- Node.js 18+
- Python 3.9+
- Browser wallet (Nami/Eternl/Lace)
- Blockfrost API key (Preprod)
- Ít nhất 10 tADA (testnet ADA)

## ⚡ Khởi động nhanh

### 1. Cài đặt Backend

```bash
# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt

# Tạo file .env
echo NETWORK=Preprod > .env
echo BLOCKFROST_URL=https://cardano-preprod.blockfrost.io/api >> .env
echo BLOCKFROST_API_KEY=your_key_here >> .env

# Chạy backend
python run_backend.py
```

### 2. Cài đặt Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Sử dụng

1. Mở http://localhost:3000
2. Click "Connect Wallet"
3. Mint NFT đầu tiên của bạn!

## ✨ Tính năng mới

### 🎯 Auto-load Metadata
- Metadata tự động hiển thị ngay khi load NFT
- Không cần click Update để xem thông tin
- Hiển thị loading indicator

### 🔍 Filter theo Platform
- Chỉ hiển thị NFT từ platform này
- Ẩn NFT từ các nền tảng khác
- Policy ID: `9a97fb710a29382d31d9d2a40faab64e5c8be912419a806425bfc7d4`

### 🔄 Auto-refresh
- Tự động refresh sau mint/update/burn (2 giây)
- Auto-refresh định kỳ mỗi 30 giây
- Loading states rõ ràng

### 📊 Transaction Status
- **Building**: Đang tạo transaction
- **Signing**: Chờ ký trong ví
- **Submitting**: Đang gửi lên blockchain
- **Success**: Thành công với link CardanoScan
- **Error**: Lỗi chi tiết

## 🎨 Workflow

### Mint NFT
```
Nhập thông tin → Click Mint → Ký trong ví → Đợi 20s → NFT xuất hiện
```

### Update Metadata
```
Click Update → Nhập mô tả mới → Ký → Đợi 20s → Metadata cập nhật
```

### Burn NFT
```
Click Burn → Xác nhận → Ký → Đợi 20s → NFT biến mất, ADA thu hồi
```

## 🔧 Lệnh hữu ích

```bash
# Kiểm tra backend
curl http://localhost:8000/api/script-info

# Xem log backend
python run_backend.py

# Rebuild frontend
cd frontend && npm run build

# Kiểm tra git status
git status
```

## 🐛 Xử lý lỗi thường gặp

### Backend không chạy
```bash
# Kiểm tra port 8000
netstat -ano | findstr :8000

# Kill process nếu bị chiếm
taskkill /PID <PID> /F

# Restart backend
python run_backend.py
```

### NFT không hiển thị
- Đợi 30 giây blockchain process
- Click nút Refresh (🔄)
- Mở F12 Developer Console kiểm tra lỗi
- Kiểm tra backend log

### Transaction bị reject
- Kiểm tra balance (cần >5 ADA)
- Kiểm tra network (phải là Preprod)
- Kiểm tra ownership (chỉ owner mới update/burn được)

## 📁 Cấu trúc quan trọng

```
pycardano_cip68_course_v0/
├── backend/
│   └── main.py              # API endpoints
├── frontend/src/
│   ├── components/
│   │   ├── NFTList.tsx      # ✨ Đã cải thiện
│   │   ├── MintForm.tsx     # ✨ Có auto-refresh
│   │   ├── UpdateModal.tsx  # ✨ Có auto-refresh
│   │   └── BurnModal.tsx    # ✨ Có auto-refresh
│   └── app/
│       └── HomeContent.tsx  # Main logic
├── offchain/
│   └── cip68_utils.py       # Policy ID, utilities
├── smart_contract/
│   └── plutus.json          # Compiled contracts
└── .env                     # Cấu hình backend
```

## 🎯 Policy ID & Network

- **Network**: Cardano Preprod Testnet
- **Policy ID**: `9a97fb710a29382d31d9d2a40faab64e5c8be912419a806425bfc7d4`
- **Faucet**: https://docs.cardano.org/cardano-testnet/tools/faucet/

## 📚 Tài liệu chi tiết

Xem file [DOCUMENTATION.md](./DOCUMENTATION.md) để biết thêm:
- Kiến trúc hệ thống
- API endpoints chi tiết
- Transaction flow
- Troubleshooting nâng cao

## 🎓 Học thêm

- Đọc code comments trong source files
- Xem docs/ folder cho giải thích CIP-68
- Thử nghiệm với testnet
- Tham gia Discord/Telegram community

---

**Ready to build Dynamic NFTs! 🚀**
