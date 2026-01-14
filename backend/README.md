# CIP-68 Dynamic Asset Backend

Python backend sử dụng FastAPI và PyCardano.

## Cài đặt

```bash
pip install -r requirements.txt
```

## Chạy server

```bash
python main.py
```

Hoặc:

```bash
uvicorn main:app --reload --port 8000
```

## API Endpoints

- `GET /` - Health check
- `GET /api/script-info` - Thông tin smart contracts
- `GET /api/wallet/{address}` - Thông tin ví
- `POST /api/mint` - Tạo transaction mint NFT
- `POST /api/update` - Tạo transaction update metadata
- `POST /api/burn` - Tạo transaction burn NFT
- `POST /api/submit` - Submit signed transaction
- `GET /api/metadata/{policy_id}/{token_name}` - Lấy metadata
