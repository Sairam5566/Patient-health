from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import json
from datetime import datetime

class EncryptionUtils:
    def __init__(self):
        self.key = self._generate_key()
        self.cipher_suite = Fernet(self.key)

    def _generate_key(self):
        # Generate a secure key using PBKDF2
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(b"health_records_key"))
        return key

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data before storing"""
        encrypted = self.cipher_suite.encrypt(data.encode())
        return encrypted.decode()

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data when retrieving"""
        decrypted = self.cipher_suite.decrypt(encrypted_data.encode())
        return decrypted.decode()

    def encrypt_file(self, file_path: str, output_path: str):
        """Encrypt a file before storage"""
        with open(file_path, 'rb') as f:
            data = f.read()
        encrypted = self.cipher_suite.encrypt(data)
        with open(output_path, 'wb') as f:
            f.write(encrypted)

    def decrypt_file(self, encrypted_file: str, output_path: str):
        """Decrypt a file when retrieving"""
        with open(encrypted_file, 'rb') as f:
            encrypted = f.read()
        decrypted = self.cipher_suite.decrypt(encrypted)
        with open(output_path, 'wb') as f:
            f.write(decrypted)

    def generate_audit_log(self, action: str, user_id: int, record_id: int = None):
        """Generate audit log entry"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "action": action,
            "record_id": record_id,
            "ip_address": "127.0.0.1"  # In production, get actual IP
        }
        return self.encrypt_data(json.dumps(log_entry))

def get_encryption_utils():
    return EncryptionUtils()
