# Phần 2 — On-chain: Aiken smart contract + compile + “deploy” Preprod (kịch bản giảng)

> Mục tiêu phần 2: Học viên đọc được logic contract, hiểu minting policy vs spending validator, compile ra blueprint, hiểu đúng khái niệm “deploy” trên Cardano, và biết cách kiểm tra policy ID/store address.

## 0) Chuẩn bị trước khi dạy
- Mở các file:
  - `smart_contract/validators/cip68.ak`
  - `smart_contract/aiken.toml`
  - `smart_contract/plutus.json`
  - `offchain/cip68_utils.py` (FIXED_POLICY_ID, FIXED_STORE_HASH)
- Nhắc học viên: “repo đang dùng simplified non-parameterized scripts (policy/store cố định).”

## 1) Mở đầu phần 2: “Deploy trên Cardano” nói cho đúng (5 phút)
**Bạn nói (rất quan trọng)**
- “Cardano không deploy contract kiểu Ethereum.”
- “Script tồn tại như code; cái được đưa vào blockchain là *transaction* có tham chiếu/đính kèm script.”
- “Vậy trong khóa này, ‘deploy’ nghĩa là: compile → lấy script hash/policy id → dùng nó build giao dịch trên Preprod.”

**Bạn chốt**
- “Smart contract = điều kiện hợp lệ. Offchain sẽ tạo tx để thỏa điều kiện đó.”

## 2) Tour Aiken project (5 phút)
**Bạn làm (on-screen)**
- Mở `smart_contract/aiken.toml`, chỉ ra:
  - `compiler` và `plutus = "v3"`
- Mở `smart_contract/validators/cip68.ak`.

**Bạn nói**
- “Aiken compile ra UPLC/Plutus; blueprint output là `plutus.json`.”

## 3) Types & dữ liệu vào/ra (10 phút)
**Bạn nói**
- “Contract có 2 nhóm redeemer:”
  - Mint redeemer: `MintToken`, `BurnToken`
  - Spend redeemer: `UpdateMetadata`, `BurnReference`
- “Datum liên quan CIP-68 chứa metadata + version (và trong repo của chúng ta còn có owner/policy_id/asset_name để verify).”

**Câu hỏi tương tác**
- “Vì sao update cần version?”
  - gợi ý: tracking lịch sử, tránh replay/đồng bộ.

## 4) Minting policy: mint/burn theo cặp (20–25 phút)
> Bám logic trong `cip68.ak` và phần giải thích ở `docs/02-smart-contract.md`.

**Bạn nói (flow)**
- “Minting policy có 2 nhánh:
  - MintToken: phải mint đúng 1 reference + 1 user.
  - BurnToken: phải burn đúng cả 2 (quantity âm).”
- “Asset name: prefix + token_name gốc.”

**Bạn nhấn mạnh invariant**
- “Không được mint lệch (chỉ user token) vì lúc đó update metadata không có reference token để bám.”

**Mini check**
- “Nếu ai đó cố mint 2 user token cho 1 reference token, policy có chặn không?”

## 5) Spending validator (store): update/burn reference token (20–25 phút)
**Bạn nói (flow)**
- “Reference token nằm ở script address. Update nghĩa là spend UTxO đó.”
- “Validator kiểm tra:
  1) Owner phải ký
  2) Với UpdateMetadata: phải có continuing output quay về script address
  3) Với BurnReference: chỉ cần owner ký (và burn flow sẽ burn token phía policy).”

**Điểm dạy quan trọng**
- “Continuing output là kỹ thuật ‘giữ token ở script’ sau khi update.”

## 6) Compile contract (10 phút)
**Bạn nói**
- “Compile tạo `plutus.json` chứa compiledCode + hash.”

**Bạn làm (demo lệnh)**
```bash
cd smart_contract
# nếu đã cài aiken
aiken build
```

**Bạn kiểm tra output**
- Mở `smart_contract/plutus.json`.
- Chỉ ra `validators` gồm 2 entry (mint/store).

## 7) Kiểm tra policy id & store address (5–10 phút)
**Bạn nói**
- “Policy ID = hash của mint script.”
- “Store address = địa chỉ script từ store validator hash + network.”

**Gắn với repo (simplified)**
- “Trong repo này, policy/store được cố định để demo đơn giản.”
- Mở `offchain/cip68_utils.py` để chỉ:
  - `FIXED_POLICY_ID = 9a97fb...c7d4`
  - `FIXED_STORE_HASH = 2d7d22...2867`

**Câu hỏi tương tác**
- “Nếu đổi code contract rồi build lại, policy id có đổi không?”
  - đáp án: có, vì hash thay đổi.

## 8) “Deploy lên Preprod” trong bài này diễn ra ở đâu? (2 phút)
**Bạn nói**
- “Khi ta mint/update/burn, tx sẽ đính kèm script + redeemer + datum → chạy trên Preprod.”
- “Nên phần ‘deploy’ thực tế của ta là: chạy giao dịch đầu tiên thành công.”

## 9) Checklist cuối phần 2
Học viên cần làm được:
- Phân biệt minting policy vs spending validator.
- Giải thích được vì sao mint/burn phải theo cặp.
- Giải thích được ‘continuing output’ trong update.
- Biết compile ra `plutus.json`.

## 10) Transition sang phần 3
**Bạn nói**
- “Giờ ta chuyển sang off-chain với PyCardano để build các giao dịch mint/update/burn theo đúng luật vừa học.”
