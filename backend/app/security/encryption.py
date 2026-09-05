from cryptography.fernet import Fernet
from backend.app.config import settings
import base64
import hashlib

class TokenEncryption:
    def __init__(self, secret_key: str):
        # Derive a 32-byte key from the secret_key for Fernet
        key = base64.urlsafe_b64encode(hashlib.sha256(secret_key.encode()).digest())
        self.fernet = Fernet(key)

    def encrypt(self, token: str) -> str:
        return self.fernet.encrypt(token.encode()).decode()

    def decrypt(self, encrypted_token: str) -> str:
        return self.fernet.decrypt(encrypted_token.encode()).decode()

token_encryption = TokenEncryption(settings.SECRET_KEY)
