"""
Tests for network client functionality.

This module tests the Kappari network client. When not in dry-run mode, it
makes real HTTP requests to test actual network functionality through the
auth flow.
"""

import json
import warnings

import pytest

from kappari.auth import Auth
from kappari.network_client import get_client


@pytest.mark.requires_database
def test_network_client_singleton():
    """Test that get_client returns the same instance."""
    client1 = get_client()
    client2 = get_client()
    assert client1 is client2, "Network client should be a singleton"


@pytest.mark.requires_database
def test_network_client_configuration():
    """Test that network client has expected configuration."""
    client = get_client()

    # Test that client has required attributes
    assert hasattr(client, "config")
    assert hasattr(client, "post")
    assert hasattr(client, "get")
    assert hasattr(client, "authenticate")

    # Test config attributes
    assert client.config.api_base_url.startswith("http")
    assert isinstance(client.config.api_timeout, int)
    assert isinstance(client.config.dry_run, bool)


@pytest.mark.requires_database
def test_request_methods_exist():
    """Test that all expected request methods exist."""
    client = get_client()

    # Test that methods are callable
    assert callable(client.post)
    assert callable(client.get)
    assert callable(client.authenticate)
    assert callable(client.make_authenticated_request)


@pytest.mark.requires_network
@pytest.mark.requires_credentials
@pytest.mark.requires_database
def test_real_network_authentication(
    _skip_if_no_credentials, _skip_if_no_database
):
    """Test real network functionality through complete authentication flow."""
    # Create auth instance which uses the network client
    auth = Auth()

    # Decrypt license data (requires database)
    auth.decrypt_license_data()
    assert auth.license_data is not None
    assert auth.signature is not None

    # Verify license data is valid JSON
    license_json = json.loads(auth.license_data)
    assert isinstance(license_json, dict)

    # Attempt authentication (behavior depends on dry-run mode)
    jwt_token = auth.authenticate(auth.config.email, auth.config.password)

    if auth.config.dry_run:
        # In dry-run mode, should return None (no actual network call)
        assert jwt_token is None, "Dry-run mode should return None"
        warnings.warn(
            "Network test passed in dry-run mode - no real HTTP requests made",
            UserWarning,
            stacklevel=2,
        )
    else:
        # In live mode, should return actual JWT token
        assert jwt_token is not None, (
            "Live mode authentication should succeed with valid credentials"
        )
        assert isinstance(jwt_token, str)
        assert len(jwt_token) > 50, "JWT token should be substantial length"

        # Test authenticated API request only in live mode
        response = auth.make_authenticated_request("sync/recipes/", jwt_token)
        assert response is not None, (
            "Authenticated request should return response"
        )
        assert response.status_code == 200, (
            f"API request should succeed, got {response.status_code}"
        )

        # Verify response is valid JSON
        response_data = response.json()
        assert isinstance(response_data, dict), (
            "Response should be JSON object"
        )
