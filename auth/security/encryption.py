from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Optional
from auth.logger.log import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EncryptionService:
    """AES-256 encryption service for sensitive data"""
    
    _key = None
    _cipher = None
    
    @classmethod
    def reset(cls):
        """Reset cached key and cipher"""
        cls._key = None
        cls._cipher = None
    
    @classmethod
    def _get_or_create_key(cls) -> bytes:
        """Get encryption key from environment or generate new one"""
        try:
            # Try to get key from environment
            key_b64 = os.getenv('ENCRYPTION_KEY')
            if key_b64:
                # Return the key as bytes for Fernet (it expects base64 string)
                return key_b64.encode()
            
            # Generate new key if not found
            key = Fernet.generate_key()
            logger("Auth", "Encryption", "WARN", "HIGH", "Generated new encryption key - add ENCRYPTION_KEY to .env")
            return key
        except Exception as e:
            logger("Auth", "Encryption", "ERROR", "CRITICAL", f"Key generation failed: {str(e)}")
            raise
    
    @classmethod
    def _get_cipher(cls):
        """Get or create cipher instance"""
        if cls._cipher is None:
            cls._key = cls._get_or_create_key()
            # Fernet expects the key as string, not bytes
            key_str = cls._key.decode() if isinstance(cls._key, bytes) else cls._key
            cls._cipher = Fernet(key_str)
            logger("Auth", "Encryption", "INFO", "null", "EncryptionService initialized")
        return cls._cipher
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """Encrypt string data"""
        try:
            if not data:
                return ""
            cipher = EncryptionService._get_cipher()
            encrypted = cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger("Auth", "Encryption", "ERROR", "CRITICAL", f"Encryption failed: {str(e)}")
            raise
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            if not encrypted_data:
                return ""
            cipher = EncryptionService._get_cipher()
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger("Auth", "Encryption", "ERROR", "CRITICAL", f"Decryption failed: {str(e)}")
            raise
    
    @staticmethod
    def encrypt_email(email: str) -> str:
        """Encrypt email with deterministic encryption for searching"""
        try:
            # Use simple hash for deterministic email encryption (for search only)
            salt_source = os.getenv('EMAIL_SALT', 'auth_system_email_salt_2024')
            salt = salt_source.encode()
            
            # Create deterministic hash using PBKDF2
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            # Use email as input for deterministic result
            email_hash = kdf.derive(email.lower().encode())
            return base64.urlsafe_b64encode(email_hash).decode()
        except Exception as e:
            logger("Auth", "Encryption", "ERROR", "CRITICAL", f"Email encryption failed: {str(e)}")
            raise

# Global encryption service instance
encryption_service = EncryptionService()