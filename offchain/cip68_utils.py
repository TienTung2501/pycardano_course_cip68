"""
CIP-68 Dynamic Asset - Off-chain Utilities
==========================================
Cung cấp các utility functions để tương tác với CIP-68 smart contract.

CIP-68 Standard:
- Reference Token (100): Prefix 0x000643b0 - lưu trữ metadata on-chain
- User Token (222): Prefix 0x000de140 - token người dùng sở hữu

SIMPLIFIED VERSION - Không có parameterized scripts
- Policy ID cố định
- Store address cố định
- Owner được lưu trong datum
"""

import json
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any, List, Union, Tuple

from pycardano import (
    Address,
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
    Network,
    UTxO,
    TransactionBuilder,
    RawPlutusData,
    plutus_script_hash,
)

# CIP-68 Asset Label Prefixes (as bytes)
CIP68_REFERENCE_PREFIX = bytes.fromhex("000643b0")  # Label 100
CIP68_USER_PREFIX = bytes.fromhex("000de140")       # Label 222


@dataclass
class MintToken(PlutusData):
    """
    Redeemer for minting CIP-68 tokens.
    Constructor ID = 0
    """
    CONSTR_ID = 0
    token_name: bytes


@dataclass
class BurnToken(PlutusData):
    """
    Redeemer for burning CIP-68 tokens.
    Constructor ID = 1
    """
    CONSTR_ID = 1
    token_name: bytes


@dataclass
class UpdateMetadata(PlutusData):
    """
    Redeemer for updating metadata in spending validator.
    Constructor ID = 0
    """
    CONSTR_ID = 0


@dataclass
class BurnReference(PlutusData):
    """
    Redeemer for burning reference token in spending validator.
    Constructor ID = 1
    """
    CONSTR_ID = 1


@dataclass
class CIP68Datum(PlutusData):
    """
    Datum chứa metadata của CIP-68 NFT.
    Theo CIP-68 standard với đầy đủ thông tin để xác định token.
    
    Fields:
        policy_id: Policy ID của token (28 bytes)
        asset_name: Tên asset không có prefix
        owner: Public key hash của owner (28 bytes)
        metadata: Key-value pairs cho metadata
        version: Phiên bản metadata
    """
    CONSTR_ID = 0
    policy_id: bytes          # Policy ID (28 bytes)
    asset_name: bytes         # Asset name (không có prefix)
    owner: bytes              # Owner public key hash (28 bytes)
    metadata: Dict[bytes, Any]  # Key-value pairs cho metadata
    version: int


def load_scripts(blueprint_path: str) -> Dict[str, Any]:
    """
    Load compiled scripts từ plutus.json blueprint.
    
    Args:
        blueprint_path: Đường dẫn tới file plutus.json
        
    Returns:
        Dict chứa thông tin của các validators
    """
    with open(blueprint_path, 'r', encoding='utf-8') as f:
        blueprint = json.load(f)
    
    scripts = {}
    for validator in blueprint['validators']:
        title = validator['title']
        scripts[title] = {
            'compiled_code': validator['compiledCode'],
            'hash': validator['hash'],
        }
    
    return scripts


def load_mint_script(blueprint_path: str) -> PlutusV3Script:
    """
    Load minting policy script từ blueprint.
    Script không có parameters - policy ID cố định.
    
    Args:
        blueprint_path: Đường dẫn tới plutus.json
        
    Returns:
        PlutusV3Script
    """
    scripts = load_scripts(blueprint_path)
    mint_info = scripts['cip68.cip68_mint.mint']
    return PlutusV3Script(bytes.fromhex(mint_info['compiled_code']))


def load_store_script(blueprint_path: str) -> PlutusV3Script:
    """
    Load spending validator script từ blueprint.
    Script không có parameters - store address cố định.
    Owner được xác định từ datum.
    
    Args:
        blueprint_path: Đường dẫn tới plutus.json
        
    Returns:
        PlutusV3Script
    """
    scripts = load_scripts(blueprint_path)
    store_info = scripts['cip68.cip68_store.spend']
    return PlutusV3Script(bytes.fromhex(store_info['compiled_code']))
# ==============================================================================
# FIXED POLICY ID & STORE ADDRESS (non-parameterized contracts)
# ==============================================================================

# These are derived from the compiled Aiken contract (no parameters)
FIXED_POLICY_ID = "9a97fb710a29382d31d9d2a40faab64e5c8be912419a806425bfc7d4"
FIXED_STORE_HASH = "2d7d22ba4cdd91176d2bc58720b15f433c023a90dfc5ffe1306d2867"


def get_fixed_policy_id() -> ScriptHash:
    """
    Get the fixed policy ID (non-parameterized contract).
    
    Returns:
        ScriptHash representing the policy ID
    """
    return ScriptHash.from_primitive(FIXED_POLICY_ID)


def get_fixed_store_address(network: Network) -> Address:
    """
    Get the fixed store address (non-parameterized contract).
    
    Args:
        network: Network (MAINNET or TESTNET)
        
    Returns:
        Address of the store script
    """
    store_hash = ScriptHash.from_primitive(FIXED_STORE_HASH)
    return Address(store_hash, network=network)


def create_cip68_asset_names(token_name: str | bytes) -> Tuple[AssetName, AssetName]:
    """
    Tạo asset names cho CIP-68 reference và user tokens.
    
    Args:
        token_name: Tên gốc của token (str hoặc bytes)
        
    Returns:
        Tuple (reference_asset_name, user_asset_name)
    """
    # Convert to bytes if string
    if isinstance(token_name, str):
        token_name_bytes = token_name.encode('utf-8')
    else:
        token_name_bytes = token_name
    
    ref_name = AssetName(CIP68_REFERENCE_PREFIX + token_name_bytes)
    user_name = AssetName(CIP68_USER_PREFIX + token_name_bytes)
    return ref_name, user_name


def create_cip68_metadata(description: str, extra_fields: Optional[Dict[str, Any]] = None) -> Dict[bytes, Any]:
    """
    Tạo metadata dictionary cho CIP-68 datum.
    
    Args:
        description: Mô tả của NFT
        extra_fields: Các fields bổ sung (optional)
        
    Returns:
        Dict metadata theo CIP-68 format
    """
    metadata = {
        b"description": description.encode('utf-8')
    }
    
    if extra_fields:
        for key, value in extra_fields.items():
            if isinstance(value, str):
                metadata[key.encode('utf-8')] = value.encode('utf-8')
            else:
                metadata[key.encode('utf-8')] = value
    
    return metadata


def create_cip68_datum(
    policy_id: bytes,
    asset_name: bytes,
    owner_pkh: bytes,
    metadata: Union[str, Dict[str, Any]], 
    version: int = 1
) -> CIP68Datum:
    """
    Tạo CIP68Datum với đầy đủ thông tin để xác định token.
    
    Args:
        policy_id: Policy ID của token (28 bytes)
        asset_name: Tên asset không có prefix (bytes)
        owner_pkh: Public key hash của owner (28 bytes)
        metadata: Metadata - nếu là string thì dùng làm description, nếu là dict thì convert to bytes keys
        version: Phiên bản metadata (default: 1)
        
    Returns:
        CIP68Datum object
    """
    if isinstance(metadata, str):
        # If string, use as description
        metadata_dict = create_cip68_metadata(metadata)
    elif isinstance(metadata, dict):
        # Convert dict with str keys to bytes keys
        metadata_dict = {}
        for key, value in metadata.items():
            key_bytes = key.encode('utf-8') if isinstance(key, str) else key
            value_bytes = value.encode('utf-8') if isinstance(value, str) else value
            metadata_dict[key_bytes] = value_bytes
    else:
        metadata_dict = metadata
    
    return CIP68Datum(
        policy_id=policy_id,
        asset_name=asset_name,
        owner=owner_pkh,
        metadata=metadata_dict,
        version=version
    )


def get_policy_id(mint_script: PlutusV3Script) -> ScriptHash:
    """
    Lấy policy ID từ minting script.
    
    Args:
        mint_script: PlutusV3Script minting policy
        
    Returns:
        ScriptHash (policy ID)
    """
    return plutus_script_hash(mint_script)


def extract_owner_from_datum(datum: CIP68Datum) -> bytes:
    """
    Extract owner public key hash từ CIP68Datum.
    
    Args:
        datum: CIP68Datum object
        
    Returns:
        bytes: Owner's public key hash (28 bytes)
    """
    return datum.owner


def get_script_address(script: PlutusV3Script, network: Network) -> Address:
    """
    Lấy address của script.
    
    Args:
        script: PlutusV3Script
        network: Network (MAINNET hoặc TESTNET)
        
    Returns:
        Address của script
    """
    script_hash = plutus_script_hash(script)
    return Address(script_hash, network=network)
