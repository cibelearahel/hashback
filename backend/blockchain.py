import time
import json
import hashlib
import os
from typing import List, Dict, Any, Optional, Tuple
from .transaction import Transaction
from .contract import HashBackContract

class Block:
    def __init__(
        self,
        index: int,
        timestamp: float,
        transactions: List[Dict[str, Any]],
        previous_hash: str,
        current_hash: Optional[str] = None
    ):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.current_hash = current_hash or self.calculate_hash()

    def calculate_hash(self) -> str:
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode('utf-8')
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(
            index=data["index"],
            timestamp=data["timestamp"],
            transactions=data["transactions"],
            previous_hash=data["previous_hash"],
            current_hash=data.get("current_hash")
        )

class Blockchain:
    def __init__(self, storage_file: str = "chain_data.json"):
        self.storage_file = storage_file
        self.chain: List[Block] = []
        self.contract = HashBackContract()
        self.state: Dict[str, Any] = {
            "balances": {},
            "nonces": {},
            "vouchers": []
        }
        self.load_or_initialize()

    def create_genesis_block(self) -> Block:
        genesis_block = Block(
            index=0,
            timestamp=1700000000.0,
            transactions=[],
            previous_hash="0000000000000000000000000000000000000000000000000000000000000000",
            current_hash=None
        )
        return genesis_block

    def load_or_initialize(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chain = [Block.from_dict(b) for b in data.get("chain", [])]
                    # Reconstrói o estado executando a cadeia a partir do gênesis
                    self.rebuild_state()
                    return
            except Exception as e:
                print(f"Erro ao carregar blockchain existente, criando nova: {e}")

        # Se não existe ou deu erro, inicializa do gênesis
        self.chain = [self.create_genesis_block()]
        self.save_chain()

    def rebuild_state(self):
        """Reconstrói o World State do contrato inteligente a partir do histórico de blocos."""
        self.state = {
            "balances": {},
            "nonces": {},
            "vouchers": []
        }
        for block in self.chain:
            for tx_data in block.transactions:
                tx = Transaction.from_dict(tx_data)
                self.contract.apply_transaction(tx, self.state)

    def save_chain(self):
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump({
                "chain": [b.to_dict() for b in self.chain]
            }, f, indent=2)

    def get_last_block(self) -> Block:
        return self.chain[-1]

    def add_transaction_and_mine(self, tx: Transaction) -> Tuple[bool, str, Optional[Block]]:
        """
        Valida a transação através do Contrato Inteligente e, se aprovada,
        sela e anexa instantaneamente um novo bloco à cadeia local.
        """
        # 1. Validação estrita pelo Contrato Inteligente
        is_valid, reason = self.contract.validate_transaction(tx, self.state)
        if not is_valid:
            return False, reason, None

        # 2. Gera o ID determinístico da transação caso não exista
        if not tx.tx_id:
            tx_repr = json.dumps(tx.to_dict(), sort_keys=True).encode('utf-8')
            tx.tx_id = "0x" + hashlib.sha256(tx_repr).hexdigest()

        # 3. Aplica no estado do contrato (atualização atômica)
        self.contract.apply_transaction(tx, self.state)

        # 4. Cria e conecta o novo bloco na cadeia
        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            transactions=[tx.to_dict()],
            previous_hash=last_block.current_hash
        )

        self.chain.append(new_block)
        self.save_chain()

        return True, "Transação validada pelo Contrato Inteligente e selada com sucesso no novo bloco.", new_block

    def is_chain_valid(self) -> Tuple[bool, str]:
        """Verifica a integridade criptográfica de todos os blocos encadeados."""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i - 1]

            if current.previous_hash != prev.current_hash:
                return False, f"Bloco #{current.index} aponta para previous_hash inválido."

            recalculated = current.calculate_hash()
            if current.current_hash != recalculated:
                return False, f"Hash do Bloco #{current.index} foi adulterado."

        return True, "A Blockchain local está íntegra e 100% válida."
