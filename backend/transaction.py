import time
from typing import Optional, Dict, Any

class Transaction:
    TYPES = ["MINT", "TRANSFER", "REDEEM"]

    def __init__(
        self,
        tx_type: str,
        sender: str,
        recipient: str,
        amount: int,
        sender_public_key: str,
        reward_id: Optional[str] = None,
        nonce: int = 0,
        timestamp: Optional[float] = None,
        signature: Optional[str] = None,
        tx_id: Optional[str] = None
    ):
        if tx_type not in self.TYPES:
            raise ValueError(f"Tipo de transação inválido: {tx_type}")
        if amount <= 0:
            raise ValueError(f"Quantidade de pontos deve ser maior que zero: {amount}")

        self.type = tx_type
        self.sender = sender
        self.recipient = recipient
        self.amount = int(amount)
        self.sender_public_key = sender_public_key
        self.reward_id = reward_id
        self.nonce = int(nonce)
        self.timestamp = timestamp or time.time()
        self.signature = signature
        self.tx_id = tx_id

    def to_signable_dict(self) -> Dict[str, Any]:
        """Retorna o dicionário determinístico que é assinado pelo remetente."""
        return {
            "type": self.type,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "reward_id": self.reward_id,
            "nonce": self.nonce
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tx_id": self.tx_id,
            "type": self.type,
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "sender_public_key": self.sender_public_key,
            "reward_id": self.reward_id,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "signature": self.signature
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            tx_type=data["type"],
            sender=data["sender"],
            recipient=data["recipient"],
            amount=data["amount"],
            sender_public_key=data.get("sender_public_key", ""),
            reward_id=data.get("reward_id"),
            nonce=data.get("nonce", 0),
            timestamp=data.get("timestamp"),
            signature=data.get("signature"),
            tx_id=data.get("tx_id")
        )
