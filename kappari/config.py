#!/usr/bin/env python3
"""
Configuration Module
Loads configuration from environment variables with sensible defaults
"""

import os
import sqlite3
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from . import log

# Load .env file using default approach
load_dotenv()


class Config:
    """Configuration class for Paprika API client"""

    def __init__(self):
        self._setup_credentials()
        self._setup_root_directory()
        self._setup_database()
        self._setup_api_config()
        self._setup_license_auth()
        self._setup_sync_config()
        self._setup_paths()
        self._setup_logging()
        self._setup_network()
        self._setup_cache_and_storage()
        self._setup_development()

    def _setup_credentials(self):
        """Setup user credentials configuration."""
        self.email = os.getenv("KAPPARI_EMAIL")
        self.password = os.getenv("KAPPARI_PASSWORD")

        # If no email in env, we'll try to get it from database later
        self._try_load_email_from_db = not self.email

    def _get_platform_default_root(self) -> Optional[Path]:
        """Get platform-specific default Paprika installation directory."""
        if sys.platform == "win32":
            localappdata = os.environ.get("LOCALAPPDATA")
            if localappdata:
                return Path(localappdata) / "Paprika Recipe Manager 3"
        elif sys.platform == "darwin":
            return (
                Path.home()
                / "Library"
                / "Application Support"
                / "Paprika Recipe Manager 3"
            )
        # No default for Linux - user must specify
        return None

    def _setup_root_directory(self):
        """Setup root directory for Paprika installation."""

        root_env = os.getenv("KAPPARI_ROOT_DIR")

        if root_env:
            self.root_dir = Path(root_env).resolve()
            log.info("Using specified root directory: %s", self.root_dir)
        else:
            platform_default = self._get_platform_default_root()
            if platform_default and platform_default.exists():
                self.root_dir = platform_default
                log.info("Auto-detected platform default: %s", self.root_dir)
            else:
                self.root_dir = None
                log.info("No root directory set, using individual path config")

    def _resolve_path(
        self,
        env_key: str,
        default_relative_path: str,
        fallback_absolute: Optional[str] = None,
    ) -> Optional[str]:
        """
        Resolve path using root directory + override logic.

        Args:
            env_key: Environment variable name to check
            default_relative_path: Default path relative to root_dir
            fallback_absolute: Fallback when no root_dir available

        Returns:
            Resolved path as string, or None if cannot resolve
        """
        specific_path = os.getenv(env_key)

        if specific_path:
            if Path(specific_path).is_absolute():
                return specific_path  # Absolute override
            if self.root_dir:
                return str(self.root_dir / specific_path)  # Relative to root
            # No root dir but user provided relative path - problematic
            raise ValueError(
                f"{env_key} is relative but KAPPARI_ROOT_DIR not set"
            )
        if self.root_dir:
            return str(self.root_dir / default_relative_path)  # Default
        return fallback_absolute  # Fallback to old behavior

    def _setup_database(self):
        """Setup database configuration."""
        self.db_file = self._resolve_path(
            "KAPPARI_DB_FILE",
            "Database/Paprika.sqlite",
            self._find_default_db_path(),  # Fallback to old logic
        )
        self.db_backup_dir = self._resolve_path(
            "KAPPARI_DB_BACKUP_DIR", "Database/Backups", None
        )

        # Validate required fields
        if not self.db_file:
            raise ValueError(
                "Database file could not be determined. "
                "Set KAPPARI_ROOT_DIR or KAPPARI_DB_FILE in your .env file"
            )

        # Try to load email from database if not in env
        if self._try_load_email_from_db and Path(self.db_file).exists():
            self._load_email_from_database()

    def _setup_api_config(self):
        """Setup API configuration."""

        self.api_base_url = os.getenv(
            "KAPPARI_API_BASE_URL", "https://www.paprikaapp.com/api/v2"
        )
        self.user_agent = os.getenv(
            "KAPPARI_USER_AGENT",
            "Paprika Recipe Manager 3/3.3.1 "
            "(Microsoft Windows NT 10.0.26100.0)",
        )
        self.api_timeout = int(os.getenv("KAPPARI_API_TIMEOUT", "30"))

    def _setup_license_auth(self):
        """Setup license and authentication configuration."""

        self.device_id = os.getenv("KAPPARI_DEVICE_ID")
        self.jwt_token = os.getenv("KAPPARI_JWT_TOKEN")

        # Encryption keys
        self.purchase_data_key = os.getenv(
            "KAPPARI_PURCHASE_DATA_KEY", "Purchase Data"
        )
        self.purchase_signature_key = os.getenv(
            "KAPPARI_PURCHASE_SIGNATURE_KEY", "Purchase Signature"
        )

    def _setup_sync_config(self):
        """Setup sync configuration."""

        self.sync_enabled = self._parse_bool(
            os.getenv("KAPPARI_SYNC_ENABLED", "true")
        )
        self.sync_interval = int(os.getenv("KAPPARI_SYNC_INTERVAL", "15"))
        self.websocket_url = os.getenv(
            "KAPPARI_WEBSOCKET_URL", "wss://www.paprikaapp.com/ws/sync/"
        )

    def _setup_paths(self):
        """Setup export/import paths."""
        export_dir_str = self._resolve_path(
            "KAPPARI_EXPORT_DIR", "exports", "./exports"
        )
        import_dir_str = self._resolve_path(
            "KAPPARI_IMPORT_DIR", "imports", "./imports"
        )
        self.export_dir = Path(export_dir_str)
        self.import_dir = Path(import_dir_str)
        self.export_format = os.getenv("KAPPARI_EXPORT_FORMAT", "json")

        # Create directories if they don't exist
        self.export_dir.mkdir(parents=True, exist_ok=True)
        self.import_dir.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Setup logging configuration."""

        self.log_level = os.getenv("KAPPARI_LOG_LEVEL", "INFO")
        log_dir_str = self._resolve_path("KAPPARI_LOG_DIR", "Logs", "./logs")
        self.log_dir = Path(log_dir_str)
        self.debug_api_requests = self._parse_bool(
            os.getenv("KAPPARI_DEBUG_API_REQUESTS", "false")
        )
        self.debug_sql_queries = self._parse_bool(
            os.getenv("KAPPARI_DEBUG_SQL_QUERIES", "false")
        )
        self.pretty_json = self._parse_bool(
            os.getenv("KAPPARI_PRETTY_JSON", "true")
        )

        # Create log directory if it doesn't exist
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _setup_network(self):
        """Setup network configuration."""

        self.http_proxy = os.getenv("KAPPARI_HTTP_PROXY")
        self.https_proxy = os.getenv("KAPPARI_HTTPS_PROXY")
        self.verify_ssl = self._parse_bool(
            os.getenv("KAPPARI_VERIFY_SSL", "true")
        )

        # Build proxy dict for requests
        self.proxies = {}
        if self.http_proxy:
            self.proxies["http"] = self.http_proxy
        if self.https_proxy:
            self.proxies["https"] = self.https_proxy

    def _setup_cache_and_storage(self):
        """Setup cache and storage configuration."""

        # Cache settings
        self.cache_enabled = self._parse_bool(
            os.getenv("KAPPARI_CACHE_ENABLED", "true")
        )
        cache_dir_str = self._resolve_path(
            "KAPPARI_CACHE_DIR", "cache", "./cache"
        )
        self.cache_dir = Path(cache_dir_str)
        self.cache_ttl = int(os.getenv("KAPPARI_CACHE_TTL", "3600"))

        # Create cache directory if enabled
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Recipe storage
        recipes_dir_str = self._resolve_path(
            "KAPPARI_RECIPES_LOCAL_DIR", "recipes", "./recipes"
        )
        self.recipes_local_dir = Path(recipes_dir_str)
        self.store_photos_locally = self._parse_bool(
            os.getenv("KAPPARI_STORE_PHOTOS_LOCALLY", "true")
        )
        photos_dir_str = self._resolve_path(
            "KAPPARI_PHOTOS_DIR", "Photos", "./photos"
        )
        self.photos_dir = Path(photos_dir_str)

        # Create recipe and photo directories
        self.recipes_local_dir.mkdir(parents=True, exist_ok=True)
        if self.store_photos_locally:
            self.photos_dir.mkdir(parents=True, exist_ok=True)

    def _setup_development(self):
        """Setup development and testing configuration."""

        self.dry_run = self._parse_bool(os.getenv("KAPPARI_DRY_RUN", "false"))
        self.use_mock_data = self._parse_bool(
            os.getenv("KAPPARI_USE_MOCK_DATA", "false")
        )
        self.mock_data_dir = Path(
            os.getenv("KAPPARI_MOCK_DATA_DIR", "./test/mock_data")
        )
        self.persist_tokens = self._parse_bool(
            os.getenv("KAPPARI_PERSIST_TOKENS", "false")
        )

        if self.use_mock_data:
            self.mock_data_dir.mkdir(parents=True, exist_ok=True)

    def _parse_bool(self, value: str) -> bool:
        """Parse boolean from string"""
        return value.lower() in ("true", "yes", "1", "on")

    def _load_email_from_database(self):
        """Try to load email from Paprika database settings."""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value FROM settings WHERE name = 'SyncEmail'"
            )
            row = cursor.fetchone()
            if row and row[0]:
                # Remove quotes if present
                email = row[0].strip('"')
                self.email = email
                log.info("Loaded email from database: %s", email)
            conn.close()
        except Exception as e:
            log.debug("Could not load email from database: %s", e)

    def _find_default_db_path(self) -> Optional[str]:
        """Try to find the default Paprika database path based on OS"""
        home = Path.home()

        # Check Windows paths
        if sys.platform == "win32":
            appdata = os.environ.get("APPDATA")
            if appdata:
                win_path = (
                    Path(appdata)
                    / "Paprika Recipe Manager 3"
                    / "Paprika.sqlite"
                )
                if win_path.exists():
                    return str(win_path)

        # Check macOS path
        elif sys.platform == "darwin":
            mac_path = (
                home
                / "Library"
                / "Application Support"
                / "Paprika Recipe Manager 3"
                / "Paprika.sqlite"
            )
            if mac_path.exists():
                return str(mac_path)

        # Check Linux path (might be in .config or .local/share)
        elif sys.platform.startswith("linux"):
            # Try common Linux paths
            paths_to_check = [
                home
                / ".config"
                / "Paprika Recipe Manager 3"
                / "Paprika.sqlite",
                home
                / ".local"
                / "share"
                / "Paprika Recipe Manager 3"
                / "Paprika.sqlite",
            ]
            for linux_path in paths_to_check:
                if linux_path.exists():
                    return str(linux_path)

        # Check if there's a local database in the captures directory
        local_test_db = (
            Path(__file__).parent.parent / "database" / "Paprika.sqlite"
        )
        if local_test_db.exists():
            return str(local_test_db)

        return None

    def validate_credentials(self) -> bool:
        """Check if we have the minimum required credentials"""
        return not (not self.email or not self.password)

    def get_request_headers(self) -> dict:
        """Get headers for API requests"""
        headers = {
            "User-Agent": self.user_agent,
        }

        if self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"

        return headers

    def update_jwt_token(self, token: str):
        """Update JWT token in memory and optionally save to .env file"""
        self.jwt_token = token

        # Optionally write back to .env file if configured to persist tokens
        if self.persist_tokens:
            self._update_env_file("KAPPARI_JWT_TOKEN", token)

    def _update_env_file(self, key: str, value: str):
        """Update a value in the .env file"""
        env_file = Path(__file__).parent.parent / ".env"
        if not env_file.exists():
            return

        lines = env_file.read_text().splitlines()
        updated = False

        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}"
                updated = True
                break

        if not updated:
            lines.append(f"{key}={value}")

        env_file.write_text("\n".join(lines) + "\n")

    def __repr__(self) -> str:
        """String representation of config"""
        return (
            f"Config(\n"
            f"  email={self.email if self.email else 'NOT SET'},\n"
            f"  db_file={self.db_file},\n"
            f"  api_base_url={self.api_base_url},\n"
            f"  sync_enabled={self.sync_enabled},\n"
            f"  cache_enabled={self.cache_enabled},\n"
            f"  dry_run={self.dry_run}\n"
            f")"
        )


# Module-level singleton
class _ConfigSingleton:
    """Config singleton holder."""

    _instance: Optional[Config] = None

    @classmethod
    def get_instance(cls) -> Config:
        """Get the singleton config instance."""
        if cls._instance is None:
            cls._instance = Config()
        return cls._instance

    @classmethod
    def reload_instance(cls) -> Config:
        """Reload configuration from environment."""
        cls._instance = Config()
        return cls._instance


# Convenience functions for common operations
def get_config() -> Config:
    """Get the singleton config instance"""
    return _ConfigSingleton.get_instance()


def reload_config() -> Config:
    """Reload configuration from environment"""
    return _ConfigSingleton.reload_instance()
