# Phần 1 — Lý thuyết CIP-68 qua slide (kịch bản giảng)

> Mục tiêu phần 1: Học viên hiểu *vì sao* cần CIP-68 và *CIP-68 hoạt động thế nào* (2 token + datum on-chain), nắm labels/prefix CIP-67, và hiểu luồng update metadata.

## 0) Chuẩn bị trước khi lên lớp (giảng viên)
- Mở sẵn các tài liệu trong repo:
  - `docs/01-cip68-overview.md`
  - `README.md` (mục “CIP-68 là gì?”)
- Chuẩn bị 1 ảnh/đồ thị minh họa “UTxO v1 → tx update → UTxO v2”.
- Chuẩn bị 1 câu chuyện use-case (gaming level, ticket used/unused…)

## 1) Mở bài (2–3 phút)
**Bạn nói (lời thoại gợi ý)**
- “Hôm nay mình học CIP-68: tiêu chuẩn Dynamic NFT trên Cardano.”
- “Điểm khác biệt: metadata *có thể update on-chain* mà *không đổi định danh user token*.”
- “Đến cuối buổi: mọi người mint/update/burn được NFT trên Preprod và chạy demo UI.”

**Bạn hỏi lớp (30 giây)**
- “Bạn từng gặp NFT mà muốn sửa metadata nhưng không thể chưa?”

## 2) Slide outline (đề xuất 10–12 slide)

### Slide 1 — Vấn đề NFT truyền thống (CIP-25/CIP-721 metadata)
**Mục tiêu**: làm rõ “metadata bất biến”.

**Bạn nói**
- “CIP-25 thường nhét metadata vào transaction lúc mint (label 721).”
- “Mint xong là metadata coi như ‘đóng băng’.”

**Tình huống minh họa**
- Gaming NFT: level thay đổi → nếu metadata bất biến, muốn update phải burn/mint lại.

**Câu hỏi tương tác**
- “Burn/mint lại thì sẽ có vấn đề gì?”
  - Gợi ý đáp án: mất lịch sử, token ID đổi, marketplace tracking rối.

---

### Slide 2 — Ý tưởng CIP-68: tách metadata khỏi user token
**Mục tiêu**: đưa ra “2 token / 1 NFT”.

**Bạn nói**
- “CIP-68 dùng 2 token: Reference token và User token.”
- “User token là thứ người dùng giữ/transfer.”
- “Reference token giữ datum metadata và nằm ở script address.”

---

### Slide 3 — Bảng so sánh: Reference token vs User token
**Bạn nói (điểm cần nhấn mạnh)**
- Reference token (label 100):
  - prefix `000643b0`
  - luôn ở script address
  - metadata nằm trong datum
  - update bằng cách spend UTxO và tạo UTxO mới
- User token (label 222):
  - prefix `000de140`
  - nằm trong ví người dùng
  - transfer bình thường
  - không đổi khi update metadata

**Mini quiz**
- “Label 100 prefix là gì?” → `000643b0`
- “Label 222 prefix là gì?” → `000de140`

---

### Slide 4 — CIP-67 labels/prefix: vì sao cần 4-byte prefix?
**Bạn nói**
- “Marketplace/tooling cần nhận ra token nào là reference/user.”
- “Prefix là một phần của asset name, giúp phân loại token.”

**Bạn minh họa nhanh**
- Token name gốc: `MyNFT`
- Reference asset name: `000643b0` + `MyNFT`
- User asset name: `000de140` + `MyNFT`

---

### Slide 5 — Datum là gì? Vì sao datum là nơi metadata sống?
**Bạn nói**
- “Trên Cardano, UTxO có thể kèm datum.”
- “Datum là dữ liệu on-chain dùng cho smart contract validation.”
- “CIP-68 tận dụng datum để lưu metadata.”

**Gắn với repo**
- Repo này dùng datum đầy đủ: policy_id + asset_name + owner + metadata + version.

---

### Slide 6 — Luồng update metadata (UTxO v1 → v2)
**Bạn nói (nói chậm, rõ)**
- “Update metadata nghĩa là *spend* UTxO đang giữ reference token.”
- “Tx tạo ra UTxO mới quay về script address, vẫn giữ reference token đó, nhưng datum mới (version + 1).”
- “User token trong ví không đổi.”

**Câu hỏi tương tác**
- “Vậy update cần điều kiện gì để an toàn?”
  - gợi ý: owner phải ký, phải có continuing output.

---

### Slide 7 — Ownership model: ai được update/burn?
**Bạn nói**
- “Nếu ai cũng update được metadata thì vô nghĩa.”
- “Cần một cơ chế chứng minh chủ sở hữu.”

**Gắn với repo**
- Owner PKH được lưu trong datum.
- Tx update/burn yêu cầu chữ ký owner (`required_signers`).

---

### Slide 8 — Mint/Update/Burn: 3 thao tác chính
**Bạn nói**
- “Mint: tạo cặp token (ref + user), tạo UTxO ref ở script + user ở ví.”
- “Update: spend ref UTxO, tạo ref UTxO mới (datum mới).”
- “Burn: burn cả 2 token + giải phóng UTxO ref.”

---

### Slide 9 — Trade-offs (thực tế sản phẩm)
**Bạn nói**
- “On-chain metadata tốt cho verify nhưng tx nặng hơn.”
- “Metadata quá lớn có thể làm tx to, phí cao.”
- “Cần design metadata tối giản + cache/truy vấn hợp lý.”

---

### Slide 10 — Mapping sang dự án của chúng ta
**Bạn nói**
- “Smart contract (Aiken): luật chơi (minting policy + store validator).”
- “Backend (FastAPI + PyCardano): build unsigned tx.”
- “Frontend (Next.js): kết nối CIP-30 wallet, ký tx, gọi submit.”

**Chuyển phần**
- “Giờ mình đi vào contract Aiken để xem ‘luật chơi’ được viết ra sao.”

## 3) Knowledge check cuối phần 1 (3–5 phút)
Bạn hỏi nhanh 5 câu:
1) CIP-68 dùng mấy token cho 1 NFT? Hai token đó là gì?
2) Label 100/222 prefix lần lượt là gì?
3) Vì sao update metadata không làm user token đổi?
4) Update metadata về mặt kỹ thuật là làm gì với UTxO reference?
5) Cơ chế bảo vệ để chỉ owner update là gì?

## 4) Transition sang phần 2 (30 giây)
**Bạn nói**
- “Phần 2: đọc smart contract Aiken, compile ra `plutus.json`, và hiểu chính xác ‘deploy’ trên Cardano nghĩa là gì.”
