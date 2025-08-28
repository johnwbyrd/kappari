"""
Tests for encryption round-trip verification.

This module tests the Kappari encryption implementation by performing
round-trip verification against real Paprika database license data.
"""

import pytest

from kappari.roundtrip import (
    decrypt_paprika_data,
    encrypt_paprika_data,
    perform_round_trip_test,
)


@pytest.mark.requires_database
def test_encryption_roundtrip_verification(_skip_if_no_database):
    """Test encryption round-trip verification with real database."""

    # Run the actual round-trip test against real database
    success = perform_round_trip_test()
    assert success, "Encryption round-trip verification failed"


def test_encrypt_decrypt_functions_exist():
    """Test that encryption/decryption functions are available."""
    assert callable(encrypt_paprika_data)
    assert callable(decrypt_paprika_data)


def test_encrypt_decrypt_with_sample_data():
    """Test encryption/decryption with sample data."""
    # Test data
    plaintext = "test data for encryption"
    password = "test password"

    # Encrypt
    encrypted_b64, salt = encrypt_paprika_data(plaintext, password)

    # Verify encryption produces expected format
    assert isinstance(encrypted_b64, str)
    assert isinstance(salt, bytes)
    assert len(salt) == 32  # Should be 32-byte salt

    # Decrypt
    decrypted_text, extracted_salt = decrypt_paprika_data(
        encrypted_b64, password
    )

    # Verify round-trip
    assert decrypted_text == plaintext
    assert extracted_salt == salt


def test_encrypt_with_custom_salt():
    """Test encryption with provided salt produces consistent results."""
    plaintext = "test data"
    password = "test password"
    custom_salt = b"0" * 32  # 32 bytes of zeros

    # Encrypt twice with same salt
    encrypted1, salt1 = encrypt_paprika_data(plaintext, password, custom_salt)
    encrypted2, salt2 = encrypt_paprika_data(plaintext, password, custom_salt)

    # Should produce identical results with same salt
    assert encrypted1 == encrypted2
    assert salt1 == salt2 == custom_salt


def test_decrypt_invalid_data():
    """Test that decrypting invalid data raises appropriate errors."""
    with pytest.raises((ValueError, Exception)):
        decrypt_paprika_data("invalid_base64_data", "password")

    with pytest.raises((ValueError, Exception)):
        decrypt_paprika_data("", "password")


def test_salt_length_validation():
    """Test that encrypt_paprika_data validates salt length."""
    with pytest.raises(ValueError, match="Salt must be exactly 32 bytes"):
        encrypt_paprika_data("test", "password", b"short_salt")
