import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any

from .wallet import Wallet
from .transaction import Transaction
from .blockchain import Blockchain

app = FastAPI(title="HashBack DApp Blockchain API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

blockchain = Blockchain(storage_file="chain_data.json")

DEMO_SEEDS = {
    "merchant": "0101010101010101010101010101010101010101010101010101010101010101",
    "alice": "0202020202020202020202020202020202020202020202020202020202020202",
    "bob": "0303030303030303030303030303030303030303030303030303030303030303"
}

demo_wallets = {}
for name, seed in DEMO_SEEDS.items():
    w = Wallet.from_private_key_hex(seed)
    demo_wallets[name] = {
        "name": "Loja Parceira" if name == "merchant" else name.capitalize(),
        "role": "MERCHANT" if name == "merchant" else "CUSTOMER",
        "address": w.address,
        "public_key": w.public_key_hex,
        "private_key": w.private_key_hex
    }

blockchain.contract.add_merchant(demo_wallets["merchant"]["address"])

class SendTransactionRequest(BaseModel):
    type: str
    sender: str
    recipient: str
    amount: int
    sender_public_key: str
    reward_id: Optional[str] = None
    nonce: int
    signature: str

class QuickActionRequest(BaseModel):
    account_key: str
    action_type: str # MINT, TRANSFER, REDEEM, DOUBLE_SPEND_ATTACK, UNAUTHORIZED_MINT, TRANSFER_TO_MERCHANT_ATTACK, MERCHANT_REDEEM_ATTACK
    recipient: Optional[str] = None
    amount: Optional[int] = 0
    reward_id: Optional[str] = None

@app.get("/api/demo-accounts")
def get_demo_accounts():
    accounts = []
    balances = blockchain.state.get("balances", {})
    nonces = blockchain.state.get("nonces", {})
    merchant_stats = blockchain.state.get("merchant_stats", {})

    for key, data in demo_wallets.items():
        is_merch = blockchain.contract.is_merchant(data["address"])
        stats = merchant_stats.get(data["address"], {"total_issued": 0, "clients": []})
        accounts.append({
            "key": key,
            "name": data["name"],
            "role": data["role"],
            "address": data["address"],
            "public_key": data["public_key"],
            "private_key": data["private_key"],
            "balance": balances.get(data["address"], 0),
            "nonce": nonces.get(data["address"], 0),
            "is_merchant": is_merch,
            "total_issued": stats.get("total_issued", 0),
            "clients_count": len(stats.get("clients", []))
        })
    return accounts

@app.get("/api/chain")
def get_chain():
    is_valid, reason = blockchain.is_chain_valid()
    return {
        "length": len(blockchain.chain),
        "is_valid": is_valid,
        "validity_report": reason,
        "chain": [b.to_dict() for b in blockchain.chain]
    }

@app.get("/api/state")
def get_contract_state():
    return {
        "balances": blockchain.state.get("balances", {}),
        "nonces": blockchain.state.get("nonces", {}),
        "vouchers": blockchain.state.get("vouchers", []),
        "merchant_stats": blockchain.state.get("merchant_stats", {}),
        "authorized_merchants": blockchain.contract.authorized_merchants,
        "rewards": list(blockchain.contract.rewards.values())
    }

@app.get("/api/rewards")
def get_rewards():
    return list(blockchain.contract.rewards.values())

@app.post("/api/quick-action")
def quick_action(req: QuickActionRequest):
    if req.account_key not in demo_wallets:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")

    sender_data = demo_wallets[req.account_key]
    wallet = Wallet.from_private_key_hex(sender_data["private_key"])
    current_nonce = blockchain.state.get("nonces", {}).get(wallet.address, 0)

    # 1. Teste: Transferência de Cliente para Loja (Proibido)
    if req.action_type == "TRANSFER_TO_MERCHANT_ATTACK":
        tx = Transaction(
            tx_type="TRANSFER",
            sender=wallet.address,
            recipient=demo_wallets["merchant"]["address"],
            amount=20,
            sender_public_key=wallet.public_key_hex,
            nonce=current_nonce
        )
        tx.signature = wallet.sign(tx.to_signable_dict())
        success, msg, block = blockchain.add_transaction_and_mine(tx)
        if not success:
            raise HTTPException(status_code=400, detail=f"[CONTRATO BLOQUEOU]: {msg}")
        return {"success": True, "message": msg}

    # 2. Teste: Loja tentando resgatar recompensa (Proibido)
    elif req.action_type == "MERCHANT_REDEEM_ATTACK":
        reward = blockchain.contract.rewards.get("REW-1")
        tx = Transaction(
            tx_type="REDEEM",
            sender=demo_wallets["merchant"]["address"],
            recipient=blockchain.contract.BURN_ADDRESS,
            amount=reward["points"],
            sender_public_key=wallet.public_key_hex,
            reward_id="REW-1",
            nonce=current_nonce
        )
        tx.signature = wallet.sign(tx.to_signable_dict())
        success, msg, block = blockchain.add_transaction_and_mine(tx)
        if not success:
            raise HTTPException(status_code=400, detail=f"[CONTRATO BLOQUEOU]: {msg}")
        return {"success": True, "message": msg}

    # 3. Teste: Emissão Não Autorizada (Cliente tentando emitir)
    elif req.action_type == "UNAUTHORIZED_MINT":
        tx = Transaction(
            tx_type="MINT",
            sender=wallet.address,
            recipient=req.recipient or demo_wallets["alice"]["address"],
            amount=req.amount if req.amount > 0 else 500,
            sender_public_key=wallet.public_key_hex,
            nonce=current_nonce
        )
        tx.signature = wallet.sign(tx.to_signable_dict())
        success, msg, block = blockchain.add_transaction_and_mine(tx)
        if not success:
            raise HTTPException(status_code=400, detail=f"[CONTRATO BLOQUEOU]: {msg}")
        return {"success": True, "message": msg}

    # 4. Teste: Gasto Duplo
    elif req.action_type == "DOUBLE_SPEND_ATTACK":
        current_balance = blockchain.state.get("balances", {}).get(wallet.address, 0)
        tx = Transaction(
            tx_type="TRANSFER",
            sender=wallet.address,
            recipient=req.recipient or demo_wallets["bob"]["address"],
            amount=current_balance + 9999,
            sender_public_key=wallet.public_key_hex,
            nonce=current_nonce
        )
        tx.signature = wallet.sign(tx.to_signable_dict())
        success, msg, block = blockchain.add_transaction_and_mine(tx)
        if not success:
            raise HTTPException(status_code=400, detail=f"[GASTO DUPLO BLOQUEADO]: {msg}")
        return {"success": True, "message": msg}

    # 5. Operações Normais
    elif req.action_type == "MINT":
        tx = Transaction(
            tx_type="MINT",
            sender=wallet.address,
            recipient=req.recipient,
            amount=req.amount,
            sender_public_key=wallet.public_key_hex,
            nonce=current_nonce
        )
        tx.signature = wallet.sign(tx.to_signable_dict())
        success, msg, block = blockchain.add_transaction_and_mine(tx)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg, "block": block.to_dict()}

    elif req.action_type == "TRANSFER":
        tx = Transaction(
            tx_type="TRANSFER",
            sender=wallet.address,
            recipient=req.recipient,
            amount=req.amount,
            sender_public_key=wallet.public_key_hex,
            nonce=current_nonce
        )
        tx.signature = wallet.sign(tx.to_signable_dict())
        success, msg, block = blockchain.add_transaction_and_mine(tx)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg, "block": block.to_dict()}

    elif req.action_type == "REDEEM":
        reward = blockchain.contract.rewards.get(req.reward_id)
        if not reward:
            raise HTTPException(status_code=400, detail="Recompensa selecionada inválida.")

        tx = Transaction(
            tx_type="REDEEM",
            sender=wallet.address,
            recipient=blockchain.contract.BURN_ADDRESS,
            amount=reward["points"],
            sender_public_key=wallet.public_key_hex,
            reward_id=req.reward_id,
            nonce=current_nonce
        )
        tx.signature = wallet.sign(tx.to_signable_dict())
        success, msg, block = blockchain.add_transaction_and_mine(tx)
        if not success:
            raise HTTPException(status_code=400, detail=msg)
        return {"success": True, "message": msg, "block": block.to_dict()}

    raise HTTPException(status_code=400, detail="Ação desconhecida.")

@app.post("/api/reset")
def reset_blockchain():
    if os.path.exists("chain_data.json"):
        os.remove("chain_data.json")
    blockchain.load_or_initialize()
    blockchain.contract.add_merchant(demo_wallets["merchant"]["address"])
    return {"success": True, "message": "Blockchain reinicializada no Bloco Gênesis."}

frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
