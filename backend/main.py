"""
CIP-68 Dynamic Asset - Backend API
==================================
FastAPI backend để xử lý các yêu cầu từ frontend.
Tạo unsigned transactions để frontend ký bằng browser wallet.

SIMPLIFIED VERSION: Non-parameterized contracts
- Fixed Policy ID
- Owner stored in datum
"""

import os
import sys
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
    Value,
    MultiAsset,
    Asset,
    AssetName,
    ScriptHash,
    UTxO,
    Transaction,
    TransactionWitnessSet,
    RawCBOR,
    plutus_script_hash,
    min_lovelace,
)
from pycardano.serialization import NonEmptyOrderedSet

from offchain.cip68_utils import (
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
    create_cip68_datum,
    get_fixed_policy_id,
    get_fixed_store_address,
    load_mint_script,
    load_store_script,
    extract_owner_from_datum,
)


# Load environment variables
load_dotenv()

# Global variables
chain_context: Optional[BlockFrostChainContext] = None
blueprint_path: Optional[str] = None
network: Network = Network.TESTNET
mint_script: Optional[PlutusV3Script] = None
store_script: Optional[PlutusV3Script] = None
policy_id: Optional[ScriptHash] = None
store_address: Optional[Address] = None


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class MintRequest(BaseModel):
    """Request model for minting CIP-68 token."""
    wallet_address: str = Field(..., description="Địa chỉ ví của người dùng")
    token_name: str = Field(..., min_length=1, max_length=32, description="Tên token")
    description: str = Field(..., min_length=1, max_length=256, description="Mô tả của NFT")


class UpdateRequest(BaseModel):
    """Request model for updating metadata."""
    wallet_address: str = Field(..., description="Địa chỉ ví của owner")
    token_name: str = Field(..., description="Tên token")
    new_description: str = Field(..., min_length=1, max_length=256, description="Mô tả mới")


class BurnRequest(BaseModel):
    """Request model for burning CIP-68 token."""
    wallet_address: str = Field(..., description="Địa chỉ ví của owner")
    token_name: str = Field(..., description="Tên token")


class TransactionResponse(BaseModel):
    """Response model containing unsigned transaction."""
    success: bool
    message: str
    tx_cbor: Optional[str] = None  # CBOR hex của unsigned transaction
    policy_id: Optional[str] = None
    token_name: Optional[str] = None


class SubmitRequest(BaseModel):
    """Request model for submitting signed transaction."""
    tx_cbor: str = Field(..., description="CBOR hex của unsigned transaction")
    witness_set_cbor: str = Field(..., description="CBOR hex của witness set từ wallet")


class SubmitResponse(BaseModel):
    """Response model for transaction submission."""
    success: bool
    message: str
    tx_hash: Optional[str] = None


class MetadataResponse(BaseModel):
    """Response model for metadata query."""
    success: bool
    message: str
    metadata: Optional[Dict[str, Any]] = None
    version: Optional[int] = None


class WalletInfoResponse(BaseModel):
    """Response model for wallet info."""
    success: bool
    address: str
    balance_lovelace: int
    utxo_count: int
    assets: List[Dict[str, Any]]


# ============================================================================
# APPLICATION LIFECYCLE
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global chain_context, mint_script, store_script, network, policy_id, store_address
    
    # Startup
    print("Starting CIP-68 Backend API (Simplified)...")
    
    # Initialize chain context
    network_str = os.getenv("NETWORK", "Preprod")
    blockfrost_url = os.getenv("BLOCKFROST_URL", "https://cardano-preprod.blockfrost.io/api")
    blockfrost_key = os.getenv("BLOCKFROST_API_KEY")
    
    network = Network.TESTNET if network_str.lower() == "preprod" else Network.MAINNET
    
    chain_context = BlockFrostChainContext(
        project_id=blockfrost_key,
        base_url=blockfrost_url,
    )
    
    # Set blueprint path
    global blueprint_path
    blueprint_path = os.path.join(
        os.path.dirname(__file__),
        '..',
        'smart_contract',
        'plutus.json'
    )
    
    if os.path.exists(blueprint_path):
        print(f"Blueprint found at {blueprint_path}")
        # Load scripts (non-parameterized)
        mint_script = load_mint_script(blueprint_path)
        store_script = load_store_script(blueprint_path)
        policy_id = get_fixed_policy_id()
        store_address = get_fixed_store_address(network)
        print(f"Fixed Policy ID: {FIXED_POLICY_ID}")
        print(f"Fixed Store Address: {store_address}")
    else:
        print(f"Warning: Blueprint not found at {blueprint_path}")
        blueprint_path = None
    
    print(f"Connected to {network_str} network")
    
    yield
    
    # Shutdown
    print("Shutting down CIP-68 Backend API...")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

app = FastAPI(
    title="CIP-68 Dynamic Asset API",
    description="""
    Backend API cho CIP-68 Dynamic Asset Demo.
    
    API này tạo unsigned transactions để frontend ký bằng browser wallet (Nami, Eternl, Lace).
    
    ## Tính năng
    
    * **Mint**: Tạo CIP-68 Dynamic NFT mới
    * **Update**: Cập nhật metadata của NFT
    * **Burn**: Đốt NFT
    * **Query**: Lấy thông tin metadata hiện tại
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "CIP-68 Dynamic Asset API",
        "network": os.getenv("NETWORK", "Preprod"),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/convert-address")
async def convert_address(hex_address: str = Query(..., description="Hex-encoded address from CIP-30")):
    """
    Convert hex-encoded address (from CIP-30 API) to bech32 format.
    CIP-30 wallets return addresses as CBOR hex, we need to convert to bech32.
    """
    try:
        # The address from CIP-30 is CBOR-encoded bytes in hex
        address_bytes = bytes.fromhex(hex_address)
        addr = Address.from_primitive(address_bytes)
        
        return {
            "success": True,
            "hex_address": hex_address,
            "bech32_address": str(addr)
        }
    except Exception as e:
        print(f"Address conversion error: {e}")
        # Try alternative parsing
        try:
            addr = Address.from_primitive(hex_address)
            return {
                "success": True,
                "hex_address": hex_address,
                "bech32_address": str(addr)
            }
        except:
            return {
                "success": False,
                "message": f"Failed to convert address: {str(e)}",
                "hex_address": hex_address,
                "bech32_address": None
            }


@app.get("/api/script-info")
async def get_script_info():
    """
    Lấy thông tin về smart contracts.
    """
    return {
        "policy_id": FIXED_POLICY_ID,
        "store_hash": FIXED_STORE_HASH,
        "store_address": str(store_address) if store_address else None,
        "network": os.getenv("NETWORK", "Preprod"),
        "message": "Using non-parameterized contracts (fixed policy ID)"
    }


@app.get("/api/wallet/{address}", response_model=WalletInfoResponse)
async def get_wallet_info(address: str):
    """Lấy thông tin ví."""
    try:
        addr = Address.from_primitive(address)
        utxos = chain_context.utxos(addr)
        
        total_lovelace = sum(utxo.output.amount.coin for utxo in utxos)
        
        # Collect assets
        assets = []
        for utxo in utxos:
            if utxo.output.amount.multi_asset:
                for policy_id, asset_dict in utxo.output.amount.multi_asset.items():
                    for asset_name, quantity in asset_dict.items():
                        assets.append({
                            "policy_id": str(policy_id),
                            "asset_name": asset_name.payload.hex(),
                            "quantity": quantity
                        })
        
        return WalletInfoResponse(
            success=True,
            address=address,
            balance_lovelace=total_lovelace,
            utxo_count=len(utxos),
            assets=assets
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/mint", response_model=TransactionResponse)
async def create_mint_transaction(request: MintRequest):
    """
    Tạo unsigned transaction để mint CIP-68 NFT.
    
    SIMPLIFIED: Uses fixed policy ID, policy_id/asset_name/owner stored in datum.
    """
    try:
        if not mint_script or not store_script:
            raise HTTPException(status_code=500, detail="Scripts not loaded")
        
        # Parse wallet address
        owner_address = Address.from_primitive(request.wallet_address)
        owner_pkh = owner_address.payment_part.to_primitive()
        
        # Get UTxOs
        utxos = chain_context.utxos(owner_address)
        if not utxos:
            raise HTTPException(status_code=400, detail="Ví không có UTxO nào!")
        
        # Create asset names
        token_name_bytes = request.token_name.encode('utf-8')
        ref_asset_name, user_asset_name = create_cip68_asset_names(token_name_bytes)
        
        # Policy ID as bytes for datum
        policy_id_bytes = bytes(policy_id)
        
        # Create CIP68 Datum with policy_id, asset_name, owner
        datum = create_cip68_datum(
            policy_id=policy_id_bytes,
            asset_name=token_name_bytes,
            owner_pkh=owner_pkh,
            metadata=request.description,
            version=1
        )
        
        # Create MultiAsset for minting
        mint_asset = Asset()
        mint_asset[ref_asset_name] = 1
        mint_asset[user_asset_name] = 1
        
        mint_assets = MultiAsset()
        mint_assets[policy_id] = mint_asset
        
        # Create redeemer
        redeemer = Redeemer(MintToken(token_name=token_name_bytes))
        
        # Calculate values
        ref_asset_only = Asset()
        ref_asset_only[ref_asset_name] = 1
        ref_multi = MultiAsset()
        ref_multi[policy_id] = ref_asset_only
        ref_value = Value(2_000_000, ref_multi)
        
        user_asset_only = Asset()
        user_asset_only[user_asset_name] = 1
        user_multi = MultiAsset()
        user_multi[policy_id] = user_asset_only
        user_value = Value(2_000_000, user_multi)
        
        # Build transaction
        builder = TransactionBuilder(chain_context)
        builder.add_input_address(owner_address)
        
        # Mint tokens
        builder.mint = mint_assets
        builder.add_minting_script(mint_script, redeemer=redeemer)
        
        # Output: Reference token to store script
        builder.add_output(
            TransactionOutput(store_address, ref_value, datum=datum)
        )
        
        # Output: User token to owner
        builder.add_output(
            TransactionOutput(owner_address, user_value)
        )
        

        # Required signers
        builder.required_signers = [owner_address.payment_part]
        
        # Build transaction body
        tx_body = builder.build(change_address=owner_address)
        
        # Build witness set (without vkey - wallet provides signature)
        witness_set = builder.build_witness_set()
        
        tx = Transaction(tx_body, witness_set)
        tx_cbor = tx.to_cbor().hex()
        
        return TransactionResponse(
            success=True,
            message="Unsigned transaction created successfully",
            tx_cbor=tx_cbor,
            policy_id=FIXED_POLICY_ID,
            token_name=request.token_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return TransactionResponse(
            success=False,
            message=f"Error creating transaction: {str(e)}"
        )


@app.post("/api/update", response_model=TransactionResponse)
async def create_update_transaction(request: UpdateRequest):
    """
    Tạo unsigned transaction để update metadata.
    
    SIMPLIFIED: Uses fixed policy ID, verifies owner from datum.
    Giữ nguyên policy_id, asset_name, owner trong datum mới.
    """
    try:
        if not store_script:
            raise HTTPException(status_code=500, detail="Store script not loaded")
        
        # Parse wallet address
        owner_address = Address.from_primitive(request.wallet_address)
        owner_pkh = owner_address.payment_part.to_primitive()
        
        # Policy ID as bytes
        policy_id_bytes = bytes(policy_id)
        
        # Create asset name
        token_name_bytes = request.token_name.encode('utf-8')
        ref_asset_name = AssetName(CIP68_REFERENCE_PREFIX + token_name_bytes)
        
        # Find reference token UTxO
        utxos = chain_context.utxos(store_address)
        ref_utxo = None
        for utxo in utxos:
            if utxo.output.amount.multi_asset:
                for pid, assets in utxo.output.amount.multi_asset.items():
                    if pid == policy_id and ref_asset_name in assets:
                        ref_utxo = utxo
                        break
        
        if not ref_utxo:
            raise HTTPException(status_code=404, detail="Reference token not found")
        
        # Get current datum and verify owner
        current_datum = ref_utxo.output.datum
        new_version = 2
        if isinstance(current_datum, CIP68Datum):
            current_owner = extract_owner_from_datum(current_datum)
            if current_owner != owner_pkh:
                raise HTTPException(status_code=403, detail="You are not the owner of this NFT")
            new_version = current_datum.version + 1
        
        # Create new datum - giữ nguyên policy_id, asset_name, owner
        new_datum = create_cip68_datum(
            policy_id=policy_id_bytes,
            asset_name=token_name_bytes,
            owner_pkh=owner_pkh,
            metadata=request.new_description,
            version=new_version
        )
        
        # Create redeemer
        redeemer = Redeemer(UpdateMetadata())
        
        # Build transaction
        builder = TransactionBuilder(chain_context)
        builder.add_input_address(owner_address)
        
        # Spend reference token UTxO
        builder.add_script_input(
            ref_utxo,
            store_script,
            redeemer=redeemer
        )
        
        # Output: Reference token back to store script
        ref_asset = Asset()
        ref_asset[ref_asset_name] = 1
        ref_multi = MultiAsset()
        ref_multi[policy_id] = ref_asset
        ref_value = Value(ref_utxo.output.amount.coin, ref_multi)
        
        builder.add_output(
            TransactionOutput(store_address, ref_value, datum=new_datum)
        )
        
        # Required signers
        builder.required_signers = [owner_address.payment_part]
        
        # Build transaction body
        tx_body = builder.build(change_address=owner_address)
        
        # Build witness set (without vkey - wallet provides signature)
        witness_set = builder.build_witness_set()
        
        tx = Transaction(tx_body, witness_set)
        tx_cbor = tx.to_cbor().hex()
        
        return TransactionResponse(
            success=True,
            message="Update transaction created successfully",
            tx_cbor=tx_cbor,
            policy_id=FIXED_POLICY_ID,
            token_name=request.token_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return TransactionResponse(
            success=False,
            message=f"Error creating update transaction: {str(e)}"
        )


@app.post("/api/burn", response_model=TransactionResponse)
async def create_burn_transaction(request: BurnRequest):
    """
    Tạo unsigned transaction để burn CIP-68 NFT.
    
    SIMPLIFIED: Uses fixed policy ID, verifies owner from datum.
    """
    try:
        if not mint_script or not store_script:
            raise HTTPException(status_code=500, detail="Scripts not loaded")
        
        # Parse inputs
        owner_address = Address.from_primitive(request.wallet_address)
        owner_pkh = owner_address.payment_part.to_primitive()
        
        # Create asset names
        token_name_bytes = request.token_name.encode('utf-8')
        ref_asset_name, user_asset_name = create_cip68_asset_names(token_name_bytes)
        
        # Find reference token UTxO
        store_utxos = chain_context.utxos(store_address)
        ref_utxo = None
        for utxo in store_utxos:
            if utxo.output.amount.multi_asset:
                for pid, assets in utxo.output.amount.multi_asset.items():
                    if pid == policy_id and ref_asset_name in assets:
                        ref_utxo = utxo
                        break
        
        if not ref_utxo:
            raise HTTPException(status_code=404, detail="Reference token not found")
        
        # Verify owner from datum
        current_datum = ref_utxo.output.datum
        if isinstance(current_datum, CIP68Datum):
            current_owner = extract_owner_from_datum(current_datum)
            if current_owner != owner_pkh:
                raise HTTPException(status_code=403, detail="You are not the owner of this NFT")
        
        # Find user token UTxO
        owner_utxos = chain_context.utxos(owner_address)
        user_utxo = None
        for utxo in owner_utxos:
            if utxo.output.amount.multi_asset:
                for pid, assets in utxo.output.amount.multi_asset.items():
                    if pid == policy_id and user_asset_name in assets:
                        user_utxo = utxo
                        break
        
        if not user_utxo:
            raise HTTPException(status_code=404, detail="User token not found in wallet")
        
        # Create burn assets (negative quantities)
        burn_asset = Asset()
        burn_asset[ref_asset_name] = -1
        burn_asset[user_asset_name] = -1
        
        burn_assets = MultiAsset()
        burn_assets[policy_id] = burn_asset
        
        # Create redeemers
        mint_redeemer = Redeemer(BurnToken(token_name=token_name_bytes))
        spend_redeemer = Redeemer(BurnReference())
        
        # Build transaction
        builder = TransactionBuilder(chain_context)
        builder.add_input_address(owner_address)
        
        # Spend reference token
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
        builder.required_signers = [owner_address.payment_part]
        
        # Build transaction body
        tx_body = builder.build(change_address=owner_address)
        
        # Build witness set (without vkey - wallet provides signature)
        witness_set = builder.build_witness_set()
        
        tx = Transaction(tx_body, witness_set)
        tx_cbor = tx.to_cbor().hex()
        
        return TransactionResponse(
            success=True,
            message="Burn transaction created successfully",
            tx_cbor=tx_cbor,
            policy_id=FIXED_POLICY_ID,
            token_name=request.token_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        return TransactionResponse(
            success=False,
            message=f"Error creating burn transaction: {str(e)}"
        )


@app.post("/api/submit", response_model=SubmitResponse)
async def submit_transaction(request: SubmitRequest):
    """
    Submit signed transaction to blockchain.
    Merge witnesses using proper PyCardano types with NonEmptyOrderedSet.
    """
    try:
       # 1. Load lại Transaction gốc từ CBOR (chứa Body + Scripts/Redeemers do Backend tạo)
        # Lưu ý: backend_tx này chưa có chữ ký ví (vkey_witnesses)
        backend_tx = Transaction.from_cbor(bytes.fromhex(request.tx_cbor))
        
        # 2. Parse Witness Set từ Frontend (Chỉ chứa vkey_witnesses - chữ ký ví)
        wallet_witness = TransactionWitnessSet.from_cbor(bytes.fromhex(request.witness_set_cbor))
        
        # 3. Hợp nhất (Merge) an toàn
        # Lấy witness set hiện tại của backend (đang chứa scripts, redeemers)
        final_witness_set = backend_tx.transaction_witness_set
        
        # Nếu ví có trả về chữ ký (vkey), hãy thêm nó vào
        if wallet_witness.vkey_witnesses:
            if final_witness_set.vkey_witnesses:
                # Nếu backend cũng đã ký gì đó (ít gặp), thì nối thêm vào
                # Lưu ý: PyCardano dùng NonEmptyOrderedSet cho vkey_witnesses
                existing_vkeys = list(final_witness_set.vkey_witnesses)
                new_vkeys = list(wallet_witness.vkey_witnesses)
                final_witness_set.vkey_witnesses = NonEmptyOrderedSet(existing_vkeys + new_vkeys)
            else:
                # Trường hợp phổ biến: Backend chưa có vkey nào, gán luôn của ví vào
                final_witness_set.vkey_witnesses = wallet_witness.vkey_witnesses

        # 4. Gán ngược lại vào Transaction
        backend_tx.transaction_witness_set = final_witness_set
        
        # 5. Submit
        # Quan trọng: Dùng backend_tx.to_cbor() để đảm bảo cấu trúc Body giữ nguyên
        tx_hash = chain_context.submit_tx_cbor(backend_tx.to_cbor())
        
        return SubmitResponse(
            success=True,
            message="Transaction submitted successfully",
            tx_hash=str(tx_hash)
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return SubmitResponse(
            success=False,
            message=f"Error submitting transaction: {str(e)}"
        )


@app.get("/api/metadata/{token_name}", response_model=MetadataResponse)
async def get_metadata(token_name: str):
    """
    Lấy metadata hiện tại của CIP-68 NFT.
    
    SIMPLIFIED: Uses fixed policy ID and store address.
    """
    try:
        if not store_address:
            raise HTTPException(status_code=500, detail="Store address not initialized")
        
        # Create asset name
        token_name_bytes = token_name.encode('utf-8')
        ref_asset_name = AssetName(CIP68_REFERENCE_PREFIX + token_name_bytes)
        
        print(f"\n=== METADATA FETCH DEBUG ===")
        print(f"Token name: {token_name}")
        print(f"Looking for ref asset: {ref_asset_name.payload.hex()}")
        
        # Find reference token UTxO
        utxos = chain_context.utxos(store_address)
        print(f"Found {len(utxos)} UTxOs at store address")
        
        for utxo in utxos:
            if utxo.output.amount.multi_asset:
                for p, assets in utxo.output.amount.multi_asset.items():
                    print(f"Policy: {p.payload.hex()}")
                    for asset_name, qty in assets.items():
                        print(f"  Asset: {asset_name.payload.hex()} = {qty}")
                    
                    if p == policy_id and ref_asset_name in assets:
                        print(f"✅ Found matching NFT!")
                        datum = utxo.output.datum
                        print(f"Datum type: {type(datum)}")
                        
                        # If datum is RawCBOR, deserialize it
                        if isinstance(datum, RawCBOR):
                            try:
                                datum = CIP68Datum.from_cbor(datum.cbor)
                                print(f"Deserialized to CIP68Datum")
                            except Exception as e:
                                print(f"Failed to deserialize datum: {e}")
                                continue
                        
                        if isinstance(datum, CIP68Datum):
                            # Convert bytes keys and values to strings
                            metadata = {}
                            for k, v in datum.metadata.items():
                                # Decode key
                                key = k.decode('utf-8') if isinstance(k, bytes) else str(k)
                                
                                # Decode value - handle various types
                                if isinstance(v, bytes):
                                    value = v.decode('utf-8')
                                elif hasattr(v, 'to_primitive'):
                                    # PlutusData object
                                    prim = v.to_primitive()
                                    if isinstance(prim, bytes):
                                        value = prim.decode('utf-8')
                                    else:
                                        value = str(prim)
                                else:
                                    value = str(v)
                                    
                                metadata[key] = value
                            
                            print(f"Metadata extracted: {metadata}")
                            
                            return MetadataResponse(
                                success=True,
                                message="Metadata found",
                                metadata=metadata,
                                version=datum.version
                            )
        
        print(f"❌ NFT not found")
        return MetadataResponse(
            success=False,
            message="NFT not found"
        )
        
    except Exception as e:
        return MetadataResponse(
            success=False,
            message=f"Error fetching metadata: {str(e)}"
        )


@app.get("/api/tokens")
async def list_all_tokens():
    """
    List all CIP-68 tokens.
    """
    try:
        if not store_address:
            raise HTTPException(status_code=500, detail="Store address not initialized")
        
        tokens = []
        utxos = chain_context.utxos(store_address)
        
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
                                }
                                
                                if isinstance(datum, CIP68Datum):
                                    token_info['owner'] = datum.owner.hex()
                                    token_info['version'] = datum.version
                                
                                tokens.append(token_info)
        
        return {
            "success": True,
            "tokens": tokens,
            "count": len(tokens)
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error listing tokens: {str(e)}",
            "tokens": []
        }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
