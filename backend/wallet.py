import hashlib
import json
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization

class Wallet:
    def __init__(self, private_key=None):
        if private_key is None:
            self._private_key = ec.generate_private_key(ec.SECP256K1())
        else:
            self._private_key = private_key
        self._public_key = self._private_key.public_key()

    @property
    def private_key_hex(self) -> str:
        private_bytes = self._private_key.private_numbers().private_value.to_bytes(32, byteorder="big")
        return private_bytes.hex()

    @property
    def public_key_hex(self) -> str:
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.X962,
            format=serialization.PublicFormat.CompressedPoint
        )
        return public_bytes.hex()

    @property
    def address(self) -> str:
        # Endereço derivado de SHA-256 da chave pública comprimida (prefixado com 0x e primeiros 40 chars hex)
        digest = hashlib.sha256(bytes.fromhex(self.public_key_hex)).hexdigest()
        return "0x" + digest[:40]

    def sign(self, message_dict: dict) -> str:
        serialized = json.dumps(message_dict, sort_keys=True).encode('utf-8')
        signature = self._private_key.sign(
            serialized,
            ec.ECDSA(hashes.SHA256())
        )
        return signature.hex()

    @staticmethod
    def verify(public_key_hex: str, message_dict: dict, signature_hex: str) -> bool:
        try:
            pub_bytes = bytes.fromhex(public_key_hex)
            public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), pub_bytes)
            signature = bytes.fromhex(signature_hex)
            serialized = json.dumps(message_dict, sort_keys=True).encode('utf-8')
            public_key.verify(signature, serialized, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False

    @staticmethod
    def get_address_from_public_key(public_key_hex: str) -> str:
        digest = hashlib.sha256(bytes.fromhex(public_key_hex)).hexdigest()
        return "0x" + digest[:40]

    @classmethod
    def from_private_key_hex(cls, hex_str: str):
        int_val = int(hex_str, 16)
        priv_key = ec.derive_private_key(int_val, ec.SECP256K1())
        return cls(private_key=priv_key)
