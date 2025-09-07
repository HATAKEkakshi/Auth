from pydantic import BaseModel, Field
from typing import Optional
from auth.security.encryption import EncryptionService

class EncryptedUser(BaseModel):
    """Encrypted user model for database storage"""
    id: str
    first_name_encrypted: str
    last_name_encrypted: str
    email_encrypted: str  # Regular encryption for decryption
    email_search_hash: str  # Deterministic encryption for searching
    phone_encrypted: str
    country_code: str  # Not encrypted - used for filtering
    country: str  # Not encrypted - used for filtering
    password: str  # Already hashed
    is_email_verified: bool = False
    
    @classmethod
    def from_plain_user(cls, user_data: dict, user_id: str):
        """Create encrypted user from plain user data"""
        email = user_data.get("email", "")
        return cls(
            id=user_id,
            first_name_encrypted=EncryptionService.encrypt_data(user_data.get("first_name", "")),
            last_name_encrypted=EncryptionService.encrypt_data(user_data.get("last_name", "")),
            email_encrypted=EncryptionService.encrypt_data(email),
            email_search_hash=EncryptionService.encrypt_email(email),
            phone_encrypted=EncryptionService.encrypt_data(user_data.get("phone", "")),
            country_code=user_data.get("country_code", ""),
            country=user_data.get("country", ""),
            password=user_data.get("password", ""),
            is_email_verified=user_data.get("is_email_verified", False)
        )
    
    def to_plain_user(self) -> dict:
        """Convert encrypted user to plain user data"""
        return {
            "id": self.id,
            "first_name": EncryptionService.decrypt_data(self.first_name_encrypted),
            "last_name": EncryptionService.decrypt_data(self.last_name_encrypted),
            "email": EncryptionService.decrypt_data(self.email_encrypted),
            "phone": EncryptionService.decrypt_data(self.phone_encrypted),
            "country_code": self.country_code,
            "country": self.country,
            "password": self.password,
            "is_email_verified": self.is_email_verified
        }
    

    
    def to_dict(self) -> dict:
        """Convert to dictionary for MongoDB storage"""
        return {
            "id": self.id,
            "first_name_encrypted": self.first_name_encrypted,
            "last_name_encrypted": self.last_name_encrypted,
            "email_encrypted": self.email_encrypted,
            "email_search_hash": self.email_search_hash,
            "phone_encrypted": self.phone_encrypted,
            "country_code": self.country_code,
            "country": self.country,
            "password": self.password,
            "is_email_verified": self.is_email_verified
        }