use aiken/collection/list
use aiken/primitive/bytearray
use cardano/assets.{PolicyId}
use cardano/transaction.{OutputReference, Transaction, InlineDatum}

// ============================================================================
// CIP-68 DYNAMIC ASSET - SMART CONTRACT (SIMPLIFIED)
// ============================================================================
// Smart contract đơn giản cho CIP-68 Dynamic NFT
// Không có parameterized scripts - dễ sử dụng và portable
// 
// CIP-68 sử dụng 2 tokens:
// - Reference Token (100): Lưu trữ metadata trên-chain, luôn ở script address
// - User Token (222): Token mà người dùng sở hữu
// ============================================================================

// CIP-68 Asset Label Prefixes
// Reference Token: (100) - 0x000643b0
// User Token: (222) - 0x000de140

/// Redeemer cho minting policy
pub type MintRedeemer {
  /// Mint mới reference token và user token
  MintToken { token_name: ByteArray }
  /// Burn reference token và user token
  BurnToken { token_name: ByteArray }
}

/// Redeemer cho spending validator (dùng để update metadata)
pub type SpendRedeemer {
  /// Update metadata của reference token
  UpdateMetadata
  /// Burn reference token
  BurnReference
}

/// Datum chứa metadata của CIP-68 NFT
/// Bao gồm thông tin để xác định chính xác token
pub type CIP68Datum {
  /// Policy ID của token - để verify đúng token
  policy_id: ByteArray,
  /// Asset name (không có prefix) - để phân biệt các token
  asset_name: ByteArray,
  /// Owner public key hash - người có quyền update/burn
  owner: ByteArray,
  /// Metadata fields theo CIP-68 standard
  metadata: Data,
  /// Version của metadata
  version: Int,
}

// ============================================================================
// VALIDATORS
// ============================================================================

/// Minting Policy cho CIP-68 tokens
/// Chỉ check format và số lượng - ai cũng có thể mint
/// Ownership được quản lý bởi spending validator
validator cip68_mint {
  mint(redeemer: MintRedeemer, policy_id: PolicyId, tx: Transaction) {
    let Transaction { mint, .. } = tx
    
    when redeemer is {
      MintToken { token_name } -> {
        // Tạo asset names theo CIP-68 standard
        let ref_token_name = #"000643b0" |> bytearray.concat(token_name)
        let user_token_name = #"000de140" |> bytearray.concat(token_name)
        
        // Kiểm tra mint đúng số lượng tokens
        let ref_qty = assets.quantity_of(mint, policy_id, ref_token_name)
        let user_qty = assets.quantity_of(mint, policy_id, user_token_name)
        
        // Phải mint đúng 1 reference token và 1 user token
        ref_qty == 1 && user_qty == 1
      }
      
      BurnToken { token_name } -> {
        let ref_token_name = #"000643b0" |> bytearray.concat(token_name)
        let user_token_name = #"000de140" |> bytearray.concat(token_name)
        
        // Kiểm tra burn đúng số lượng
        let ref_qty = assets.quantity_of(mint, policy_id, ref_token_name)
        let user_qty = assets.quantity_of(mint, policy_id, user_token_name)
        
        // Phải burn cả reference token (-1) và user token (-1)
        ref_qty == -1 && user_qty == -1
      }
    }
  }

  else(_) {
    fail
  }
}

/// Spending Validator cho Reference Token
/// Cho phép update metadata hoặc burn reference token
/// Chỉ owner (từ datum) mới có quyền thực hiện
/// Verify policy_id và asset_name để đảm bảo đúng token
validator cip68_store {
  spend(
    datum: Option<CIP68Datum>,
    redeemer: SpendRedeemer,
    own_ref: OutputReference,
    tx: Transaction,
  ) {
    // Phải có datum
    expect Some(current_datum) = datum
    
    // Lấy thông tin từ datum
    let owner_pkh = current_datum.owner
    let datum_policy_id = current_datum.policy_id
    let datum_asset_name = current_datum.asset_name
    
    // Kiểm tra chữ ký của owner
    let must_be_signed = list.has(tx.extra_signatories, owner_pkh)
    
    when redeemer is {
      UpdateMetadata -> {
        // Tìm input của script
        expect Some(own_input) = list.find(tx.inputs, fn(input) {
          input.output_reference == own_ref
        })
        
        let script_address = own_input.output.address
        
        // Tạo expected reference token name
        let ref_token_name = #"000643b0" |> bytearray.concat(datum_asset_name)
        
        // Kiểm tra input có chứa reference token với đúng policy_id và asset_name
        let input_has_ref_token = assets.quantity_of(
          own_input.output.value,
          datum_policy_id,
          ref_token_name
        ) == 1
        
        // Kiểm tra có output trả về cùng script address với:
        // - Đúng reference token
        // - Datum mới phải giữ nguyên owner, policy_id, asset_name
        let has_valid_output = list.any(tx.outputs, fn(output) {
          when output.datum is {
            InlineDatum(data) -> {
              expect new_datum: CIP68Datum = data
              // Kiểm tra output có reference token
              let output_has_ref_token = assets.quantity_of(
                output.value,
                datum_policy_id,
                ref_token_name
              ) == 1
              
              // Phải cùng script address, giữ nguyên identity fields
              output.address == script_address && 
              output_has_ref_token &&
              new_datum.policy_id == datum_policy_id &&
              new_datum.asset_name == datum_asset_name &&
              new_datum.owner == owner_pkh
            }
            _ -> False
          }
        })
        
        must_be_signed && input_has_ref_token && has_valid_output
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
