import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from ..config import settings

# AES-256 GCM Key (32 bytes). In production, this must be stored in AWS KMS / Docker Secrets.
# For now, derive it from a secure ENV variable.
SECRET_STR = os.getenv("DB_FIELD_KMS_KEY", "aviothic-kms-master-key-must-be-long-and-secure")
ENCRYPTION_KEY = base64.urlsafe_b64encode(SECRET_STR[:32].ljust(32, '0').encode())
ENCRYPTION_KEY = base64.urlsafe_bdecode(ENCRYPTION_KEY)

class HIPAAEncryptor:
    """AES-256 GCM authenticated encryption for Medical PII."""
    
    _aesgcm = AESGCM(ENCRYPTION_KEY)

    @classmethod
    def encrypt(cls, data: str) -> str:
        """Encrypts sensitive medical data (e.g. Patient Name, Report Content)."""
        if not data: return data
        nonce = os.urandom(12) # 12 bytes recommended for GCM
        ciphertext = cls._aesgcm.encrypt(nonce, data.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    @classmethod
    def decrypt(cls, encrypted_data: str) -> str:
        """Decrypts and authenticates ciphertext."""
        if not encrypted_data: return encrypted_data
        try:
            raw_data = base64.b64decode(encrypted_data)
            nonce = raw_data[:12]
            ciphertext = raw_data[12:]
            return cls._aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
        except Exception as e:
            # Audit failure to decrypt PII (possible tamper/key mismatch)
            return "[ENCRYPTION_PROTECTED_TAG]"

# Global Singleton
hp_encryptor = HIPAAEncryptor
