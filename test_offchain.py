"""
Test script for CIP-68 Off-chain Operations
============================================
Test các chức năng cơ bản của offchain code.
"""
import os
import sys
from dotenv import load_dotenv

# Add project root to path
project_root = os.path.abspath(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from pycardano import (
    BlockFrostChainContext,
    Network,
    Address,
    PaymentSigningKey,
    PaymentVerificationKey,
    StakeSigningKey,
    StakeVerificationKey,
    HDWallet,
    PlutusV3Script,
    plutus_script_hash,
)

from offchain.cip68_utils import (
    load_scripts,
    get_script_address,
    create_cip68_asset_names,
    create_cip68_datum,
    get_policy_id,
)

def test_load_scripts():
    """Test loading scripts from blueprint."""
    print("\n=== Test 1: Load Scripts ===")
    
    # Use absolute path from project root
    blueprint_path = os.path.abspath(os.path.join(project_root, 'smart_contract', 'plutus.json'))
    
    if not os.path.exists(blueprint_path):
        print(f"❌ Blueprint not found at {blueprint_path}")
        return False
    
    try:
        scripts = load_scripts(blueprint_path)
        print(f"✅ Loaded {len(scripts)} scripts")
        
        for title, info in scripts.items():
            print(f"\n  Script: {title}")
            print(f"    Hash: {info['hash']}")
            print(f"    Code length: {len(info['compiled_code'])} chars")
        
        return True
    except Exception as e:
        print(f"❌ Error loading scripts: {e}")
        return False


def test_script_hashes():
    """Test script hash calculation."""
    print("\n=== Test 2: Script Hashes ===")
    
    blueprint_path = os.path.abspath(os.path.join(project_root, 'smart_contract', 'plutus.json'))
    scripts = load_scripts(blueprint_path)
    
    try:
        # Create PlutusV3Script objects
        mint_script = PlutusV3Script(bytes.fromhex(scripts['cip68.cip68_mint.mint']['compiled_code']))
        store_script = PlutusV3Script(bytes.fromhex(scripts['cip68.cip68_store.spend']['compiled_code']))
        
        mint_hash = plutus_script_hash(mint_script)
        store_hash = plutus_script_hash(store_script)
        
        print(f"✅ Mint Policy ID: {mint_hash.to_primitive().hex()}")
        print(f"✅ Store Script Hash: {store_hash.to_primitive().hex()}")
        
        return True
    except Exception as e:
        print(f"❌ Error calculating hashes: {e}")
        return False


def test_wallet_creation():
    """Test wallet creation from seed phrase."""
    print("\n=== Test 3: Wallet Creation ===")
    
    load_dotenv()
    seed_phrase = os.getenv('SEED_PHRASE')
    
    if not seed_phrase:
        print("❌ SEED_PHRASE not found in .env")
        return False
    
    try:
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
        
        print(f"✅ Address: {str(address)}")
        print(f"   Payment Key Hash: {payment_vkey.hash().to_primitive().hex()}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating wallet: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_blockfrost_connection():
    """Test Blockfrost connection."""
    print("\n=== Test 4: Blockfrost Connection ===")
    
    load_dotenv()
    blockfrost_url = os.getenv('BLOCKFROST_URL', 'https://cardano-preprod.blockfrost.io/api')
    blockfrost_key = os.getenv('BLOCKFROST_API_KEY')
    
    if not blockfrost_key:
        print("❌ BLOCKFROST_API_KEY not found in .env")
        return False
    
    try:
        context = BlockFrostChainContext(
            project_id=blockfrost_key,
            base_url=blockfrost_url,
        )
        
        # Test query epoch info
        epoch = context.epoch
        print(f"✅ Connected to Blockfrost")
        print(f"   Current epoch: {epoch}")
        
        return True
    except Exception as e:
        print(f"❌ Error connecting to Blockfrost: {e}")
        return False


def test_cip68_utils():
    """Test CIP-68 utility functions."""
    print("\n=== Test 5: CIP-68 Utils ===")
    
    try:
        # Test asset name creation
        token_name = "TestNFT"
        ref_asset, user_asset = create_cip68_asset_names(token_name)
        
        print(f"✅ Token name: {token_name}")
        print(f"   Reference asset: {ref_asset.payload.hex()}")
        print(f"   User asset: {user_asset.payload.hex()}")
        
        # Test datum creation
        metadata = {
            "name": token_name,
            "description": "Test NFT",
            "image": "ipfs://test"
        }
        datum = create_cip68_datum(metadata, version=1)
        print(f"✅ Created datum with version: {datum.version}")
        
        return True
    except Exception as e:
        print(f"❌ Error in CIP-68 utils: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_query_utxos():
    """Test querying UTxOs from address."""
    print("\n=== Test 6: Query UTxOs ===")
    
    load_dotenv()
    
    try:
        # Create context
        blockfrost_url = os.getenv('BLOCKFROST_URL', 'https://cardano-preprod.blockfrost.io/api')
        blockfrost_key = os.getenv('BLOCKFROST_API_KEY')
        
        context = BlockFrostChainContext(
            project_id=blockfrost_key,
            base_url=blockfrost_url,
        )
        
        # Create wallet
        seed_phrase = os.getenv('SEED_PHRASE')
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
        # Query UTxOs
        utxos = context.utxos(address)
        
        print(f"✅ Address: {str(address)}")
        print(f"   UTxOs found: {len(utxos)}")
        
        total_lovelace = sum(utxo.output.amount.coin for utxo in utxos)
        print(f"   Total ADA: {total_lovelace / 1_000_000:.2f} ADA")
        
        if len(utxos) == 0:
            print("\n⚠️  Warning: No UTxOs found!")
            print("   Please fund this address with test ADA from:")
            print("   https://docs.cardano.org/cardano-testnet/tools/faucet")
        
        return True
    except Exception as e:
        print(f"❌ Error querying UTxOs: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("CIP-68 Off-chain Code Tests")
    print("=" * 60)
    
    tests = [
        ("Load Scripts", test_load_scripts),
        ("Script Hashes", test_script_hashes),
        ("Wallet Creation", test_wallet_creation),
        ("Blockfrost Connection", test_blockfrost_connection),
        ("CIP-68 Utils", test_cip68_utils),
        ("Query UTxOs", test_query_utxos),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
