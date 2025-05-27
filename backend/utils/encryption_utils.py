from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
import json
from datetime import datetime
from backend.config.config import Config

class EncryptionUtils:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EncryptionUtils, cls).__new__(cls)
            cls._instance.key = cls._instance._get_or_create_key()
            cls._instance.cipher_suite = Fernet(cls._instance.key)
        return cls._instance

    def _get_or_create_key(self):
        """Get existing key or create a new one"""
        key_file = os.path.join(Config.BASE_DIR, 'instance', 'encryption.key')
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            key = self._generate_key()
            os.makedirs(os.path.dirname(key_file), exist_ok=True)
            with open(key_file, 'wb') as f:
                f.write(key)
            return key

    def _generate_key(self):
        salt = b'health_records_salt'  # Fixed salt for development
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(Config.ENCRYPTION_KEY.encode()))
        return key

    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data before storing"""
        try:
            encrypted = self.cipher_suite.encrypt(data.encode())
            return encrypted.decode()
        except Exception as e:
            print(f"Encryption error: {str(e)}")
            return data

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data when retrieving"""
        try:
            decrypted = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted.decode()
        except Exception as e:
            print(f"Decryption error: {str(e)}")
            return encrypted_data

    def encrypt_file(self, file_path: str, output_path: str):
        """Encrypt a file before storage"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            encrypted = self.cipher_suite.encrypt(data)
            with open(output_path, 'wb') as f:
                f.write(encrypted)
        except Exception as e:
            print(f"File encryption error: {str(e)}")

    def decrypt_file(self, encrypted_file: str, output_path: str):
        """Decrypt a file when retrieving"""
        try:
            with open(encrypted_file, 'rb') as f:
                encrypted = f.read()
            decrypted = self.cipher_suite.decrypt(encrypted)
            with open(output_path, 'wb') as f:
                f.write(decrypted)
        except Exception as e:
            print(f"File decryption error: {str(e)}")

    def generate_audit_log(self, action: str, user_id: int, record_id: int = None):
        """Generate audit log entry"""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "action": action,
                "record_id": record_id,
                "ip_address": "127.0.0.1"  # In production, get actual IP
            }
            return self.encrypt_data(json.dumps(log_entry))
        except Exception as e:
            print(f"Audit log error: {str(e)}")
            return None

_encryption_utils_instance = None

def get_encryption_utils():
    global _encryption_utils_instance
    if _encryption_utils_instance is None:
        _encryption_utils_instance = EncryptionUtils()
    return _encryption_utils_instance
