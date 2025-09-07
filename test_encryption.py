#!/usr/bin/env python3
"""Test encryption functionality"""

import os
import sys
sys.path.append('.')

from auth.security.encryption import EncryptionService

def test_encryption():
    try:
        # Test basic encryption
        test_data = "test@example.com"
        print(f"Original: {test_data}")
        
        encrypted = EncryptionService.encrypt_data(test_data)
        print(f"Encrypted: {encrypted}")
        
        decrypted = EncryptionService.decrypt_data(encrypted)
        print(f"Decrypted: {decrypted}")
        
        print(f"Match: {test_data == decrypted}")
        
        # Test email encryption
        email_encrypted = EncryptionService.encrypt_email(test_data)
        print(f"Email encrypted: {email_encrypted}")
        
        print("✅ Encryption test passed!")
        
    except Exception as e:
        print(f"❌ Encryption test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_encryption()