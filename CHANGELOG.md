# Changelog

Tất cả các thay đổi quan trọng của dự án sẽ được ghi lại ở đây.

## [v0.2.0] - 2026-01-14

### ✨ Added - Tính năng mới

#### Frontend Improvements
- **Auto-load Metadata**: NFT list tự động load và hiển thị metadata khi component mount
  - Không cần click "Update" để xem thông tin token
  - Hiển thị loading indicator khi đang fetch metadata
  - Cache metadata để tối ưu performance
  
- **Platform Filtering**: Lọc NFT theo nền tảng
  - Chỉ hiển thị NFT từ platform này (policy ID cố định)
  - Ẩn NFT CIP-68 từ các nền tảng khác
  - Policy ID: `9a97fb710a29382d31d9d2a40faab64e5c8be912419a806425bfc7d4`
  
- **Auto-refresh**: Tự động cập nhật danh sách NFT
  - Refresh sau khi mint thành công (2 giây delay)
  - Refresh sau khi update metadata thành công (2 giây delay)
  - Refresh sau khi burn NFT thành công (2 giây delay)
  - Auto-refresh định kỳ mỗi 30 giây
  
- **Transaction Status Tracking**: Hiển thị rõ ràng trạng thái giao dịch
  - Building: Đang tạo transaction
  - Signing: Chờ user ký trong ví
  - Submitting: Đang gửi lên blockchain
  - Success: Thành công với link CardanoScan
  - Error: Hiển thị lỗi chi tiết
  
- **Loading States**: Loading indicators cho mọi thao tác
  - Loading spinner khi fetch NFT list
  - Loading indicator cho metadata đang load
  - Disable buttons khi đang xử lý
  - Hover tooltips cho disabled states

#### Documentation
- Thêm `DOCUMENTATION.md`: Tài liệu chi tiết đầy đủ
  - Kiến trúc hệ thống
  - API endpoints chi tiết
  - Transaction flow diagrams
  - Setup instructions
  - Troubleshooting guide
  
- Thêm `QUICKSTART.md`: Hướng dẫn nhanh
  - Cài đặt nhanh
  - Lệnh hữu ích
  - Xử lý lỗi thường gặp
  
- Thêm `CHANGELOG.md`: Ghi lại lịch sử thay đổi

### 🔧 Changed - Thay đổi

#### NFTList Component
- **File**: `frontend/src/components/NFTList.tsx`
- Thêm state `isLoadingMetadata` để track loading state
- Thêm constant `PLATFORM_POLICY_ID` để filter NFT
- Refactor `fetchAssets()`:
  - Filter NFT theo policy ID của platform
  - Gọi `loadAllMetadata()` sau khi fetch assets
- Thêm function `loadAllMetadata()`:
  - Fetch metadata song song cho tất cả NFT
  - Sử dụng Promise.all để tối ưu
- Cập nhật UI:
  - Hiển thị loading state khi fetch metadata
  - Hiển thị "Loading metadata..." khi chưa có data
  - Disable nút Update khi metadata chưa load xong
  - Thêm tooltip cho disabled buttons

#### MintForm Component
- **File**: `frontend/src/components/MintForm.tsx`
- Thêm prop `onMintSuccess?: () => void`
- Gọi callback `onMintSuccess()` sau khi mint thành công
- Delay 2 giây để blockchain process

#### UpdateModal Component
- **File**: `frontend/src/components/UpdateModal.tsx`
- Delay 2 giây trước khi gọi `onSuccess()` và `onClose()`
- Cho phép blockchain process transaction

#### BurnModal Component
- **File**: `frontend/src/components/BurnModal.tsx`
- Delay 2 giây trước khi gọi `onSuccess()` và `onClose()`
- Cho phép blockchain process transaction

#### HomeContent Component
- **File**: `frontend/src/app/HomeContent.tsx`
- Thêm state `refreshNFTList` để trigger re-render
- Thêm function `handleRefreshNFTList()`
- Truyền `onMintSuccess` callback cho MintForm
- Thêm `key={refreshNFTList}` cho NFTList để force re-mount

#### .gitignore
- **File**: `.gitignore`
- Cập nhật pattern cho `node_modules/`, `.vscode/`
- Thêm pattern cho `frontend/.next/`, `frontend/out/`
- Thêm pattern cho `frontend/next-env.d.ts`
- Loại bỏ `docs/` khỏi gitignore
- Thêm pattern `minted_*.json` để ignore generated files
- Fix trailing slash cho virtual environment paths

### 📝 Documentation Updates

#### README.md
- Thêm section "Tính năng mới (v0.2)"
- Cập nhật cấu trúc dự án với icons ✨ cho files được cải thiện
- Thêm links đến DOCUMENTATION.md và QUICKSTART.md
- Thêm section "Cải tiến Frontend (v0.2)" với chi tiết các tính năng
- Cập nhật hướng dẫn cài đặt (loại bỏ yêu cầu Aiken, seed phrase)
- Đơn giản hóa bước "Chạy Backend"

#### DOCUMENTATION.md (New)
- Tổng quan dự án và tính năng
- Kiến trúc hệ thống chi tiết (4 layers)
- Smart contract specification
- Backend API documentation
- Frontend component architecture
- Transaction flow diagrams
- Setup instructions đầy đủ
- Cách sử dụng từng tính năng
- Configuration options
- Troubleshooting guide
- References và links hữu ích

#### QUICKSTART.md (New)
- Yêu cầu hệ thống
- Cài đặt nhanh (backend + frontend)
- Tóm tắt tính năng mới
- Workflow đơn giản
- Lệnh hữu ích
- Xử lý lỗi thường gặp
- Cấu trúc project quan trọng

### 🐛 Bug Fixes

- Fix metadata không hiển thị khi load NFT list lần đầu
- Fix NFT từ platform khác bị hiển thị lộn xộn
- Fix NFT list không tự động cập nhật sau mint/update/burn
- Fix loading state không rõ ràng khi thực hiện thao tác

### 🎯 Improvements - Cải thiện

- Tăng trải nghiệm người dùng với auto-refresh
- Giảm số lần user phải refresh thủ công
- Hiển thị thông tin rõ ràng hơn
- Loading states tốt hơn
- Error messages chi tiết hơn
- Documentation đầy đủ và dễ hiểu

---

## [v0.1.0] - Initial Release

### Added - Tính năng ban đầu

- Smart Contract (Aiken):
  - Minting policy cho CIP-68 tokens
  - Spending validator cho reference token storage
  - Non-parameterized contracts (fixed policy ID)
  
- Backend (FastAPI + PyCardano):
  - API endpoints: mint, update, burn, submit
  - Unsigned transaction building
  - Wallet info và metadata queries
  - Address conversion (hex to bech32)
  
- Frontend (Next.js + React):
  - Browser wallet integration (CIP-30)
  - Mint form
  - NFT list display
  - Update modal
  - Burn modal
  - Transaction status display
  
- Off-chain code (PyCardano):
  - CIP-68 utilities
  - Datum creation and parsing
  - Asset name helpers
  - Script loading

### Documentation

- README.md với hướng dẫn cơ bản
- docs/ folder với CIP-68 overview
- Backend README
- Code comments trong source files

---

## Future Plans - Kế hoạch tương lai

### v0.3.0 (Planned)
- [ ] Metadata editor với nhiều fields
- [ ] Image upload và IPFS integration
- [ ] Batch operations (mint/update multiple NFTs)
- [ ] Transaction history
- [ ] Export NFT data
- [ ] Dark mode

### v0.4.0 (Planned)
- [ ] NFT marketplace integration
- [ ] Transfer NFT functionality
- [ ] Royalty configuration
- [ ] Collection management
- [ ] Analytics dashboard

---

**Ghi chú**: 
- Dự án sử dụng [Semantic Versioning](https://semver.org/)
- Format dựa trên [Keep a Changelog](https://keepachangelog.com/)
