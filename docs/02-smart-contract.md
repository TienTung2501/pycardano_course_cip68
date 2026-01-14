# Bài 2: Smart Contract với Aiken

## 📚 Giới thiệu Aiken

**Aiken** là ngôn ngữ lập trình dành riêng cho smart contracts trên Cardano:

- Syntax đơn giản, dễ học
- Compile thành UPLC (Untyped Plutus Lambda Calculus)
- Type-safe với type inference
- Tooling tốt (formatter, LSP, testing)

## 🔧 Cấu trúc Project

```
smart_contract/
├── aiken.toml           # Config file
├── validators/
│   └── cip68.ak         # Smart contract code
├── lib/                 # Library code (optional)
└── plutus.json          # Compiled blueprint
```

### aiken.toml

```toml
name = "pycardano_course/cip68_dynamic_asset"
version = "0.0.1"
compiler = "v1.1.19"
plutus = "v3"
license = "MIT"

[[dependencies]]
name = "aiken-lang/stdlib"
version = "v2.2.0"
source = "github"
```

## 📝 Định nghĩa Types

### Redeemers

```aiken
/// Redeemer cho minting policy
pub type MintRedeemer {
  /// Mint mới reference token và user token
  MintToken { token_name: ByteArray }
  /// Burn reference token và user token
  BurnToken { token_name: ByteArray }
}

/// Redeemer cho spending validator
pub type SpendRedeemer {
  /// Update metadata của reference token
  UpdateMetadata
  /// Burn reference token
  BurnReference
}
```

### Datum

```aiken
/// Datum chứa metadata của CIP-68 NFT
pub type CIP68Datum {
  /// Metadata fields theo CIP-68 standard
  metadata: Data,
  /// Version của metadata
  version: Int,
}
```

## 🔐 Minting Policy

```aiken
validator cip68_mint(utxo_ref: OutputReference) {
  mint(redeemer: MintRedeemer, policy_id: PolicyId, tx: Transaction) {
    let Transaction { inputs, mint, .. } = tx
    
    when redeemer is {
      MintToken { token_name } -> {
        // 1. Kiểm tra one-shot: UTxO phải được consume
        let has_utxo = list.any(inputs, fn(input) { 
          input.output_reference == utxo_ref 
        })
        
        // 2. Tạo asset names với CIP-68 prefixes
        let ref_token_name = #"000643b0" |> bytearray.concat(token_name)
        let user_token_name = #"000de140" |> bytearray.concat(token_name)
        
        // 3. Kiểm tra mint đúng số lượng
        let ref_qty = assets.quantity_of(mint, policy_id, ref_token_name)
        let user_qty = assets.quantity_of(mint, policy_id, user_token_name)
        
        // 4. Validate
        has_utxo && ref_qty == 1 && user_qty == 1
      }
      
      BurnToken { token_name } -> {
        // Tương tự nhưng kiểm tra số âm (-1)
        let ref_token_name = #"000643b0" |> bytearray.concat(token_name)
        let user_token_name = #"000de140" |> bytearray.concat(token_name)
        
        let ref_qty = assets.quantity_of(mint, policy_id, ref_token_name)
        let user_qty = assets.quantity_of(mint, policy_id, user_token_name)
        
        ref_qty == -1 && user_qty == -1
      }
    }
  }

  else(_) {
    fail
  }
}
```

### Giải thích

1. **One-shot minting**: Sử dụng `utxo_ref` như parameter để đảm bảo policy chỉ có thể mint một lần với UTxO cụ thể
2. **Asset name prefixes**: Thêm prefix theo CIP-68 standard
3. **Quantity check**: Đảm bảo mint/burn đúng số lượng

## 📦 Spending Validator

```aiken
validator cip68_store(owner_pkh: ByteArray) {
  spend(
    datum: Option<CIP68Datum>,
    redeemer: SpendRedeemer,
    own_ref: OutputReference,
    tx: Transaction,
  ) {
    // Phải có datum
    expect Some(_current_datum) = datum
    
    // Kiểm tra chữ ký của owner
    let must_be_signed = list.has(tx.extra_signatories, owner_pkh)
    
    when redeemer is {
      UpdateMetadata -> {
        // Tìm input của script
        expect Some(own_input) = list.find(tx.inputs, fn(input) {
          input.output_reference == own_ref
        })
        
        let script_address = own_input.output.address
        
        // Kiểm tra có output trả về cùng script address
        let has_continuing_output = list.any(tx.outputs, fn(output) {
          output.address == script_address
        })
        
        must_be_signed && has_continuing_output
      }
      
      BurnReference -> {
        // Chỉ cần owner ký để cho phép burn
        must_be_signed
      }
    }
  }

  else(_) {
    fail
  }
}
```

### Giải thích

1. **Owner authorization**: Chỉ owner có thể update/burn
2. **Continuing output**: Với UpdateMetadata, phải có output trở về script
3. **Flexible datum**: Datum mới có thể khác datum cũ

## 🏗️ Build Contract

```bash
cd smart_contract
aiken build
```

Output: `plutus.json` chứa compiled code và schema.

## 📋 Blueprint (plutus.json)

```json
{
  "preamble": {
    "title": "pycardano_course/cip68_dynamic_asset",
    "plutusVersion": "v3"
  },
  "validators": [
    {
      "title": "cip68.cip68_mint.mint",
      "compiledCode": "59025e0101...",
      "hash": "18b1e6ec..."
    },
    {
      "title": "cip68.cip68_store.spend",
      "compiledCode": "5901a90101...",
      "hash": "e229d645..."
    }
  ]
}
```

## 🧪 Testing

```aiken
test mint_token_success() {
  // Test logic here
  True
}

test update_metadata_requires_signature() {
  // Test logic here
  True
}
```

Run tests:
```bash
aiken check
```

## ⚠️ Lưu ý thiết kế

Contract này được thiết kế **tối giản** để minh họa:

1. Không có role-based access control
2. Không validate metadata format
3. Không có thời gian khóa
4. Không check reference token trong output

Trong production, bạn cần thêm các kiểm tra này.

---

*Tiếp theo: [Bài 3 - Off-chain Code](./03-off-chain-code.md)*
