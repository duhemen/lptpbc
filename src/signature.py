# src/signature.py
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization


class DigitalSignature:
    def __init__(self, key_dir="src/data/keys"):
        self.key_dir = key_dir
        os.makedirs(key_dir, exist_ok=True)
        self.private_key_path = os.path.join(key_dir, "private.pem")
        self.public_key_path = os.path.join(key_dir, "public.pem")
        self._load_or_create_keys()
    
    def _load_or_create_keys(self):
        if os.path.exists(self.private_key_path):
            with open(self.private_key_path, 'rb') as f:
                self.private_key = serialization.load_pem_private_key(f.read(), password=None)
            with open(self.public_key_path, 'rb') as f:
                self.public_key = serialization.load_pem_public_key(f.read())
        else:
            self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
            self.public_key = self.private_key.public_key()
            with open(self.private_key_path, 'wb') as f:
                f.write(self.private_key.private_bytes(encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()))
            with open(self.public_key_path, 'wb') as f:
                f.write(self.public_key.public_bytes(encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo))
    
    def sign(self, data: str) -> str:
        signature = self.private_key.sign(data.encode(),
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256())
        return base64.b64encode(signature).decode()
    
    def verify(self, data: str, signature: str) -> bool:
        try:
            self.public_key.verify(base64.b64decode(signature), data.encode(),
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256())
            return True
        except:
            return False