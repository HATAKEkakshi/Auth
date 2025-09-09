"""Basic tests for the authentication system"""
import pytest
from auth.security.encryption import EncryptionService


def test_encryption_service():
    """Test basic encryption functionality"""
    test_data = "test@example.com"
    encrypted = EncryptionService.encrypt_data(test_data)
    decrypted = EncryptionService.decrypt_data(encrypted)
    assert decrypted == test_data


def test_email_encryption():
    """Test deterministic email encryption"""
    email = "test@example.com"
    hash1 = EncryptionService.encrypt_email(email)
    hash2 = EncryptionService.encrypt_email(email)
    assert hash1 == hash2  # Should be deterministic


def test_password_validation():
    """Test password strength validation"""
    from auth.middleware.security import validate_password_strength
    
    assert validate_password_strength("Password@123") == True
    assert validate_password_strength("weak") == False
    assert validate_password_strength("NoSpecial123") == False


def test_email_validation():
    """Test email format validation"""
    from auth.middleware.security import validate_email
    
    assert validate_email("test@example.com") == True
    assert validate_email("invalid-email") == False
    assert validate_email("test@") == False