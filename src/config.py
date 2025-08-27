#!/usr/bin/env python3
"""
Configuration Module
Loads configuration from environment variables with sensible defaults
"""

import os
import sys
from pathlib import Path
from typing import Optional, Union
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


class Config:
    """Configuration class for Paprika API client"""
    
    def __init__(self):
        # ===========================================
        # USER CREDENTIALS
        # ===========================================
        self.email = os.getenv('KAPPARI_EMAIL')
        self.password = os.getenv('KAPPARI_PASSWORD')
        
        # ===========================================
        # DATABASE CONFIGURATION
        # ===========================================
        self.db_path = os.getenv('KAPPARI_DB_PATH')
        self.db_backup_path = os.getenv('KAPPARI_DB_BACKUP_PATH')
        
        # Validate required fields
        if not self.db_path:
            # Try to find default paths
            self.db_path = self._find_default_db_path()
            if not self.db_path:
                raise ValueError("KAPPARI_DB_PATH is required. Please set it in your .env file")
        
        # ===========================================
        # API CONFIGURATION
        # ===========================================
        self.api_base_url = os.getenv(
            'KAPPARI_API_BASE_URL', 
            'https://www.paprikaapp.com/api/v2'
        )
        self.user_agent = os.getenv(
            'KAPPARI_USER_AGENT',
            'Paprika Recipe Manager 3/3.3.1 (Microsoft Windows NT 10.0.26100.0)'
        )
        self.api_timeout = int(os.getenv('KAPPARI_API_TIMEOUT', '30'))
        
        # ===========================================
        # LICENSE & AUTHENTICATION
        # ===========================================
        self.device_id = os.getenv('KAPPARI_DEVICE_ID')
        self.jwt_token = os.getenv('KAPPARI_JWT_TOKEN')
        self.license_key = os.getenv('KAPPARI_LICENSE_KEY')
        self.license_signature = os.getenv('KAPPARI_LICENSE_SIGNATURE')
        
        # ===========================================
        # ENCRYPTION KEYS
        # ===========================================
        self.purchase_data_key = os.getenv(
            'KAPPARI_PURCHASE_DATA_KEY',
            'Purchase Data'
        )
        self.purchase_signature_key = os.getenv(
            'KAPPARI_PURCHASE_SIGNATURE_KEY',
            'Purchase Signature'
        )
        
        # ===========================================
        # SYNC CONFIGURATION
        # ===========================================
        self.sync_enabled = self._parse_bool(
            os.getenv('KAPPARI_SYNC_ENABLED', 'true')
        )
        self.sync_interval = int(os.getenv('KAPPARI_SYNC_INTERVAL', '15'))
        self.websocket_url = os.getenv(
            'KAPPARI_WEBSOCKET_URL',
            'wss://www.paprikaapp.com/ws/sync/'
        )
        
        # ===========================================
        # EXPORT/IMPORT PATHS
        # ===========================================
        self.export_path = Path(os.getenv('KAPPARI_EXPORT_PATH', './exports'))
        self.import_path = Path(os.getenv('KAPPARI_IMPORT_PATH', './imports'))
        self.export_format = os.getenv('KAPPARI_EXPORT_FORMAT', 'json')
        
        # Create directories if they don't exist
        self.export_path.mkdir(parents=True, exist_ok=True)
        self.import_path.mkdir(parents=True, exist_ok=True)
        
        # ===========================================
        # LOGGING & DEBUG
        # ===========================================
        self.log_level = os.getenv('KAPPARI_LOG_LEVEL', 'INFO')
        self.log_path = Path(os.getenv('KAPPARI_LOG_PATH', './logs'))
        self.debug_api_requests = self._parse_bool(
            os.getenv('KAPPARI_DEBUG_API_REQUESTS', 'false')
        )
        self.debug_sql_queries = self._parse_bool(
            os.getenv('KAPPARI_DEBUG_SQL_QUERIES', 'false')
        )
        self.pretty_json = self._parse_bool(
            os.getenv('KAPPARI_PRETTY_JSON', 'true')
        )
        
        # Create log directory if it doesn't exist
        self.log_path.mkdir(parents=True, exist_ok=True)
        
        # ===========================================
        # NETWORK CONFIGURATION
        # ===========================================
        self.http_proxy = os.getenv('KAPPARI_HTTP_PROXY')
        self.https_proxy = os.getenv('KAPPARI_HTTPS_PROXY')
        self.verify_ssl = self._parse_bool(
            os.getenv('KAPPARI_VERIFY_SSL', 'true')
        )
        
        # Build proxy dict for requests
        self.proxies = {}
        if self.http_proxy:
            self.proxies['http'] = self.http_proxy
        if self.https_proxy:
            self.proxies['https'] = self.https_proxy
        
        # ===========================================
        # CAPTURE FILES
        # ===========================================
        self.capture_saz_path = Path(os.getenv('KAPPARI_CAPTURE_SAZ_PATH', './captures'))
        self.capture_raw_path = Path(os.getenv('KAPPARI_CAPTURE_RAW_PATH', './captures/raw'))
        
        # ===========================================
        # CACHE SETTINGS
        # ===========================================
        self.cache_enabled = self._parse_bool(
            os.getenv('KAPPARI_CACHE_ENABLED', 'true')
        )
        self.cache_path = Path(os.getenv('KAPPARI_CACHE_PATH', './cache'))
        self.cache_ttl = int(os.getenv('KAPPARI_CACHE_TTL', '3600'))
        
        # Create cache directory if enabled
        if self.cache_enabled:
            self.cache_path.mkdir(parents=True, exist_ok=True)
        
        # ===========================================
        # RECIPE STORAGE
        # ===========================================
        self.recipes_local_path = Path(os.getenv('KAPPARI_RECIPES_LOCAL_PATH', './recipes'))
        self.store_photos_locally = self._parse_bool(
            os.getenv('KAPPARI_STORE_PHOTOS_LOCALLY', 'true')
        )
        self.photos_path = Path(os.getenv('KAPPARI_PHOTOS_PATH', './photos'))
        
        # Create recipe and photo directories
        self.recipes_local_path.mkdir(parents=True, exist_ok=True)
        if self.store_photos_locally:
            self.photos_path.mkdir(parents=True, exist_ok=True)
        
        # ===========================================
        # DEVELOPMENT/TESTING
        # ===========================================
        self.dry_run = self._parse_bool(
            os.getenv('KAPPARI_DRY_RUN', 'false')
        )
        self.use_mock_data = self._parse_bool(
            os.getenv('KAPPARI_USE_MOCK_DATA', 'false')
        )
        self.mock_data_path = Path(os.getenv('KAPPARI_MOCK_DATA_PATH', './test/mock_data'))
        
        if self.use_mock_data:
            self.mock_data_path.mkdir(parents=True, exist_ok=True)
    
    def _parse_bool(self, value: str) -> bool:
        """Parse boolean from string"""
        return value.lower() in ('true', 'yes', '1', 'on')
    
    def _find_default_db_path(self) -> Optional[str]:
        """Try to find the default Paprika database path based on OS"""
        home = Path.home()
        
        # Check Windows paths
        if sys.platform == 'win32':
            appdata = os.environ.get('APPDATA')
            if appdata:
                win_path = Path(appdata) / 'Paprika Recipe Manager 3' / 'Paprika.sqlite'
                if win_path.exists():
                    return str(win_path)
        
        # Check macOS path
        elif sys.platform == 'darwin':
            mac_path = home / 'Library' / 'Application Support' / 'Paprika Recipe Manager 3' / 'Paprika.sqlite'
            if mac_path.exists():
                return str(mac_path)
        
        # Check Linux path (might be in .config or .local/share)
        elif sys.platform.startswith('linux'):
            # Try common Linux paths
            paths_to_check = [
                home / '.config' / 'Paprika Recipe Manager 3' / 'Paprika.sqlite',
                home / '.local' / 'share' / 'Paprika Recipe Manager 3' / 'Paprika.sqlite',
            ]
            for linux_path in paths_to_check:
                if linux_path.exists():
                    return str(linux_path)
        
        # Check if there's a local database in the captures directory (for testing)
        local_test_db = Path(__file__).parent.parent / 'database' / 'Paprika.sqlite'
        if local_test_db.exists():
            return str(local_test_db)
        
        return None
    
    def validate_credentials(self) -> bool:
        """Check if we have the minimum required credentials"""
        if not self.email or not self.password:
            return False
        return True
    
    def get_request_headers(self) -> dict:
        """Get headers for API requests"""
        headers = {
            'User-Agent': self.user_agent,
        }
        
        if self.jwt_token:
            headers['Authorization'] = f'Bearer {self.jwt_token}'
        
        return headers
    
    def update_jwt_token(self, token: str):
        """Update JWT token in memory and optionally save to .env file"""
        self.jwt_token = token
        
        # Optionally write back to .env file
        # This is commented out by default to avoid modifying user's .env
        # Uncomment if you want to persist tokens
        # self._update_env_file('KAPPARI_JWT_TOKEN', token)
    
    def _update_env_file(self, key: str, value: str):
        """Update a value in the .env file"""
        env_file = Path(__file__).parent.parent / '.env'
        if not env_file.exists():
            return
        
        lines = env_file.read_text().splitlines()
        updated = False
        
        for i, line in enumerate(lines):
            if line.startswith(f'{key}='):
                lines[i] = f'{key}={value}'
                updated = True
                break
        
        if not updated:
            lines.append(f'{key}={value}')
        
        env_file.write_text('\n'.join(lines) + '\n')
    
    def __repr__(self) -> str:
        """String representation of config"""
        return (
            f"Config(\n"
            f"  email={self.email if self.email else 'NOT SET'},\n"
            f"  db_path={self.db_path},\n"
            f"  api_base_url={self.api_base_url},\n"
            f"  sync_enabled={self.sync_enabled},\n"
            f"  cache_enabled={self.cache_enabled},\n"
            f"  dry_run={self.dry_run}\n"
            f")"
        )


# Create a singleton instance
config = Config()


# Convenience functions for common operations
def get_config() -> Config:
    """Get the singleton config instance"""
    return config


def reload_config() -> Config:
    """Reload configuration from environment"""
    global config
    config = Config()
    return config


if __name__ == "__main__":
    # Test configuration loading
    try:
        cfg = get_config()
        print("Configuration loaded successfully")
        print("-" * 50)
        print(cfg)
        print("-" * 50)
        
        if cfg.validate_credentials():
            print("✓ Credentials are set")
        else:
            print("✗ Missing credentials (KAPPARI_EMAIL and/or KAPPARI_PASSWORD)")
        
        if Path(cfg.db_path).exists():
            print(f"✓ Database found at: {cfg.db_path}")
        else:
            print(f"✗ Database not found at: {cfg.db_path}")
        
    except Exception as e:
        print(f"Configuration Error: {e}")
        sys.exit(1)