# Bài 1: Tổng quan về CIP-68

## 📚 CIP-68 là gì?

**CIP-68** (Cardano Improvement Proposal 68) là tiêu chuẩn cho **Dynamic NFTs** trên Cardano - NFT có metadata có thể cập nhật mà không thay đổi định danh của token.

### Vấn đề với NFT truyền thống

Với tiêu chuẩn NFT cũ (CIP-25), metadata được gắn trực tiếp vào transaction khi mint:

```
Transaction:
├── Mint: 1 token
└── Metadata (label 721):
    └── {policy_id}.{asset_name}: { name, image, ... }
```

**Vấn đề**:
- Metadata bất biến sau khi mint
- Muốn thay đổi phải burn và mint lại token mới
- Token mới có định danh khác → mất lịch sử giao dịch

### Giải pháp CIP-68

CIP-68 tách metadata ra khỏi token bằng cách sử dụng **2 tokens**:

```
┌─────────────────────────────────────────────────────────┐
│                      CIP-68 NFT                         │
├───────────────────────┬─────────────────────────────────┤
│   Reference Token     │      User Token                 │
│   (label 100)         │      (label 222)                │
├───────────────────────┼─────────────────────────────────┤
│ • Prefix: 0x000643b0  │ • Prefix: 0x000de140           │
│ • Lưu metadata        │ • Token người dùng sở hữu      │
│ • Ở script address    │ • Có thể transfer              │
│ • Có thể update       │ • Không đổi khi update metadata│
└───────────────────────┴─────────────────────────────────┘
```

## 🔧 Asset Name Labels

CIP-68 sử dụng 4-byte prefix để phân biệt loại token:

| Label | Prefix (hex) | Mục đích |
|-------|--------------|----------|
| 100   | 000643b0     | Reference Token |
| 222   | 000de140     | User Token (NFT) |
| 333   | 0014df10     | User Token (FT) |
| 444   | 001bc280     | Rich Fungible Token |

### Cách tính prefix

```python
# Formula: (label * 65536 + 1) with checksum
def label_to_prefix(label):
    prefix = (label << 16) + 1
    # Add CRC-8 checksum
    return prefix.to_bytes(4, 'big')

# Examples:
# 100 → 0x000643b0
# 222 → 0x000de140
```

## 📝 Datum Structure

Reference Token lưu metadata trong datum:

```aiken
type CIP68Datum {
  metadata: Data,  // Key-value pairs
  version: Int,    // Metadata version
  extra: Data,     // Optional extra data
}
```

### Metadata Format

```json
{
  "name": "My Dynamic NFT",
  "image": "ipfs://...",
  "description": "This can be updated!",
  "custom_field": "any value"
}
```

## 🔄 Update Flow

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   UTxO #1    │──────▶│ Transaction  │──────▶│   UTxO #2    │
│              │       │              │       │              │
│ RefToken     │       │ • Spend #1   │       │ RefToken     │
│ Datum v1     │       │ • Create #2  │       │ Datum v2     │
│              │       │              │       │              │
│ Script Addr  │       │ Owner signs  │       │ Script Addr  │
└──────────────┘       └──────────────┘       └──────────────┘
```

1. Spend UTxO chứa Reference Token
2. Tạo UTxO mới với datum updated
3. Reference Token trở lại script address
4. User Token không bị ảnh hưởng

## ✅ Ưu điểm CIP-68

1. **Dynamic Metadata**: Update bất kỳ lúc nào
2. **On-chain Storage**: Metadata lưu trực tiếp on-chain
3. **Identity Preservation**: User Token không đổi
4. **Standard Compliant**: Được community chấp nhận
5. **Marketplace Compatible**: Hỗ trợ bởi các marketplace

## 🎯 Use Cases

- **Gaming NFTs**: Cập nhật stats, level, equipment
- **Real World Assets**: Cập nhật trạng thái sở hữu
- **Tickets**: Cập nhật status (used/unused)
- **Certificates**: Cập nhật thông tin
- **Profile NFTs**: Cập nhật bio, avatar

## 📖 Tài liệu tham khảo

- [CIP-68 Specification](https://cips.cardano.org/cip/CIP-68)
- [CIP-67 (Asset Name Label)](https://cips.cardano.org/cip/CIP-67)

---

*Tiếp theo: [Bài 2 - Smart Contract](./02-smart-contract.md)*
