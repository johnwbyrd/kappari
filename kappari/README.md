# Kappari: Python Library

Python implementation of the Paprika 3 protocols documented in the parent directory.

## Module Structure

- **`auth.py`** - Main authentication class and license decryption
- **`network_client.py`** - HTTP client with multipart form handling  
- **`config.py`** - Environment-based configuration management
- **`roundtrip.py`** - Crypto implementation verification functions
- **`log.py`** - Simple logging interface with file rotation
- **`__init__.py`** - Clean public API exports

## Public API

```python
from kappari import Auth, get_config, get_client, decrypt_paprika_data

# Basic usage
auth = Auth()
auth.decrypt_license_data()
jwt_token = auth.authenticate(email, password)

# Direct functions
config = get_config()
client = get_client()
plaintext, salt = decrypt_paprika_data(encrypted_data, password)
```

## Configuration

Uses `.env` file with `KAPPARI_*` environment variables. See `.env.example` for complete documentation.

Required variables:
- `KAPPARI_EMAIL` and `KAPPARI_PASSWORD` - your Paprika account
- `KAPPARI_DEVICE_ID` - UUID from licensed device  
- `KAPPARI_DB_FILE` or `KAPPARI_ROOT_DIR` - database location