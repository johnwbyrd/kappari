"""
Pytest configuration and shared fixtures for Kappari tests.

This module provides shared fixtures and configuration for conditional test
execution based on available environment variables and resources.
"""

from pathlib import Path

import pytest

from kappari.config import get_config


@pytest.fixture(scope="session")
def config():
    """Shared config fixture for all tests."""
    return get_config()


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers",
        "requires_credentials: test requires KAPPARI_EMAIL and "
        "KAPPARI_PASSWORD",
    )
    config.addinivalue_line(
        "markers",
        "requires_database: test requires Paprika database file to exist",
    )
    config.addinivalue_line(
        "markers", "requires_network: test makes actual network requests"
    )


@pytest.fixture
def _skip_if_no_credentials(config):
    """Skip test if credentials are not available."""
    if not config.validate_credentials():
        pytest.skip(
            "Skipping: No credentials found. "
            "Set KAPPARI_EMAIL and KAPPARI_PASSWORD in .env file."
        )


@pytest.fixture
def _skip_if_no_database(config):
    """Skip test if Paprika database file is not available."""
    if not Path(config.db_file).exists():
        pytest.skip(
            f"Skipping: No database found at {config.db_file}. "
            "Set KAPPARI_DB_FILE or place database at expected location."
        )


@pytest.fixture
def _skip_if_dry_run(config):
    """Skip test if in dry-run mode (test requires real network calls)."""
    if config.dry_run:
        pytest.skip(
            "Skipping: Test requires real network calls. "
            "Set KAPPARI_DRY_RUN=false in .env file to enable."
        )
