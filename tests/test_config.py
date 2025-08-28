"""
Tests for configuration loading and validation.

This module tests the Kappari configuration system, including environment
variable loading, path resolution, and credential validation.
"""

from pathlib import Path

import pytest

from kappari import log
from kappari.config import get_config, reload_config


@pytest.mark.requires_database
def test_configuration_loading():
    """Test that configuration loads successfully."""
    cfg = get_config()
    log.info("Configuration loaded successfully")
    log.info("Config: %s", cfg)

    if cfg.validate_credentials():
        log.info("Credentials are set")
    else:
        log.warning(
            "Missing credentials (KAPPARI_EMAIL and/or KAPPARI_PASSWORD)"
        )

    # Test passes regardless of database existence - that's tested separately
    if Path(cfg.db_file).exists():
        log.info("Database found at: %s", cfg.db_file)
    else:
        log.info("Database not found at: %s", cfg.db_file)


@pytest.mark.requires_database
def test_config_singleton():
    """Test that config singleton works properly."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2, "Config should be a singleton"


@pytest.mark.requires_database
def test_config_reload():
    """Test that config can be reloaded."""
    config1 = get_config()
    config2 = reload_config()
    # After reload, they should be different instances
    assert config1 is not config2, "Reload should create new instance"


@pytest.mark.requires_database
def test_config_has_required_attributes():
    """Test that config object has expected attributes."""
    config = get_config()

    # Test core attributes exist
    assert hasattr(config, "email")
    assert hasattr(config, "password")
    assert hasattr(config, "device_id")
    assert hasattr(config, "db_file")
    assert hasattr(config, "api_base_url")
    assert hasattr(config, "dry_run")

    # Test method exists
    assert hasattr(config, "validate_credentials")
    assert callable(config.validate_credentials)


@pytest.mark.requires_database
def test_path_resolution_attributes():
    """Test that all path attributes are properly set."""
    config = get_config()

    # Test directory attributes
    assert hasattr(config, "export_dir")
    assert hasattr(config, "import_dir")
    assert hasattr(config, "log_dir")
    assert hasattr(config, "cache_dir")
    assert hasattr(config, "photos_dir")
    assert hasattr(config, "recipes_local_dir")
    assert hasattr(config, "db_backup_dir")

    # All should be Path objects or strings

    assert isinstance(config.export_dir, Path)
    assert isinstance(config.import_dir, Path)
    assert isinstance(config.log_dir, Path)


@pytest.mark.requires_database
def test_boolean_parsing():
    """Test that boolean configuration values are parsed correctly."""
    config = get_config()

    # These should all be boolean values
    assert isinstance(config.dry_run, bool)
    assert isinstance(config.sync_enabled, bool)
    assert isinstance(config.cache_enabled, bool)
    assert isinstance(config.store_photos_locally, bool)
    assert isinstance(config.debug_api_requests, bool)
    assert isinstance(config.verify_ssl, bool)
