"""
CIP-68 Dynamic Asset - Main Off-chain Operations
================================================
Cung cấp các hàm chính để mint, update metadata, và burn CIP-68 tokens.

Sử dụng PyCardano để xây dựng transactions.

SIMPLIFIED VERSION: Non-parameterized contracts
- Fixed Policy ID
- Fixed Store Address  
- Owner stored in datum (portable across devices)
"""

import os
import json
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

from pycardano import (
    BlockFrostChainContext,
    Network,
    Address,
    TransactionBuilder,
    TransactionOutput,
    TransactionInput,
    TransactionId,
    PlutusV3Script,
    PlutusData,
    Redeemer,
    RedeemerTag,
    Value,
    MultiAsset,
    Asset,
    AssetName,
    ScriptHash,
    UTxO,
    PaymentSigningKey,
    PaymentVerificationKey,
    StakeSigningKey,
    StakeVerificationKey,
    Transaction,
    HDWallet,
    plutus_script_hash,
    min_lovelace,
)

from .cip68_utils import (
    CIP68_REFERENCE_PREFIX,
    CIP68_USER_PREFIX,
    FIXED_POLICY_ID,
    FIXED_STORE_HASH,
    MintToken,
    BurnToken,
    UpdateMetadata,
    BurnReference,
    CIP68Datum,
    create_cip68_asset_names,
    create_cip68_metadata,
    create_cip68_datum,
    get_policy_id,
    get_script_address,
    get_fixed_policy_id,
    get_fixed_store_address,
    load_mint_script,
    load_store_script,
    extract_owner_from_datum,
)


# Load environment variables
load_dotenv()


def get_chain_context() -> BlockFrostChainContext:
    """
    Tạo BlockFrost chain context từ environment variables.
    
    Returns:
        BlockFrostChainContext
    """
    network_str = os.getenv("NETWORK", "Preprod")
    blockfrost_url = os.getenv("BLOCKFROST_URL")
    blockfrost_key = os.getenv("BLOCKFROST_API_KEY")
    
    network = Network.TESTNET if network_str.lower() == "preprod" else Network.MAINNET
    
    return BlockFrostChainContext(
        project_id=blockfrost_key,
        base_url=blockfrost_url,
        network=network
    )


def get_wallet_from_seed(seed_phrase: str) -> tuple:
    """
    Tạo wallet từ seed phrase.
    
    Args:
        seed_phrase: 24-word mnemonic
        
    Returns:
        Tuple (payment_skey, payment_vkey, stake_skey, stake_vkey, address)
    """
    hdwallet = HDWallet.from_mnemonic(seed_phrase)
    
    # Derive keys
    hdwallet_spend = hdwallet.derive_from_path("m/1852'/1815'/0'/0/0")
    hdwallet_stake = hdwallet.derive_from_path("m/1852'/1815'/0'/2/0")
    
    payment_skey = PaymentSigningKey(hdwallet_spend.xprivate_key[:32])
    payment_vkey = PaymentVerificationKey.from_signing_key(payment_skey)
    
    stake_skey = StakeSigningKey(hdwallet_stake.xprivate_key[:32])
    stake_vkey = StakeVerificationKey.from_signing_key(stake_skey)
    
    network_str = os.getenv("NETWORK", "Preprod")
    network = Network.TESTNET if network_str.lower() == "preprod" else Network.MAINNET
    
    address = Address(payment_vkey.hash(), stake_vkey.hash(), network=network)
    
    return payment_skey, payment_vkey, stake_skey, stake_vkey, address


def get_network() -> Network:
    """Get network from environment."""
    network_str = os.getenv("NETWORK", "Preprod")
    return Network.TESTNET if network_str.lower() == "preprod" else Network.MAINNET


# ============================================================================
# SIMPLIFIED HELPER FUNCTIONS (Non-parameterized contracts)
# ============================================================================

def get_scripts(blueprint_path: str = None) -> tuple:
    """
    Load mint and store scripts from blueprint.
    
    Args:
        blueprint_path: Path to plutus.json. If None, uses default path.
        
    Returns:
        Tuple (mint_script, store_script, policy_id, store_address)
    """
    if blueprint_path is None:
        blueprint_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "smart_contract",
            "plutus.json"
        )
    
    mint_script = load_mint_script(blueprint_path)
    store_script = load_store_script(blueprint_path)
    
    policy_id = get_fixed_policy_id()
    network = get_network()
    store_address = get_fixed_store_address(network)
    
    return mint_script, store_script, policy_id, store_address


def mint_cip68_token(
    context: BlockFrostChainContext,
    payment_skey: PaymentSigningKey,
    payment_vkey: PaymentVerificationKey,
    owner_address: Address,
    token_name: str,
    description: str,
    blueprint_path: str = None,
) -> dict:
    """
    Mint một CIP-68 Dynamic NFT.
    
    SIMPLIFIED VERSION: Uses non-parameterized contracts.
    policy_id, asset_name, và owner được lưu trong datum.
    
    Args:
        context: BlockFrost chain context
        payment_skey: Payment signing key
        payment_vkey: Payment verification key
        owner_address: Địa chỉ của owner
        token_name: Tên token (sẽ được thêm prefix)
        description: Mô tả ban đầu của NFT
        blueprint_path: Path to plutus.json (optional)
        
    Returns:
        Dict with tx_hash, policy_id, and asset info
    """
    network = get_network()
    
    # Load scripts
    mint_script, store_script, policy_id, store_address = get_scripts(blueprint_path)
    
    # Get owner's public key hash
    owner_pkh = bytes(payment_vkey.hash())
    
    # Tạo asset names theo CIP-68
    token_name_bytes = token_name.encode('utf-8')
    ref_asset_name, user_asset_name = create_cip68_asset_names(token_name_bytes)
    
    # Policy ID as bytes for datum
    policy_id_bytes = bytes(policy_id)
    
    # Tạo CIP68 Datum - lưu policy_id, asset_name, owner
    datum = create_cip68_datum(
        policy_id=policy_id_bytes,
        asset_name=token_name_bytes,
        owner_pkh=owner_pkh,
        metadata=description,
        version=1
    )
    
    # Tạo MultiAsset cho minting
    mint_asset = Asset()
    mint_asset[ref_asset_name] = 1   # Reference token
    mint_asset[user_asset_name] = 1  # User token
    
    mint_assets = MultiAsset()
    mint_assets[policy_id] = mint_asset
    
    # Tạo redeemer
    redeemer = Redeemer(MintToken(token_name=token_name_bytes))
    
    # Tính reference token output value
    ref_asset = Asset()
    ref_asset[ref_asset_name] = 1
    ref_multi = MultiAsset()
    ref_multi[policy_id] = ref_asset
    ref_value = Value(2_000_000, ref_multi)
    
    # Build transaction
    builder = TransactionBuilder(context)
    builder.add_input_address(owner_address)
    
    # Mint tokens
    builder.mint = mint_assets
    builder.add_minting_script(mint_script, redeemer=redeemer)
    
    # Output: Reference token đến store script với datum
    builder.add_output(
        TransactionOutput(
            store_address,
            ref_value,
            datum=datum,
        )
    )
    
    # Output: User token đến owner
    user_asset = Asset()
    user_asset[user_asset_name] = 1
    user_multi = MultiAsset()
    user_multi[policy_id] = user_asset
    user_value = Value(2_000_000, user_multi)
    builder.add_output(
        TransactionOutput(
            owner_address,
            user_value,
        )
    )
    
    # Required signers
    builder.required_signers = [payment_vkey.hash()]
    
    # Build and sign
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=owner_address
    )
    
    # Submit
    tx_hash = context.submit_tx(signed_tx)
    print(f"Transaction submitted: {tx_hash}")
    
    return {
        "tx_hash": str(tx_hash),
        "policy_id": FIXED_POLICY_ID,
        "token_name": token_name,
        "ref_asset_name": ref_asset_name.payload.hex(),
        "user_asset_name": user_asset_name.payload.hex(),
        "store_address": str(store_address),
    }


def update_metadata(
    context: BlockFrostChainContext,
    payment_skey: PaymentSigningKey,
    payment_vkey: PaymentVerificationKey,
    owner_address: Address,
    token_name: str,
    new_description: str,
    blueprint_path: str = None,
) -> dict:
    """
    Update metadata của một CIP-68 NFT.
    
    SIMPLIFIED VERSION: Uses non-parameterized contracts.
    Verifies owner from datum. Giữ nguyên policy_id, asset_name, owner.
    
    Args:
        context: BlockFrost chain context
        payment_skey: Payment signing key
        payment_vkey: Payment verification key  
        owner_address: Địa chỉ của owner
        token_name: Tên token
        new_description: Mô tả mới
        blueprint_path: Path to plutus.json (optional)
        
    Returns:
        Dict with tx_hash and updated info
    """
    network = get_network()
    
    # Load scripts
    mint_script, store_script, policy_id, store_address = get_scripts(blueprint_path)
    
    # Get owner's public key hash for verification
    owner_pkh = bytes(payment_vkey.hash())
    
    # Policy ID as bytes
    policy_id_bytes = bytes(policy_id)
    
    # Tạo asset name cho reference token
    token_name_bytes = token_name.encode('utf-8')
    ref_asset_name = AssetName(CIP68_REFERENCE_PREFIX + token_name_bytes)
    
    # Tìm UTxO chứa reference token
    utxos = context.utxos(store_address)
    ref_utxo = None
    for utxo in utxos:
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid == policy_id and ref_asset_name in assets:
                    ref_utxo = utxo
                    break
    
    if not ref_utxo:
        raise ValueError("Không tìm thấy reference token UTxO!")
    
    # Parse current datum and verify owner
    current_datum = ref_utxo.output.datum
    if isinstance(current_datum, CIP68Datum):
        current_owner = extract_owner_from_datum(current_datum)
        if current_owner != owner_pkh:
            raise ValueError("Bạn không phải owner của NFT này!")
        new_version = current_datum.version + 1
    else:
        # Try to parse from raw data
        new_version = 2
    
    # Tạo datum mới - giữ nguyên policy_id, asset_name, owner
    new_datum = create_cip68_datum(
        policy_id=policy_id_bytes,
        asset_name=token_name_bytes,
        owner_pkh=owner_pkh,
        metadata=new_description,
        version=new_version
    )
    
    # Tạo redeemer cho spending
    redeemer = Redeemer(UpdateMetadata())
    
    # Build transaction
    builder = TransactionBuilder(context)
    builder.add_input_address(owner_address)
    
    # Spend reference token UTxO
    builder.add_script_input(
        ref_utxo,
        store_script,
        redeemer=redeemer
    )
    
    # Output: Reference token trở lại store script với datum mới
    ref_asset = Asset()
    ref_asset[ref_asset_name] = 1
    ref_multi = MultiAsset()
    ref_multi[policy_id] = ref_asset
    ref_value = Value(
        ref_utxo.output.amount.coin,
        ref_multi
    )
    builder.add_output(
        TransactionOutput(
            store_address,
            ref_value,
            datum=new_datum,
        )
    )
    
    # Required signers
    builder.required_signers = [payment_vkey.hash()]
    
    # Build and sign
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=owner_address
    )
    
    # Submit
    tx_hash = context.submit_tx(signed_tx)
    print(f"Update transaction submitted: {tx_hash}")
    
    return {
        "tx_hash": str(tx_hash),
        "policy_id": FIXED_POLICY_ID,
        "token_name": token_name,
        "new_version": new_version,
    }


def burn_cip68_token(
    context: BlockFrostChainContext,
    payment_skey: PaymentSigningKey,
    payment_vkey: PaymentVerificationKey,
    owner_address: Address,
    token_name: str,
    blueprint_path: str = None,
) -> dict:
    """
    Burn một CIP-68 NFT (cả reference token và user token).
    
    SIMPLIFIED VERSION: Uses non-parameterized contracts.
    Verifies owner from datum.
    
    Args:
        context: BlockFrost chain context
        payment_skey: Payment signing key
        payment_vkey: Payment verification key
        owner_address: Địa chỉ của owner
        token_name: Tên token
        blueprint_path: Path to plutus.json (optional)
        
    Returns:
        Dict with tx_hash and burn info
    """
    network = get_network()
    
    # Load scripts
    mint_script, store_script, policy_id, store_address = get_scripts(blueprint_path)
    
    # Get owner's public key hash
    owner_pkh = bytes(payment_vkey.hash())
    
    # Tạo asset names
    token_name_bytes = token_name.encode('utf-8')
    ref_asset_name, user_asset_name = create_cip68_asset_names(token_name_bytes)
    
    # Tìm UTxO chứa reference token
    store_utxos = context.utxos(store_address)
    ref_utxo = None
    for utxo in store_utxos:
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid == policy_id and ref_asset_name in assets:
                    ref_utxo = utxo
                    break
    
    if not ref_utxo:
        raise ValueError("Không tìm thấy reference token UTxO!")
    
    # Verify owner from datum
    current_datum = ref_utxo.output.datum
    if isinstance(current_datum, CIP68Datum):
        current_owner = extract_owner_from_datum(current_datum)
        if current_owner != owner_pkh:
            raise ValueError("Bạn không phải owner của NFT này!")
    
    # Tìm UTxO chứa user token trong ví owner
    owner_utxos = context.utxos(owner_address)
    user_utxo = None
    for utxo in owner_utxos:
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid == policy_id and user_asset_name in assets:
                    user_utxo = utxo
                    break
    
    if not user_utxo:
        raise ValueError("Không tìm thấy user token UTxO!")
    
    # Tạo MultiAsset cho burning (số âm)
    burn_asset = Asset()
    burn_asset[ref_asset_name] = -1   # Burn reference token
    burn_asset[user_asset_name] = -1  # Burn user token
    
    burn_assets = MultiAsset()
    burn_assets[policy_id] = burn_asset
    
    # Tạo redeemers
    mint_redeemer = Redeemer(BurnToken(token_name=token_name_bytes))
    spend_redeemer = Redeemer(BurnReference())
    
    # Build transaction
    builder = TransactionBuilder(context)
    builder.add_input_address(owner_address)
    
    # Spend reference token UTxO
    builder.add_script_input(
        ref_utxo,
        store_script,
        redeemer=spend_redeemer
    )
    
    # Add user token input
    builder.add_input(user_utxo)
    
    # Burn tokens
    builder.mint = burn_assets
    builder.add_minting_script(mint_script, redeemer=mint_redeemer)
    
    # Required signers
    builder.required_signers = [payment_vkey.hash()]
    
    # Build and sign
    signed_tx = builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=owner_address
    )
    
    # Submit
    tx_hash = context.submit_tx(signed_tx)
    print(f"Burn transaction submitted: {tx_hash}")
    
    return {
        "tx_hash": str(tx_hash),
        "policy_id": FIXED_POLICY_ID,
        "token_name": token_name,
        "burned": True,
    }


def get_cip68_metadata(
    context: BlockFrostChainContext,
    token_name: str,
    blueprint_path: str = None,
) -> Optional[Dict[str, Any]]:
    """
    Lấy metadata hiện tại của một CIP-68 NFT.
    
    SIMPLIFIED VERSION: Uses fixed policy ID and store address.
    
    Args:
        context: BlockFrost chain context
        token_name: Tên token
        blueprint_path: Path to plutus.json (optional)
        
    Returns:
        Dict with metadata, version, owner, policy_id, asset_name or None nếu không tìm thấy
    """
    network = get_network()
    
    # Get fixed addresses
    policy_id = get_fixed_policy_id()
    store_address = get_fixed_store_address(network)
    
    # Tạo asset name cho reference token
    token_name_bytes = token_name.encode('utf-8')
    ref_asset_name = AssetName(CIP68_REFERENCE_PREFIX + token_name_bytes)
    
    # Tìm UTxO chứa reference token
    utxos = context.utxos(store_address)
    for utxo in utxos:
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid == policy_id and ref_asset_name in assets:
                    datum = utxo.output.datum
                    if isinstance(datum, CIP68Datum):
                        # Convert bytes keys to strings
                        metadata = {}
                        for k, v in datum.metadata.items():
                            key = k.decode('utf-8') if isinstance(k, bytes) else str(k)
                            value = v.decode('utf-8') if isinstance(v, bytes) else v
                            metadata[key] = value
                        return {
                            'metadata': metadata,
                            'version': datum.version,
                            'owner': datum.owner.hex(),
                            'policy_id': datum.policy_id.hex() if datum.policy_id else FIXED_POLICY_ID,
                            'asset_name': datum.asset_name.decode('utf-8') if datum.asset_name else token_name,
                        }
    
    return None


def list_all_tokens(
    context: BlockFrostChainContext,
    owner_address: Address = None,
) -> List[Dict[str, Any]]:
    """
    List all CIP-68 tokens, optionally filtered by owner.
    
    Args:
        context: BlockFrost chain context
        owner_address: Filter by owner address (optional)
        
    Returns:
        List of token info dicts
    """
    network = get_network()
    policy_id = get_fixed_policy_id()
    store_address = get_fixed_store_address(network)
    
    tokens = []
    utxos = context.utxos(store_address)
    
    for utxo in utxos:
        if utxo.output.amount.multi_asset:
            for pid, assets in utxo.output.amount.multi_asset.items():
                if pid == policy_id:
                    for asset_name in assets.keys():
                        # Check if it's a reference token
                        if asset_name.payload.startswith(CIP68_REFERENCE_PREFIX):
                            token_name = asset_name.payload[4:].decode('utf-8')
                            datum = utxo.output.datum
                            
                            token_info = {
                                'token_name': token_name,
                                'policy_id': FIXED_POLICY_ID,
                                'ref_asset_name': asset_name.payload.hex(),
                            }
                            
                            if isinstance(datum, CIP68Datum):
                                token_info['owner'] = datum.owner.hex()
                                token_info['version'] = datum.version
                                # Lấy thêm thông tin từ datum
                                if datum.policy_id:
                                    token_info['datum_policy_id'] = datum.policy_id.hex()
                                if datum.asset_name:
                                    token_info['datum_asset_name'] = datum.asset_name.decode('utf-8')
                                
                                # Filter by owner if specified
                                if owner_address:
                                    owner_pkh = bytes(owner_address.payment_part)
                                    if datum.owner != owner_pkh:
                                        continue
                            
                            tokens.append(token_info)
    
    return tokens


if __name__ == "__main__":
    # Test basic functionality
    print("CIP-68 Off-chain module loaded successfully!")
    
    # Load environment
    seed_phrase = os.getenv("SEED_PHRASE")
    if seed_phrase:
        payment_skey, payment_vkey, stake_skey, stake_vkey, address = get_wallet_from_seed(seed_phrase)
        print(f"Wallet address: {address}")
