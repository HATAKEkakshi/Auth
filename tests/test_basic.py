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


def test_id_generator():
    """Test secure ID generation"""
    from auth.helper.utils import id_generator
    
    id1 = id_generator()
    id2 = id_generator()
    assert len(id1) == 7
    assert len(id2) == 7
    assert id1 != id2  # Should be unique


def test_password_hashing():
    """Test password hashing"""
    from auth.helper.utils import password_hash, password_context
    
    password = "TestPassword123!"
    hashed = password_hash(password)
    assert password_context.verify(password, hashed)
    assert not password_context.verify("wrong", hashed)


def test_country_from_dial_code():
    """Test country resolution from dial code"""
    from auth.helper.utils import get_country_from_dial_code
    
    country = get_country_from_dial_code("+1")
    assert "United States" in country or "Canada" in country
    
    country = get_country_from_dial_code("+91")
    assert "India" in country


def test_input_sanitization():
    """Test input sanitization"""
    from auth.middleware.security import sanitize_input
    
    clean = sanitize_input("normal text")
    assert clean == "normal text"
    
    malicious = sanitize_input("<script>alert('xss')</script>")
    assert "<script>" not in malicious


def test_jwt_token_generation():
    """Test JWT token generation and decoding"""
    from auth.helper.utils import generate_access_token, decode_access_token
    
    data = {"id": "test123", "email": "test@example.com"}
    token = generate_access_token(data)
    decoded = decode_access_token(token)
    
    assert decoded["id"] == "test123"
    assert decoded["email"] == "test@example.com"
    assert "jti" in decoded
    assert "exp" in decoded