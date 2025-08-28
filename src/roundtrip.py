#!/usr/bin/env python3
"""
Round-trip encryption/decryption verification for Paprika license data.

This script validates that our implementation of Paprika's encryption algorithm
is correct by performing a complete round-trip test with real license data:

1. Read encrypted license data from the SQLite database
2. Decrypt it using our implementation
3. Re-encrypt the decrypted data
4. Compare the re-encrypted data with the original

If the re-encrypted data matches the original encrypted data byte-for-byte,
we know our implementation is correct. This is a stronger test than using
sample data because:

- It tests against Paprika's actual encryption output
- It validates both encryption and decryption in one test
- It catches any subtle implementation differences
- It works with real data that may have edge cases

The script will only run if a Paprika database is present. If no database
is found, it will exit with an appropriate message.

Technical Details:
- Encryption: AES-256-CBC with PBKDF2 key derivation
- Key derivation: PBKDF2-HMAC-SHA1 with 1000 iterations
- Salt: 32 bytes, prepended to ciphertext
- Padding: PKCS#7
- Output encoding: Base64
"""

import base64
import json
import sqlite3
import sys
import traceback
from pathlib import Path
from typing import Optional, Tuple

from Crypto.Cipher import AES
from Crypto.Hash import SHA1
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes

import log
from config import get_config


def encrypt_paprika_data(
    plaintext: str, password: str, salt: Optional[bytes] = None
) -> Tuple[str, bytes]:
    """
    Encrypt data using Paprika's encryption algorithm.

    This function implements the exact encryption algorithm used by Paprika:
    - AES-256-CBC encryption
    - PBKDF2-HMAC-SHA1 key derivation with 1000 iterations
    - 32-byte salt (random or provided)
    - PKCS#7 padding

    Args:
        plaintext: The data to encrypt (as string)
        password: The encryption password
        salt: Optional 32-byte salt (if None, generates random salt)

    Returns:
        Tuple of (Base64-encoded encrypted data, salt used)

    The encrypted data format is:
        [32 bytes salt][AES-256-CBC encrypted data with PKCS#7 padding]

    This entire byte sequence is then Base64-encoded for storage.
    """
    # Use provided salt or generate a random 32-byte salt
    if salt is None:
        salt = get_random_bytes(32)
    elif len(salt) != 32:
        raise ValueError(f"Salt must be exactly 32 bytes, got {len(salt)}")

    # Paprika uses exactly 1000 iterations with SHA-1
    iterations = 1000

    # Derive 48 bytes of key material using PBKDF2-HMAC-SHA1
    # This matches the .NET Rfc2898DeriveBytes implementation
    key_iv = PBKDF2(
        password.encode("utf-8"),
        salt,
        dkLen=48,  # Total bytes to derive
        count=iterations,
        hmac_hash_module=SHA1,
    )

    # Split the derived bytes:
    # - First 32 bytes: AES-256 key
    # - Next 16 bytes: AES CBC initialization vector
    key = key_iv[:32]
    iv = key_iv[32:48]

    # Convert plaintext to UTF-8 bytes for encryption
    plaintext_bytes = plaintext.encode("utf-8")

    # Apply PKCS#7 padding
    # Padding ensures data length is multiple of AES block size
    block_size = 16
    padding_length = block_size - (len(plaintext_bytes) % block_size)
    padding = bytes([padding_length] * padding_length)
    padded_plaintext = plaintext_bytes + padding

    # Encrypt with AES-256-CBC
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(padded_plaintext)

    # Prepend salt to ciphertext (Paprika's format)
    encrypted_data = salt + ciphertext

    # Base64 encode for storage
    encrypted_b64 = base64.b64encode(encrypted_data).decode("utf-8")

    return encrypted_b64, salt


def decrypt_paprika_data(
    encrypted_b64: str, password: str
) -> Tuple[str, bytes]:
    """
    Decrypt Paprika-encrypted data.

    This reverses the encryption process:
    1. Base64 decode
    2. Extract salt (first 32 bytes)
    3. Derive key and IV using PBKDF2
    4. Decrypt with AES-256-CBC
    5. Remove PKCS#7 padding

    Args:
        encrypted_b64: Base64-encoded encrypted data
        password: The decryption password

    Returns:
        Tuple of (decrypted plaintext, salt that was used)

    Raises:
        Exception: If decryption fails or padding is invalid
    """
    try:
        # Decode base64
        encrypted_data = base64.b64decode(encrypted_b64)

        # Extract salt (first 32 bytes) and ciphertext
        salt = encrypted_data[:32]
        ciphertext = encrypted_data[32:]

        # Use exactly 1000 iterations with SHA-1 (Paprika's parameters)
        iterations = 1000

        # Derive key and IV using PBKDF2 with same parameters as encryption
        key_iv = PBKDF2(
            password.encode("utf-8"),
            salt,
            dkLen=48,
            count=iterations,
            hmac_hash_module=SHA1,
        )
        key = key_iv[:32]  # AES-256 key
        iv = key_iv[32:48]  # AES CBC IV

        # Decrypt with AES-256-CBC
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_padded = cipher.decrypt(ciphertext)

        # Remove PKCS#7 padding
        # The last byte indicates the padding length
        padding_len = decrypted_padded[-1]

        # Validate padding (all padding bytes should equal padding_len)
        if 1 <= padding_len <= 16:
            padding_bytes = decrypted_padded[-padding_len:]
            if all(b == padding_len for b in padding_bytes):
                decrypted = decrypted_padded[:-padding_len]
                plaintext = decrypted.decode("utf-8")
                return plaintext, salt

        raise ValueError("Invalid PKCS#7 padding")

    except Exception as e:
        raise Exception(f"Decryption failed: {e}") from e


def read_encrypted_data_from_db(db_path: str) -> Tuple[str, str]:
    """
    Read encrypted license data and signature from Paprika's SQLite database.

    Args:
        db_path: Path to Paprika.sqlite database

    Returns:
        Tuple of (encrypted_data, encrypted_signature) as Base64 strings

    Raises:
        Exception: If database doesn't exist or has no purchase data
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT product_id, data, signature FROM purchases")
        row = cursor.fetchone()

        if not row:
            raise Exception("No purchase data found in database")

        product_id, encrypted_data, encrypted_signature = row
        log.info("Found purchase data for product: %s", product_id)

        return encrypted_data, encrypted_signature

    finally:
        conn.close()


def perform_round_trip_test():
    """
    Perform a complete round-trip test with real license data.

    This function:
    1. Reads encrypted data from the database
    2. Decrypts it
    3. Re-encrypts it using the same salt
    4. Compares the re-encrypted data with the original

    The test passes if the re-encrypted data exactly matches the original,
    proving our implementation is correct.
    """
    config = get_config()

    log.info("=" * 70)
    log.info("Paprika License Data Round-Trip Verification")
    log.info("=" * 70)

    # Step 1: Read encrypted data from database
    log.info("\nStep 1: Reading encrypted data from database...")
    log.info("Database path: %s", config.db_path)

    try:
        encrypted_data_original, encrypted_signature_original = (
            read_encrypted_data_from_db(config.db_path)
        )
        log.info("Successfully read encrypted data")
        log.info("  Data length: %d characters", len(encrypted_data_original))
        log.info(
            "  Signature length: %d characters",
            len(encrypted_signature_original),
        )
    except Exception as e:
        log.error("Failed to read database: %s", e)
        return False

    # Step 2: Decrypt the data
    log.info("\nStep 2: Decrypting license data...")

    try:
        decrypted_data, data_salt = decrypt_paprika_data(
            encrypted_data_original, config.purchase_data_key
        )
        log.info("Successfully decrypted license data")

        # Parse and display license info (partially redacted for privacy)
        license_json = json.loads(decrypted_data)
        log.info("  Product ID: %s", license_json.get("product_id", "N/A"))
        log.info("  Customer: %s", license_json.get("name", "N/A"))
        log.info(
            "  Email: %s***",
            license_json.get("email", "N/A")[:3]
            if license_json.get("email")
            else "N/A",
        )
        log.info(
            "  License: %s***",
            license_json.get("key", "N/A")[:5]
            if license_json.get("key")
            else "N/A",
        )

    except Exception as e:
        log.error("Failed to decrypt data: %s", e)
        return False

    log.info("\nStep 3: Decrypting signature...")

    try:
        decrypted_signature, sig_salt = decrypt_paprika_data(
            encrypted_signature_original, config.purchase_signature_key
        )
        log.info("Successfully decrypted signature")
        log.info(
            "  Signature preview: %s...",
            decrypted_signature[:30]
            if len(decrypted_signature) > 30
            else decrypted_signature,
        )

    except Exception as e:
        log.error("Failed to decrypt signature: %s", e)
        return False

    # Step 4: Re-encrypt the data using the same salt
    log.info("\nStep 4: Re-encrypting license data with original salt...")

    try:
        re_encrypted_data, _ = encrypt_paprika_data(
            decrypted_data,
            config.purchase_data_key,
            salt=data_salt,  # Use the same salt as original
        )
        log.info("Successfully re-encrypted license data")
        log.info(
            "  Re-encrypted length: %d characters", len(re_encrypted_data)
        )

    except Exception as e:
        log.error("Failed to re-encrypt data: %s", e)
        return False

    log.info("\nStep 5: Re-encrypting signature with original salt...")

    try:
        re_encrypted_signature, _ = encrypt_paprika_data(
            decrypted_signature,
            config.purchase_signature_key,
            salt=sig_salt,  # Use the same salt as original
        )
        log.info("Successfully re-encrypted signature")
        log.info(
            "  Re-encrypted length: %d characters", len(re_encrypted_signature)
        )

    except Exception as e:
        log.error("Failed to re-encrypt signature: %s", e)
        return False

    # Step 6: Compare original and re-encrypted data
    log.info("\nStep 6: Comparing original and re-encrypted data...")

    data_matches = encrypted_data_original == re_encrypted_data
    signature_matches = encrypted_signature_original == re_encrypted_signature

    if data_matches:
        log.info("License data: EXACT MATCH - Implementation is correct!")
    else:
        log.error("License data: MISMATCH - Implementation has errors")
        log.debug(
            "  Original first 50 chars: %s", encrypted_data_original[:50]
        )
        log.debug("  Re-encrypted first 50 chars: %s", re_encrypted_data[:50])

    if signature_matches:
        log.info("Signature: EXACT MATCH - Implementation is correct!")
    else:
        log.error("Signature: MISMATCH - Implementation has errors")
        log.debug(
            "  Original first 50 chars: %s", encrypted_signature_original[:50]
        )
        log.debug(
            "  Re-encrypted first 50 chars: %s", re_encrypted_signature[:50]
        )

    # Final summary
    log.info("\n" + "=" * 70)
    if data_matches and signature_matches:
        log.info("SUCCESS: Round-trip verification PASSED!")
        log.info("Our encryption implementation exactly matches Paprika's.")
    else:
        log.error("FAILURE: Round-trip verification FAILED!")
        log.error("Our implementation differs from Paprika's.")
    log.info("=" * 70)

    return data_matches and signature_matches


def main():
    """
    Main entry point for the round-trip verification script.

    This script requires a Paprika database to be present. If no database
    is found, it will exit with an informative message.
    """
    config = get_config()

    # Check if database exists
    if not Path(config.db_path).exists():
        log.info("=" * 70)
        log.info("No Paprika database found")
        log.info("=" * 70)
        log.info("\nThis script requires a Paprika database to verify the")
        log.info("encryption implementation against real data.")
        log.info("\nDatabase path checked: %s", config.db_path)
        log.info("\nTo use this script:")
        log.info(
            "1. Ensure Paprika 3 is installed and has been run at least once"
        )
        log.info(
            "2. Set KAPPARI_DB_PATH in your .env file to point to "
            "Paprika.sqlite"
        )
        log.info("3. Or copy a Paprika.sqlite file to the expected location")
        return 1

    # Run the round-trip test
    try:
        success = perform_round_trip_test()
        return 0 if success else 1
    except Exception as e:
        log.error("Unexpected error during round-trip test: %s", e)
        log.debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
