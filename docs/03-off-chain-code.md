# Bài 3: Off-chain Code với PyCardano

## 📚 Giới thiệu PyCardano

**PyCardano** là thư viện Python để tương tác với Cardano blockchain:

- Tạo và ký transactions
- Tương tác với Plutus smart contracts
- Quản lý keys và addresses
- Kết nối với Blockfrost/Ogmios

## 🔧 Cài đặt

```bash
pip install pycardano
```

## 📝 Cấu trúc Off-chain Code

```
offchain/
├── __init__.py
├── cip68_utils.py       # Utility functions
└── cip68_operations.py  # Main operations
```

## 🔑 Wallet Management

### Từ Seed Phrase

```python
from pycardano import HDWallet, PaymentSigningKey, PaymentVerificationKey

def get_wallet_from_seed(seed_phrase: str):
    hdwallet = HDWallet.from_mnemonic(seed_phrase)
    
    # Derive keys theo CIP-1852
    hdwallet_spend = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")
    hdwallet_stake = hdwallet.derive_from_path("m/1852'/1815'/0'/2/0")
    
    payment_skey = PaymentSigningKey(hdwallet_spend.xprivate_key[:32])
    payment_vkey = PaymentVerificationKey.from_signing_key(payment_skey)
    
    return payment_skey, payment_vkey
```

### Tạo Address

```python
from pycardano import Address, Network

address = Address(
    payment_vkey.hash(),
    stake_vkey.hash(),  # Optional
    network=Network.TESTNET
)
```

## 🌐 Chain Context

### Với Blockfrost

```python
from pycardano import BlockFrostChainContext

context = BlockFrostChainContext(
    project_id="your_api_key",
    base_url="https://cardano-preprod.blockfrost.io/api/v0",
    network=Network.TESTNET
)
```

### Lấy UTxOs

```python
utxos = context.utxos(address)
for utxo in utxos:
    print(f"TxId: {utxo.input.transaction_id}")
    print(f"Index: {utxo.input.index}")
    print(f"Amount: {utxo.output.amount}")
```

## 📦 CIP-68 Types

### PlutusData Definitions

```python
from dataclasses import dataclass
from pycardano import PlutusData

# CIP-68 Prefixes
CIP68_REFERENCE_PREFIX = bytes.fromhex("000643b0")
CIP68_USER_PREFIX = bytes.fromhex("000de140")

@dataclass
class MintToken(PlutusData):
    CONSTR_ID = 0
    token_name: bytes

@dataclass
class BurnToken(PlutusData):
    CONSTR_ID = 1
    token_name: bytes

@dataclass
class UpdateMetadata(PlutusData):
    CONSTR_ID = 0

@dataclass
class BurnReference(PlutusData):
    CONSTR_ID = 1

@dataclass
class CIP68Datum(PlutusData):
    CONSTR_ID = 0
    metadata: dict  # Key-value pairs
    version: int
```

## 🎨 Mint Operation

```python
from pycardano import (
    TransactionBuilder,
    TransactionOutput,
    Value,
    MultiAsset,
    Asset,
    AssetName,
    Redeemer,
    PlutusV3Script,
    plutus_script_hash,
)

def mint_cip68_token(
    context,
    payment_skey,
    payment_vkey,
    owner_address,
    token_name: str,
    description: str,
    mint_script: PlutusV3Script,
    store_script: PlutusV3Script,
):
    # 1. Lấy UTxOs
    utxos = context.utxos(owner_address)
    seed_utxo = utxos[0]  # UTxO cho one-shot
    
    # 2. Tạo asset names
    token_name_bytes = token_name.encode('utf-8')
    ref_asset_name = AssetName(CIP68_REFERENCE_PREFIX + token_name_bytes)
    user_asset_name = AssetName(CIP68_USER_PREFIX + token_name_bytes)
    
    # 3. Lấy policy ID và store address
    policy_id = plutus_script_hash(mint_script)
    store_address = Address(plutus_script_hash(store_script), network=Network.TESTNET)
    
    # 4. Tạo datum
    datum = CIP68Datum(
        metadata={b"description": description.encode()},
        version=1
    )
    
    # 5. Tạo MultiAsset cho minting
    mint_assets = MultiAsset()
    mint_assets[policy_id] = Asset()
    mint_assets[policy_id][ref_asset_name] = 1
    mint_assets[policy_id][user_asset_name] = 1
    
    # 6. Tạo redeemer
    redeemer = Redeemer(MintToken(token_name=token_name_bytes))
    
    # 7. Build transaction
    builder = TransactionBuilder(context)
    builder.add_input(seed_utxo)
    builder.add_input_address(owner_address)
    
    # Add minting
    builder.mint = mint_assets
    builder.add_minting_script(mint_script, redeemer=redeemer)
    
    # Reference token output (to script)
    ref_value = Value(2_000_000, MultiAsset({policy_id: {ref_asset_name: 1}}))
    builder.add_output(TransactionOutput(store_address, ref_value, datum=datum))
    
    # User token output (to owner)
    user_value = Value(2_000_000, MultiAsset({policy_id: {user_asset_name: 1}}))
    builder.add_output(TransactionOutput(owner_address, user_value))
    
    # Required signers
    builder.required_signers = [payment_vkey.hash()]
    
    # 8. Build and sign
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=owner_address
    )
    
    # 9. Submit
    tx_hash = context.submit_tx(signed_tx)
    return str(tx_hash)
```

## ✏️ Update Metadata

```python
def update_metadata(
    context,
    payment_skey,
    payment_vkey,
    owner_address,
    policy_id,
    token_name: str,
    new_description: str,
    store_script: PlutusV3Script,
):
    # 1. Tìm reference token UTxO
    ref_asset_name = AssetName(CIP68_REFERENCE_PREFIX + token_name.encode())
    store_address = Address(plutus_script_hash(store_script), network=Network.TESTNET)
    
    utxos = context.utxos(store_address)
    ref_utxo = None
    for utxo in utxos:
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid == policy_id and ref_asset_name in assets:
                    ref_utxo = utxo
                    break
    
    # 2. Tạo datum mới
    current_datum = ref_utxo.output.datum
    new_version = current_datum.version + 1 if isinstance(current_datum, CIP68Datum) else 2
    new_datum = CIP68Datum(
        metadata={b"description": new_description.encode()},
        version=new_version
    )
    
    # 3. Tạo redeemer
    redeemer = Redeemer(UpdateMetadata())
    
    # 4. Build transaction
    builder = TransactionBuilder(context)
    builder.add_input_address(owner_address)
    
    # Spend script UTxO
    builder.add_script_input(
        ref_utxo,
        store_script,
        datum=current_datum,
        redeemer=redeemer
    )
    
    # Output: Reference token back to script with new datum
    ref_value = Value(
        ref_utxo.output.amount.coin,
        MultiAsset({policy_id: {ref_asset_name: 1}})
    )
    builder.add_output(TransactionOutput(store_address, ref_value, datum=new_datum))
    
    # Required signers
    builder.required_signers = [payment_vkey.hash()]
    
    # 5. Build and sign
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=owner_address
    )
    
    return context.submit_tx(signed_tx)
```

## 🔥 Burn Token

```python
def burn_cip68_token(
    context,
    payment_skey,
    payment_vkey,
    owner_address,
    policy_id,
    token_name: str,
    mint_script: PlutusV3Script,
    store_script: PlutusV3Script,
):
    # Tìm cả 2 UTxOs chứa reference và user token
    # ...
    
    # Burn assets (số âm)
    burn_assets = MultiAsset()
    burn_assets[policy_id] = Asset()
    burn_assets[policy_id][ref_asset_name] = -1
    burn_assets[policy_id][user_asset_name] = -1
    
    # Cần 2 redeemers: mint và spend
    mint_redeemer = Redeemer(BurnToken(token_name=token_name.encode()))
    spend_redeemer = Redeemer(BurnReference())
    
    # Build transaction với cả minting script và spending script
    # ...
```

## 📊 Transaction Builder Flow

```
┌─────────────────────────────────────────────────────────┐
│                  TransactionBuilder                      │
├─────────────────────────────────────────────────────────┤
│  1. add_input_address(owner)    ← Inputs từ ví         │
│  2. add_script_input(...)       ← Input từ script      │
│  3. mint = MultiAsset(...)      ← Tokens để mint/burn  │
│  4. add_minting_script(...)     ← Minting policy       │
│  5. add_output(...)             ← Outputs              │
│  6. required_signers = [...]    ← Required signatures  │
├─────────────────────────────────────────────────────────┤
│  7. build_and_sign([skeys], change_address)            │
│     → Calculate fees                                    │
│     → Balance transaction                               │
│     → Add change output                                 │
│     → Sign with keys                                    │
├─────────────────────────────────────────────────────────┤
│  8. context.submit_tx(signed_tx)                        │
│     → Submit to blockchain                              │
└─────────────────────────────────────────────────────────┘
```

## ⚠️ Lưu ý quan trọng

1. **Collateral**: PyCardano tự động xử lý collateral cho Plutus scripts
2. **Min UTxO**: Mỗi output cần tối thiểu ~1-2 ADA
3. **Fees**: Được tính tự động dựa trên transaction size
4. **Script execution**: Execution units được tính tự động

---

*Tiếp theo: [Bài 4 - Kiến trúc dApp](./04-dapp-architecture.md)*
