"""
Testes automatizados para validar todas as regras do Contrato Inteligente do HashBack:
1. Emissão autorizada por Loja Parceira
2. Bloqueio de emissão por usuário não autorizado
3. Transferência legítima de pontos
4. Bloqueio de Gasto Duplo (saldo insuficiente)
5. Resgate de Recompensa (geração de voucher e queima de tokens)
6. Integridade Criptográfica da Blockchain
"""
import unittest
import os
from backend.wallet import Wallet
from backend.transaction import Transaction
from backend.contract import HashBackContract
from backend.blockchain import Blockchain

class TestHashBackDApp(unittest.TestCase):
    def setUp(self):
        # Utiliza arquivo de testes limpo
        self.test_storage = "test_chain.json"
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)

        self.blockchain = Blockchain(storage_file=self.test_storage)
        self.contract = self.blockchain.contract

        # Carteiras de teste
        self.merchant_wallet = Wallet()
        self.alice_wallet = Wallet()
        self.bob_wallet = Wallet()

        # Autoriza apenas a loja no contrato
        self.contract.add_merchant(self.merchant_wallet.address)

    def tearDown(self):
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)

    def test_01_authorized_mint(self):
        """Loja autorizada emite 200 pontos para Alice -> Sucesso"""
        tx = Transaction(
            tx_type="MINT",
            sender=self.merchant_wallet.address,
            recipient=self.alice_wallet.address,
            amount=200,
            sender_public_key=self.merchant_wallet.public_key_hex,
            nonce=0
        )
        tx.signature = self.merchant_wallet.sign(tx.to_signable_dict())
        success, msg, block = self.blockchain.add_transaction_and_mine(tx)

        self.assertTrue(success, f"Falha na emissão: {msg}")
        self.assertEqual(self.blockchain.state["balances"][self.alice_wallet.address], 200)
        self.assertEqual(len(self.blockchain.chain), 2) # Genesis + Bloco #1

    def test_02_unauthorized_mint_rejection(self):
        """Alice (cliente) tenta emitir pontos para si mesma -> Rejeição pelo Contrato"""
        tx = Transaction(
            tx_type="MINT",
            sender=self.alice_wallet.address,
            recipient=self.alice_wallet.address,
            amount=500,
            sender_public_key=self.alice_wallet.public_key_hex,
            nonce=0
        )
        tx.signature = self.alice_wallet.sign(tx.to_signable_dict())
        success, msg, block = self.blockchain.add_transaction_and_mine(tx)

        self.assertFalse(success)
        self.assertIn("Apenas lojas parceiras autorizadas", msg)
        self.assertEqual(len(self.blockchain.chain), 1) # Apenas gênesis

    def test_03_double_spending_prevention(self):
        """Alice recebe 100 pontos e tenta transferir 150 para Bob -> Rejeição por gasto duplo"""
        # 1. Emissão de 100 pontos para Alice
        mint_tx = Transaction(
            tx_type="MINT",
            sender=self.merchant_wallet.address,
            recipient=self.alice_wallet.address,
            amount=100,
            sender_public_key=self.merchant_wallet.public_key_hex,
            nonce=0
        )
        mint_tx.signature = self.merchant_wallet.sign(mint_tx.to_signable_dict())
        self.blockchain.add_transaction_and_mine(mint_tx)

        # 2. Alice tenta transferir 150 pontos (tendo apenas 100)
        transfer_tx = Transaction(
            tx_type="TRANSFER",
            sender=self.alice_wallet.address,
            recipient=self.bob_wallet.address,
            amount=150,
            sender_public_key=self.alice_wallet.public_key_hex,
            nonce=0
        )
        transfer_tx.signature = self.alice_wallet.sign(transfer_tx.to_signable_dict())
        success, msg, block = self.blockchain.add_transaction_and_mine(transfer_tx)

        self.assertFalse(success)
        self.assertIn("Tentativa de gasto duplo ou saldo insuficiente", msg)
        self.assertEqual(self.blockchain.state["balances"][self.alice_wallet.address], 100)

    def test_04_reward_redemption_and_voucher(self):
        """Alice resgata Cupom de R$ 20 (custa 100 pontos) -> Saldo debitado e voucher gerado"""
        # Emite 150 pontos para Alice
        mint_tx = Transaction(
            tx_type="MINT",
            sender=self.merchant_wallet.address,
            recipient=self.alice_wallet.address,
            amount=150,
            sender_public_key=self.merchant_wallet.public_key_hex,
            nonce=0
        )
        mint_tx.signature = self.merchant_wallet.sign(mint_tx.to_signable_dict())
        self.blockchain.add_transaction_and_mine(mint_tx)

        # Alice resgata 'REW-1' (Cupom de R$ 20 OFF, 100 pontos)
        redeem_tx = Transaction(
            tx_type="REDEEM",
            sender=self.alice_wallet.address,
            recipient=self.contract.BURN_ADDRESS,
            amount=100,
            sender_public_key=self.alice_wallet.public_key_hex,
            reward_id="REW-1",
            nonce=0
        )
        redeem_tx.signature = self.alice_wallet.sign(redeem_tx.to_signable_dict())
        success, msg, block = self.blockchain.add_transaction_and_mine(redeem_tx)

        self.assertTrue(success, f"Falha no resgate: {msg}")
        self.assertEqual(self.blockchain.state["balances"][self.alice_wallet.address], 50)
        self.assertEqual(len(self.blockchain.state["vouchers"]), 1)
        self.assertEqual(self.blockchain.state["vouchers"][0]["reward_id"], "REW-1")

    def test_05_chain_integrity(self):
        """Verifica a integridade criptográfica da cadeia com múltiplos blocos"""
        mint_tx = Transaction(
            tx_type="MINT",
            sender=self.merchant_wallet.address,
            recipient=self.alice_wallet.address,
            amount=100,
            sender_public_key=self.merchant_wallet.public_key_hex,
            nonce=0
        )
        mint_tx.signature = self.merchant_wallet.sign(mint_tx.to_signable_dict())
        self.blockchain.add_transaction_and_mine(mint_tx)

        is_valid, msg = self.blockchain.is_chain_valid()
        self.assertTrue(is_valid)
        self.assertIn("100% válida", msg)

if __name__ == "__main__":
    unittest.main()
