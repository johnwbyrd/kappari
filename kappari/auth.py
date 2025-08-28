#!/usr/bin/env python3
"""
Authentication implementation
"""

import base64
import json
import sqlite3
from pathlib import Path

from Crypto.Cipher import AES
from Crypto.Hash import SHA1
from Crypto.Protocol.KDF import PBKDF2

from . import log
from .config import get_config
from .network_client import get_client


class Auth:
    def __init__(self):
        self.config = get_config()
        self.client = get_client()
        self.license_data = None
        self.signature = None

    def decrypt_license_data(self):
        """Decrypt license data from SQLite database"""
        log.debug("Starting license data decryption")

        if not Path(self.config.db_file).exists():
            log.error("Database not found: %s", self.config.db_file)
            raise Exception(f"Database not found: {self.config.db_file}")

        log.debug("Connecting to database: %s", self.config.db_file)
        conn = sqlite3.connect(self.config.db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT product_id, data, signature FROM purchases")
        row = cursor.fetchone()

        if not row:
            log.error("No purchase data found in database")
            raise Exception("No purchase data found in database")

        product_id, encrypted_data, encrypted_signature = row
        log.debug("Found purchase data for product: %s", product_id)

        self.license_data = self._decrypt_data(
            encrypted_data, self.config.purchase_data_key
        )
        if self.license_data.startswith("Decryption failed"):
            log.error("Failed to decrypt license data: %s", self.license_data)
            raise Exception(
                f"Failed to decrypt license data: {self.license_data}"
            )

        signature_raw = self._decrypt_data(
            encrypted_signature, self.config.purchase_signature_key
        )
        if signature_raw.startswith("Decryption failed"):
            log.error("Failed to decrypt signature: %s", signature_raw)
            raise Exception(f"Failed to decrypt signature: {signature_raw}")

        # Check if the decrypted signature is already Base64 encoded
        try:
            # Try to decode it to see if it's already Base64
            base64.b64decode(signature_raw)
            self.signature = signature_raw  # Already Base64 encoded
            log.debug("Signature is already Base64 encoded")
        except Exception:
            # If it's not Base64, encode it
            self.signature = base64.b64encode(
                signature_raw.encode("utf-8")
            ).decode("utf-8")
            log.debug("Signature was not Base64 encoded, encoded it")
        log.debug("License data and signature decrypted successfully")

        conn.close()
        return True

    def _decrypt_data(self, encrypted_b64, password):
        """Decrypt encrypted data"""
        try:
            # Decode base64
            encrypted_data = base64.b64decode(encrypted_b64)

            # First 32 bytes are the salt
            salt = encrypted_data[:32]
            ciphertext = encrypted_data[32:]

            # Use 1000 iterations
            iterations = 1000

            # Derive key and IV using PBKDF2
            key_iv = PBKDF2(
                password.encode("utf-8"),
                salt,
                48,
                count=iterations,
                hmac_hash_module=SHA1,
            )
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
                    return decrypted.decode("utf-8")

            return "Decryption failed: Invalid padding"

        except Exception as e:
            return f"Decryption failed: {e}"

    def authenticate(self, email, password):
        """Authenticate with server and get JWT token"""
        if not self.license_data or not self.signature:
            raise Exception(
                "License data not decrypted. "
                "Call decrypt_license_data() first."
            )

        # The license data needs to be sent as JSON
        try:
            license_json = json.loads(self.license_data)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid license data JSON: {e}") from e

        log.info("Attempting to authenticate with email: %s", email)
        log.debug("License key: %s", license_json.get("key", "N/A"))
        log.debug("Product ID: %s", license_json.get("product_id", "N/A"))

        # Use the network client for authentication
        jwt_token = self.client.authenticate(
            email, password, self.license_data, self.signature
        )

        if jwt_token:
            log.debug(
                "JWT Token received: %s",
                jwt_token[:20] + "..." if len(jwt_token) > 20 else jwt_token,
            )

        return jwt_token

    def make_authenticated_request(self, endpoint, jwt_token):
        """Make an authenticated request to API"""
        return self.client.make_authenticated_request(endpoint, jwt_token)
