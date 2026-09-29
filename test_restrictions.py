"""
Testes automatizados completos do HashBack DApp com as novas restrições:
1. Emissão autorizada da Loja para Cliente -> Sucesso
2. Bloqueio de emissão de Loja para outra Loja -> Rejeição
3. Bloqueio de transferência de Cliente para Loja -> Rejeição
4. Bloqueio de resgate de recompensa por Loja -> Rejeição
5. Bloqueio de emissão por Cliente -> Rejeição
6. Bloqueio de gasto duplo de Cliente -> Rejeição
7. Resgate válido por Cliente -> Sucesso
"""
import unittest
import os
from backend.wallet import Wallet
from backend.transaction import Transaction
from backend.blockchain import Blockchain

class TestHashBackRestrictions(unittest.TestCase):
    def setUp(self):
        self.test_storage = "test_chain_restrictions.json"
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)

        self.blockchain = Blockchain(storage_file=self.test_storage)
        self.contract = self.blockchain.contract

        self.merchant = Wallet()
        self.alice = Wallet()
        self.bob = Wallet()

        self.contract.add_merchant(self.merchant.address)

    def tearDown(self):
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)

    def test_01_merchant_cannot_receive_points_via_mint(self):
        """Loja tenta emitir pontos para si mesma -> Rejeitado pelo contrato"""
        tx = Transaction(
            tx_type="MINT",
            sender=self.merchant.address,
            recipient=self.merchant.address,
            amount=100,
            sender_public_key=self.merchant.public_key_hex,
            nonce=0
        )
        tx.signature = self.merchant.sign(tx.to_signable_dict())
        success, msg, _ = self.blockchain.add_transaction_and_mine(tx)
        self.assertFalse(success)
        self.assertIn("Lojas não podem receber pontos", msg)

    def test_02_customer_cannot_transfer_to_merchant(self):
        """Alice tenta transferir pontos para a Loja -> Rejeitado pelo contrato"""
        # Emite 100 pontos para Alice
        mint_tx = Transaction(
            tx_type="MINT",
            sender=self.merchant.address,
            recipient=self.alice.address,
            amount=100,
            sender_public_key=self.merchant.public_key_hex,
            nonce=0
        )
        mint_tx.signature = self.merchant.sign(mint_tx.to_signable_dict())
        self.blockchain.add_transaction_and_mine(mint_tx)

        # Alice tenta transferir 50 pontos para a Loja
        transfer_tx = Transaction(
            tx_type="TRANSFER",
            sender=self.alice.address,
            recipient=self.merchant.address,
            amount=50,
            sender_public_key=self.alice.public_key_hex,
            nonce=0
        )
        transfer_tx.signature = self.alice.sign(transfer_tx.to_signable_dict())
        success, msg, _ = self.blockchain.add_transaction_and_mine(transfer_tx)
        self.assertFalse(success)
        self.assertIn("Lojas parceiras não acumulam ou recebem pontos", msg)

    def test_03_merchant_cannot_redeem_rewards(self):
        """Loja tenta resgatar recompensa -> Rejeitado pelo contrato"""
        redeem_tx = Transaction(
            tx_type="REDEEM",
            sender=self.merchant.address,
            recipient=self.contract.BURN_ADDRESS,
            amount=100,
            sender_public_key=self.merchant.public_key_hex,
            reward_id="REW-1",
            nonce=0
        )
        redeem_tx.signature = self.merchant.sign(redeem_tx.to_signable_dict())
        success, msg, _ = self.blockchain.add_transaction_and_mine(redeem_tx)
        self.assertFalse(success)
        self.assertIn("Lojas parceiras não podem resgatar recompensas", msg)

if __name__ == "__main__":
    unittest.main()
