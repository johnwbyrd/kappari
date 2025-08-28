"""
Tests for authentication functionality.

This module tests the Kappari authentication system including license
decryption and API authentication. Tests require valid credentials and
database.
"""

import json
import warnings

import pytest

from kappari.auth import Auth


@pytest.mark.requires_credentials
@pytest.mark.requires_database
def test_full_authentication_flow(
    _skip_if_no_credentials, _skip_if_no_database
):
    """Test complete authentication flow with real credentials and database."""
    auth = Auth()

    # Decrypt license data
    auth.decrypt_license_data()

    # Parse license data to verify it's valid

    license_json = json.loads(auth.license_data)

    # Should have expected fields
    assert "key" in license_json
    assert "email" in license_json
    assert "product_id" in license_json

    # Authenticate with server
    jwt_token = auth.authenticate(auth.config.email, auth.config.password)

    if auth.config.dry_run:
        # In dry-run mode, should return None (no actual network call)
        assert jwt_token is None, "Dry-run mode should return None"
        warnings.warn(
            "Authentication test passed in dry-run mode - "
            "no real network call made",
            UserWarning,
            stacklevel=2
        )
    else:
        # In live mode, should return actual JWT token
        assert jwt_token is not None, "Live mode authentication should succeed"
        assert isinstance(jwt_token, str)

        # Test authenticated API request only in live mode
        response = auth.make_authenticated_request("sync/recipes/", jwt_token)

        if response is not None:
            assert response.status_code == 200, (
                f"API request failed with status {response.status_code}"
            )

            # Verify response is valid JSON
            response_data = response.json()
            assert isinstance(response_data, dict)


def test_auth_class_creation():
    """Test that Auth class can be instantiated."""
    auth = Auth()
    assert auth is not None
    assert hasattr(auth, "config")
    assert hasattr(auth, "client")


def test_auth_class_methods():
    """Test that Auth class has expected methods."""
    auth = Auth()

    assert hasattr(auth, "decrypt_license_data")
    assert callable(auth.decrypt_license_data)

    assert hasattr(auth, "authenticate")
    assert callable(auth.authenticate)

    assert hasattr(auth, "make_authenticated_request")
    assert callable(auth.make_authenticated_request)


@pytest.mark.requires_database
def test_license_decryption(_skip_if_no_database):
    """Test that license data can be decrypted from database."""
    auth = Auth()

    # This should not raise an exception
    auth.decrypt_license_data()

    # License data should be populated
    assert auth.license_data is not None
    assert auth.signature is not None

    # License data should be valid JSON

    license_json = json.loads(auth.license_data)
    assert isinstance(license_json, dict)

    # Should have expected fields
    assert "key" in license_json
    assert "email" in license_json
    assert "product_id" in license_json
