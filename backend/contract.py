from typing import Dict, Any, List, Tuple
from .transaction import Transaction
from .wallet import Wallet

class HashBackContract:
    """
    Contrato Inteligente do Programa de Fidelidade HashBack.
    Regras de Negócio e Governança:
    1. Perfil EMISSOR (Loja Parceira):
       - Apenas lojas credenciadas podem invocar MINT.
       - A loja é um canal emissor: NÃO PODE receber transferências de pontos (não acumula saldo).
       - A loja NÃO PODE resgatar recompensas (não pode invocar REDEEM).
    2. Perfil RECEPTOR (Cliente):
       - Clientes acumulam pontos através de compras nas lojas (MINT) ou transferências de outros clientes.
       - Clientes podem transferir (TRANSFER) pontos exclusivamente para outros clientes (nunca para lojas).
       - Clientes podem resgatar (REDEEM) recompensas do catálogo oficial.
    3. PREVENÇÃO DE GASTO DUPLO (Double-Spending):
       - Verificação atômica: saldo atual do cliente >= valor da transação.
       - Nonce sequencial por conta para mitigar replay attacks.
    4. Criptografia ECDSA secp256k1 obrigatória em todas as transações.
    """

    DEFAULT_REWARDS = [
        {"id": "REW-1", "name": "Cupom de R$ 20 OFF", "points": 100, "description": "Válido para compras acima de R$ 50 em qualquer loja credenciada."},
        {"id": "REW-2", "name": "Frete Grátis Nacional", "points": 50, "description": "Válido para 1 entrega padrão sem valor mínimo de pedido."},
        {"id": "REW-3", "name": "Brinde Especial HashBack", "points": 250, "description": "Kit exclusivo com garrafa térmica e ecobag sustentável."},
        {"id": "REW-4", "name": "Acesso VIP / Cashback em Dobro", "points": 400, "description": "30 dias de acúmulo de pontos em dobro em todos os parceiros."}
    ]

    BURN_ADDRESS = "0x0000000000000000000000000000000000000000"

    def __init__(self):
        self.rewards: Dict[str, Dict[str, Any]] = {r["id"]: r for r in self.DEFAULT_REWARDS}
        self.authorized_merchants: List[str] = []

    def add_merchant(self, address: str):
        if address not in self.authorized_merchants:
            self.authorized_merchants.append(address)

    def is_merchant(self, address: str) -> bool:
        return address.lower() in [m.lower() for m in self.authorized_merchants]

    def validate_transaction(self, tx: Transaction, state: Dict[str, Any]) -> Tuple[bool, str]:
        """Validação determinística das regras do contrato inteligente."""
        # 1. Criptografia e Assinatura
        if not tx.signature:
            return False, "Rejeitada pelo Contrato: Transação não assinada."
        if not tx.sender_public_key:
            return False, "Rejeitada pelo Contrato: Chave pública do remetente ausente."

        expected_sender = Wallet.get_address_from_public_key(tx.sender_public_key)
        if expected_sender.lower() != tx.sender.lower():
            return False, f"Rejeitada pelo Contrato: Remetente ({tx.sender}) não corresponde à chave pública."

        if not Wallet.verify(tx.sender_public_key, tx.to_signable_dict(), tx.signature):
            return False, "Rejeitada pelo Contrato: Assinatura criptográfica ECDSA inválida."

        # 2. Nonce anti-replay
        sender_nonces = state.get("nonces", {})
        expected_nonce = sender_nonces.get(tx.sender, 0)
        if tx.nonce != expected_nonce:
            return False, f"Rejeitada pelo Contrato: Nonce inválido. Esperado: {expected_nonce}, Recebido: {tx.nonce}."

        balances = state.get("balances", {})
        sender_balance = balances.get(tx.sender, 0)

        # 3. Regras por Tipo de Operação
        if tx.type == "MINT":
            # Apenas lojas credenciadas podem emitir
            if not self.is_merchant(tx.sender):
                return False, f"Rejeitada pelo Contrato: Apenas lojas parceiras autorizadas podem emitir pontos. Endereço {tx.sender} não possui permissão de MINT."
            # A loja não pode emitir pontos para si mesma ou para outra loja
            if self.is_merchant(tx.recipient):
                return False, "Rejeitada pelo Contrato: Lojas não podem receber pontos. Destinatário de emissão deve ser um cliente."
            if not tx.recipient or tx.recipient == self.BURN_ADDRESS:
                return False, "Rejeitada pelo Contrato: Endereço de cliente inválido."
            return True, "Emissão aprovada pelo contrato."

        elif tx.type == "TRANSFER":
            # A loja não transfere pontos (ela emite via MINT)
            if self.is_merchant(tx.sender):
                return False, "Rejeitada pelo Contrato: Lojas não realizam transferências de pontos comuns, apenas emissão autorizada (MINT)."
            # Não é permitido transferir pontos para lojas
            if self.is_merchant(tx.recipient):
                return False, "Rejeitada pelo Contrato: Lojas parceiras não acumulam ou recebem pontos de clientes."
            if tx.sender.lower() == tx.recipient.lower():
                return False, "Rejeitada pelo Contrato: Remetente e destinatário não podem ser o mesmo endereço."
            # Prevenção de Gasto Duplo
            if sender_balance < tx.amount:
                return False, f"Rejeitada pelo Contrato: Tentativa de gasto duplo ou saldo insuficiente. Saldo atual: {sender_balance} pts, Tentativa: {tx.amount} pts."
            return True, "Transferência entre clientes aprovada pelo contrato."

        elif tx.type == "REDEEM":
            # A loja NUNCA pode resgatar recompensas
            if self.is_merchant(tx.sender):
                return False, "Rejeitada pelo Contrato: Lojas parceiras não podem resgatar recompensas. O catálogo é exclusivo para clientes."

            if not tx.reward_id:
                return False, "Rejeitada pelo Contrato: Identificador da recompensa (reward_id) é obrigatório."
            reward = self.rewards.get(tx.reward_id)
            if not reward:
                return False, f"Rejeitada pelo Contrato: Recompensa '{tx.reward_id}' não existe no catálogo oficial."

            if tx.amount != reward["points"]:
                return False, f"Rejeitada pelo Contrato: Quantidade de pontos difere do custo do item ({reward['points']} pts)."

            # Prevenção de Gasto Duplo no Resgate
            if sender_balance < tx.amount:
                return False, f"Rejeitada pelo Contrato: Saldo insuficiente para resgatar este item. Saldo atual: {sender_balance} pts, Custo: {tx.amount} pts."

            return True, "Resgate de recompensa aprovado pelo contrato."

        return False, f"Tipo de transação desconhecido: {tx.type}"

    def apply_transaction(self, tx: Transaction, state: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica a mutação de estado de forma atômica."""
        balances = state.setdefault("balances", {})
        nonces = state.setdefault("nonces", {})
        vouchers = state.setdefault("vouchers", [])
        merchant_stats = state.setdefault("merchant_stats", {})

        # Incrementa o nonce do remetente
        nonces[tx.sender] = nonces.get(tx.sender, 0) + 1

        if tx.type == "MINT":
            # Credita pontos ao cliente receptor
            balances[tx.recipient] = balances.get(tx.recipient, 0) + tx.amount
            # Registra estatística de emissão da loja
            stats = merchant_stats.setdefault(tx.sender, {"total_issued": 0, "clients": []})
            stats["total_issued"] += tx.amount
            if tx.recipient not in stats["clients"]:
                stats["clients"].append(tx.recipient)

        elif tx.type == "TRANSFER":
            balances[tx.sender] = balances.get(tx.sender, 0) - tx.amount
            balances[tx.recipient] = balances.get(tx.recipient, 0) + tx.amount

        elif tx.type == "REDEEM":
            balances[tx.sender] = balances.get(tx.sender, 0) - tx.amount
            balances[self.BURN_ADDRESS] = balances.get(self.BURN_ADDRESS, 0) + tx.amount

            reward = self.rewards[tx.reward_id]
            voucher = {
                "voucher_code": f"HASH-{tx.reward_id}-{int(tx.timestamp)}-{tx.sender[:6].upper()}",
                "reward_id": tx.reward_id,
                "reward_name": reward["name"],
                "customer": tx.sender,
                "points_spent": tx.amount,
                "timestamp": tx.timestamp,
                "tx_id": tx.tx_id
            }
            vouchers.append(voucher)

        return state
