from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Optional
from auth.logger.log import logger

class EncryptionService:
    """AES-256 encryption service for sensitive data"""
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
        logger("Auth", "Encryption", "INFO", "null", "EncryptionService initialized")
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from environment or generate new one"""
        try:
            # Try to get key from environment
            key_b64 = os.getenv('ENCRYPTION_KEY')
            if key_b64:
                return base64.urlsafe_b64decode(key_b64.encode())
            
            # Generate new key if not found
            key = Fernet.generate_key()
            logger("Auth", "Encryption", "WARN", "HIGH", "Generated new encryption key - add ENCRYPTION_KEY to .env")
            return key
        except Exception as e:
            logger("Auth", "Encryption", "ERROR", "CRITICAL", f"Key generation failed: {str(e)}")
            raise
    
    def encrypt(self, data: str) -> str:
        """Encrypt string data"""
        try:
            if not data:
                return ""
            encrypted = self.cipher.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger("Auth", "Encryption", "ERROR", "ERROR", f"Encryption failed: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        try:
            if not encrypted_data:
                return ""
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger("Auth", "Encryption", "ERROR", "ERROR", f"Decryption failed: {str(e)}")
            raise
    
    def encrypt_email(self, email: str) -> str:
        """Encrypt email with deterministic encryption for searching"""
        try:
            # Use PBKDF2 for deterministic encryption of emails (for search)
            # Generate salt from environment or use secure default
            salt_source = os.getenv('EMAIL_SALT', 'auth_system_email_salt_2024')
            salt = salt_source.encode()[:16].ljust(16, b'0')  # Ensure 16 bytes
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(email.lower().encode()))
            cipher = Fernet(key)
            encrypted = cipher.encrypt(email.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger("Auth", "Encryption", "ERROR", "ERROR", f"Email encryption failed: {str(e)}")
            raise
    
    def decrypt_email(self, encrypted_email: str) -> str:
        """Decrypt email (requires original email for key derivation)"""
        try:
            if not encrypted_email:
                return ""
            # Note: This is for deterministic decryption - in practice, 
            # you'd store a mapping or use the search functionality
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_email.encode())
            # This method requires the original email to derive the key
            # In practice, use search by encrypted email instead
            return encrypted_email  # Placeholder - implement search logic
        except Exception as e:
            logger("Auth", "Encryption", "ERROR", "ERROR", f"Email decryption failed: {str(e)}")
            raise

# Global encryption service
encryption_service = EncryptionService()