"""
Kappari - Paprika Recipe Manager API library.

This library provides tools for interacting with Paprika Recipe Manager 3's
REST API and local SQLite database through clean-room reverse engineering.

Main functionality:
- Configuration management with environment variable support
- Authentication with license decryption and JWT tokens
- Encryption/decryption utilities for license data
- Network client for API requests with dry-run support
- Logging utilities

Example usage:
    from kappari import get_config, Auth, encrypt_paprika_data

    config = get_config()
    auth = Auth()
    encrypted = encrypt_paprika_data("data", "password")
"""

__version__ = "0.1.0"

# Configuration management
# Authentication and license handling
from .auth import Auth
from .config import Config, get_config, reload_config

# Network client
from .network_client import NetworkClient, get_client

# Encryption utilities
from .roundtrip import (
    decrypt_paprika_data,
    encrypt_paprika_data,
    perform_round_trip_test,
    read_encrypted_data_from_db,
)

__all__ = [
    "Auth",
    "Config",
    "NetworkClient",
    "decrypt_paprika_data",
    "encrypt_paprika_data",
    "get_client",
    "get_config",
    "perform_round_trip_test",
    "read_encrypted_data_from_db",
    "reload_config",
]
