# Phần 3 — Off-chain: PyCardano tương tác smart contract (kịch bản giảng)

> Mục tiêu phần 3: Học viên hiểu cách build transaction theo UTxO model cho CIP-68, chạy thử các script mint/update/burn trên Preprod, và biết quan sát kết quả (UTxO ở ví + UTxO ở store script).

## 0) Chuẩn bị trước khi dạy
- Mở các file:
  - `offchain/cip68_utils.py`
  - `offchain/cip68_operations.py`
  - `demo_mint.py`, `demo_update.py`, `demo_burn.py`
- Chuẩn bị:
  - Blockfrost API key (Preprod)
  - ví có tADA (>= 10 tADA)

## 1) Nhắc lại tư duy off-chain (5 phút)
**Bạn nói**
- “Off-chain không phải contract; off-chain là ‘người lắp ráp’ transaction.”
- “Mọi thứ ta làm phải thỏa điều kiện on-chain.”
- “Cấu trúc tư duy chuẩn khi build tx:”
  1) Tìm inputs phù hợp (wallet UTxO + script UTxO)
  2) Tạo outputs đúng (ref về script + user về wallet)
  3) Gắn script + redeemer + required signers
  4) Tính fee, cân bằng, submit

## 2) Repo này encode CIP-68 thế nào? (10 phút)
**Bạn làm (on-screen)**
- Mở `offchain/cip68_utils.py` và chỉ:
  - `CIP68_REFERENCE_PREFIX = 000643b0`
  - `CIP68_USER_PREFIX = 000de140`
  - `CIP68Datum` gồm: `policy_id`, `asset_name`, `owner`, `metadata`, `version`

**Bạn nói**
- “Datum không chỉ có metadata; repo này lưu luôn owner/policy_id/asset_name để truy vết và kiểm tra quyền sở hữu.”

**Bạn demo logic tạo asset names**
- Hàm `create_cip68_asset_names(token_name)` tạo 2 `AssetName`.

## 3) Cấu hình môi trường Preprod (5–8 phút)
**Bạn nói**
- “Muốn chạy được off-chain: cần chain context qua Blockfrost.”

**Bạn làm**
- Tạo `.env` ở thư mục gốc (nếu chưa):
```env
NETWORK=Preprod
BLOCKFROST_URL=https://cardano-preprod.blockfrost.io/api
BLOCKFROST_API_KEY=preprod_xxx
```

**Cảnh báo**
- “Sai network hoặc sai key → query UTxO fail / submit fail.”

## 4) Demo 1 — Mint CIP-68 (20 phút)
> Mục tiêu demo: sau mint, ví có user token, và store script có reference token kèm datum.

**Bạn nói (trước khi chạy)**
- “Mint = mint 2 token + tạo 2 outputs.”
- “Ref token output về store address có datum version=1.”
- “User token output về ví.”

**Bạn làm (hands-on)**
- Chạy script mint (tùy cách bạn set script):
```bash
python demo_mint.py
```

**Bạn hướng dẫn quan sát kết quả**
- “Sau submit, đợi 20–30 giây để blockchain/index cập nhật.”
- “Kiểm tra ví: thấy asset có prefix `000de140` + token_name.”
- “Kiểm tra store script: có UTxO chứa prefix `000643b0` + token_name.”

**Nếu học viên hỏi: ‘vì sao cần min-ADA ở outputs?’**
- “Mỗi UTxO phải có tối thiểu ADA (min-UTxO) để tồn tại.”

## 5) Demo 2 — Update metadata (15 phút)
> Mục tiêu demo: datum version tăng, description thay đổi.

**Bạn nói (trước khi chạy)**
- “Update nghĩa là spend UTxO ref ở store, rồi tạo UTxO ref mới quay về store.”
- “User token không đổi.”

**Bạn làm**
```bash
python demo_update.py
```

**Bạn nhấn mạnh**
- “Nếu update ngay sau mint mà không thấy reference token: đợi thêm 20–30 giây.”

## 6) Demo 3 — Burn (15 phút)
> Mục tiêu demo: burn cả 2 token, UTxO ref biến mất.

**Bạn nói (trước khi chạy)**
- “Burn cần gom cả 2 phía:
  - User token nằm trong ví
  - Reference token nằm ở store script
  => tx burn có cả minting script (burn) + spending script (burn reference).”

**Bạn làm**
```bash
python demo_burn.py
```

**Bạn nói**
- “Burn xong: NFT biến mất, ADA (trừ fee) quay về ví.”

## 7) Troubleshooting nhanh (5–8 phút)
- Không tìm thấy reference token:
  - Chờ 20–30 giây, thử lại.
  - Token name sai (khác chữ hoa/thường) → ref asset name mismatch.
- Tx bị reject do thiếu collateral/min-ADA:
  - Nạp thêm tADA.
- Sai Blockfrost URL hoặc key:
  - kiểm tra `.env`.

## 8) Chốt phần 3
**Bạn nói**
- “Phần 3 giúp mọi người hiểu tx CIP-68 theo kiểu ‘raw’.”
- “Giờ ta chuyển sang phần 4: làm dApp đúng kiểu sản phẩm: backend build tx, frontend nhờ wallet ký (CIP-30) và submit.”
