#!/usr/bin/env python3
"""
Demonstration of Paprika 3 encryption/decryption as described in crypto.md

This script demonstrates the complete encryption and decryption process
using the same algorithms and parameters described in the documentation.
"""

import base64
import hashlib
import os
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA1
from Crypto.Random import get_random_bytes

def encrypt_paprika_data(plaintext, password):
    """
    Encrypt data using Paprika 3's encryption algorithm
    
    Args:
        plaintext (str): The data to encrypt
        password (str): The encryption password
    
    Returns:
        str: Base64-encoded encrypted data (salt + ciphertext)
    """
    # Generate a random 32-byte salt
    salt = get_random_bytes(32)
    
    # Use exactly 1000 iterations with SHA-1 as specified
    iterations = 1000
    
    # Derive 48 bytes of key material using PBKDF2
    key_iv = PBKDF2(password.encode('utf-8'), salt, 48, count=iterations, hmac_hash_module=SHA1)
    key = key_iv[:32]  # First 32 bytes for AES-256 key
    iv = key_iv[32:48]  # Next 16 bytes for AES-IV
    
    # Convert plaintext to UTF-8 bytes
    plaintext_bytes = plaintext.encode('utf-8')
    
    # Apply PKCS#7 padding
    block_size = 16  # AES block size
    padding_length = block_size - (len(plaintext_bytes) % block_size)
    padding = bytes([padding_length] * padding_length)
    padded_plaintext = plaintext_bytes + padding
    
    # Encrypt with AES-256-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(padded_plaintext)
    
    # Prepend salt to ciphertext and Base64 encode
    encrypted_data = salt + ciphertext
    return base64.b64encode(encrypted_data).decode('utf-8')

def decrypt_paprika_data(encrypted_b64, password):
    """
    Decrypt data using Paprika 3's decryption algorithm
    
    Args:
        encrypted_b64 (str): Base64-encoded encrypted data
        password (str): The decryption password
    
    Returns:
        str: The decrypted plaintext
    """
    # Decode base64
    encrypted_data = base64.b64decode(encrypted_b64)
    
    # Extract salt (first 32 bytes) and ciphertext
    salt = encrypted_data[:32]
    ciphertext = encrypted_data[32:]
    
    # Use exactly 1000 iterations with SHA-1 as specified
    iterations = 1000
    
    # Derive key and IV using the same parameters
    key_iv = PBKDF2(password.encode('utf-8'), salt, 48, count=iterations, hmac_hash_module=SHA1)
    key = key_iv[:32]  # First 32 bytes for AES-256 key
    iv = key_iv[32:48]  # Next 16 bytes for AES-IV
    
    # Decrypt with AES-256-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_padded = cipher.decrypt(ciphertext)
    
    # Remove PKCS#7 padding
    padding_length = decrypted_padded[-1]
    decrypted = decrypted_padded[:-padding_length]
    
    # Convert back to string
    return decrypted.decode('utf-8')

def main():
    print("Paprika 3 Encryption/Decryption Demonstration")
    print("=" * 45)
    
    # Example license data
    license_data = '{"key":"LICENSE-KEY-HERE","name":"USER NAME HERE","email":"user@example.com","product_id":"com.hindsightlabs.paprika.windows.v3","purchase_date":"2025-07-14 20:09:31","disabled":false,"refunded":false,"install_uid":"device-identifier-here","algorithm":1}'
    
    # Example signature (in real Paprika apps, this RSA signature is stored encrypted in the local SQLite database)
# The signature is retrieved from the 'signature' column in the 'purchases' table of Paprika.sqlite
signature_data = "EXAMPLE_SIGNATURE_DATA_FOR_DEMONSTRATION_ONLY_NOT_A_REAL_SIGNATURE"
    
    # Encryption keys as documented
    data_key = "Purchase Data"
    signature_key = "Purchase Signature"
    
    print("\n1. Encrypting license data...")
    encrypted_license = encrypt_paprika_data(license_data, data_key)
    print(f"   Encrypted license length: {len(encrypted_license)} characters")
    
    print("\n2. Encrypting signature...")
    encrypted_signature = encrypt_paprika_data(signature_data, signature_key)
    print(f"   Encrypted signature length: {len(encrypted_signature)} characters")
    
    print("\n3. Decrypting license data...")
    decrypted_license = decrypt_paprika_data(encrypted_license, data_key)
    print(f"   Decryption successful: {decrypted_license == license_data}")
    
    print("\n4. Decrypting signature...")
    decrypted_signature = decrypt_paprika_data(encrypted_signature, signature_key)
    print(f"   Decryption successful: {decrypted_signature == signature_data}")
    
    print("\n5. Verifying decrypted license data...")
    if decrypted_license == license_data:
        print("   ✓ License data matches original")
        # Show a snippet of the decrypted data
        print(f"   Sample: {decrypted_license[:50]}...")
    else:
        print("   ✗ License data does not match original")
    
    print("   PASS: License data matches original")
        
    print("\n6. Verifying decrypted signature...")
    if decrypted_signature == signature_data:
        print("   PASS: Signature matches original")
        print(f"   Sample: {decrypted_signature[:30]}...")
    else:
        print("   FAIL: Signature does not match original")

if __name__ == "__main__":
    main()