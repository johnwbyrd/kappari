#!/usr/bin/env python3
"""
Decrypt Paprika license data from SQLite database.
Based on reverse engineered GClass1.smethod_1() decryption algorithm.
"""

import base64
import sqlite3
import hashlib
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA1
import sys
import os
import json

def decrypt_paprika_data(encrypted_b64, password):
    """
    Decrypt Paprika encrypted data using AES-256-CBC + PBKDF2
    Based on GClass1.smethod_1() algorithm from decompiled code
    """
    try:
        # Decode base64
        encrypted_data = base64.b64decode(encrypted_b64)
        
        # First 32 bytes are the salt
        salt = encrypted_data[:32]
        ciphertext = encrypted_data[32:]
        
        # Use 1000 iterations as confirmed by debugging
        iterations = 1000
        
        # Derive key and IV using PBKDF2 (matches .NET Rfc2898DeriveBytes)
        key_iv = PBKDF2(password.encode('utf-8'), salt, 48, count=iterations, hmac_hash_module=SHA1)
        key = key_iv[:32]  # 256-bit AES key
        iv = key_iv[32:48]  # 128-bit IV
        
        # Decrypt with AES-256-CBC
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)
        
        # Remove PKCS7 padding
        padding_len = decrypted_padded[-1]
        if 1 <= padding_len <= 16:
            # Verify padding is correct
            padding_bytes = decrypted_padded[-padding_len:]
            if all(b == padding_len for b in padding_bytes):
                decrypted = decrypted_padded[:-padding_len]
                result = decrypted.decode('utf-8')
                return result
        
        return f"Decryption failed: Invalid padding"
        
    except Exception as e:
        return f"Decryption failed: {e}"

def main():
    db_path = "../database/Paprika.sqlite"
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get encrypted purchase data
    cursor.execute("SELECT product_id, data, signature FROM purchases")
    row = cursor.fetchone()
    
    if not row:
        print("No purchase data found in database")
        return
        
    product_id, encrypted_data, encrypted_signature = row
    print(f"Product ID: {product_id}")
    print(f"Encrypted data length: {len(encrypted_data)}")
    print(f"Encrypted signature length: {len(encrypted_signature)}")
    print()
    
    # Use the confirmed encryption keys from StringExtractor
    data_key = "Purchase Data"
    signature_key = "Purchase Signature"
    
    print(f"Using data encryption key: '{data_key}'")
    print(f"Using signature encryption key: '{signature_key}'")
    
    print("\nAttempting to decrypt license data...")
    result = decrypt_paprika_data(encrypted_data, data_key)
    if not result.startswith("Decryption failed"):
        print(f"Decrypted license data:")
        try:
            # Pretty print JSON if it's valid
            parsed = json.loads(result)
            print(json.dumps(parsed, indent=2))
            # Store for later use in authentication
            license_data_json = result
        except:
            print(result)
    else:
        print(f"FAILED to decrypt license data: {result}")
        return
        
    print("\nAttempting to decrypt signature...")  
    result = decrypt_paprika_data(encrypted_signature, signature_key)
    if not result.startswith("Decryption failed"):
        print(f"Success. Decrypted signature:")
        print(f"Signature length: {len(result)} characters")
        # Store for later use in authentication
        signature_data = base64.b64encode(result.encode('utf-8')).decode('utf-8')
        print("(Base64 encoded for transmission)")
    else:
        print(f"FAILED to decrypt signature: {result}")
        return
        
    conn.close()

if __name__ == "__main__":
    main()