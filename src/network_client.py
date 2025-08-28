#!/usr/bin/env python3
"""
Network client for Paprika API.

Handles all HTTP requests with dry run support and proper logging.
"""

import json
import sys
import uuid
from typing import Any, Dict, Optional

import log
from config import get_config

# Try to import requests and requests-toolbelt, but handle if not available
try:
    import requests

    kappari_requests_available = True
except ImportError:
    kappari_requests_available = False
    log.warning("requests library not available. Network features disabled.")


class NetworkClient:
    """HTTP client for Paprika API with dry run support."""

    def __init__(self):
        self.config = get_config()

    def _log_prepared_request(self, prepared):
        """Log the prepared request from requests library."""
        log.debug("=== PREPARED REQUEST ===")
        log.debug("Method: %s", prepared.method)
        log.debug("URL: %s", prepared.url)
        log.debug("Headers: %s", dict(prepared.headers))
        if prepared.body:
            body = prepared.body
            if isinstance(body, bytes):
                try:
                    body = body.decode("utf-8")
                except UnicodeDecodeError:
                    body = f"<{len(prepared.body)} bytes>"
            log.debug("Body: %s", body)
        log.debug("=== END PREPARED REQUEST ===")

    def _log_request(
        self, method: str, url: str, headers: dict, data: Any = None
    ) -> None:
        """Log request details."""
        log.debug("--- %s Request ---", method.upper())
        log.debug("URL: %s", url)
        log.debug("Headers:")
        for key, value in headers.items():
            # Hide sensitive auth tokens in logs
            if key.lower() == "authorization" and len(value) > 20:
                log.debug("  %s: %s...", key, value[:20])
            else:
                log.debug("  %s: %s", key, value)

        if data:
            if isinstance(data, dict):
                log.debug("Form Data:")
                for key, value in data.items():
                    if isinstance(value, tuple) and len(value) == 2:
                        # Multipart form data format (filename, content)
                        filename, content = value
                        if key in ["password", "signature"]:
                            log.debug(
                                "  %s: [HIDDEN - %d chars]",
                                key,
                                len(str(content)),
                            )
                        else:
                            log.debug("  %s: %s", key, content)
                    elif key in ["password", "signature"]:
                        log.debug("  %s: [HIDDEN]", key)
                    else:
                        log.debug("  %s: %s", key, value)
            else:
                log.debug("Data: %s", data)

    def _log_response(self, response) -> None:
        """Log response details."""
        if response is None:
            log.debug("No response (dry run or error)")
            return

        log.debug("--- Response ---")
        log.debug("Status Code: %d", response.status_code)
        log.debug("Headers:")
        for key, value in response.headers.items():
            log.debug("  %s: %s", key, value)

        try:
            response_data = response.json()
            if self.config.pretty_json:
                log.debug(
                    "JSON Body:\n%s", json.dumps(response_data, indent=2)
                )
            else:
                log.debug("JSON Body: %s", response_data)
        except (ValueError, json.JSONDecodeError):
            log.debug("Text Body: %s", response.text)

    def _add_default_headers(self, headers: Dict[str, str]) -> None:
        """Add default headers if not present."""
        if "User-Agent" not in headers:
            headers["User-Agent"] = self.config.user_agent
        if "Accept-Encoding" not in headers:
            headers["Accept-Encoding"] = "gzip, deflate"
        if "Expect" not in headers:
            headers["Expect"] = "100-continue"

    def _build_multipart_body(
        self, files: Dict[str, Any]
    ) -> tuple[bytes, str]:
        """Build multipart form data body."""
        boundary = str(uuid.uuid4())
        body_parts = []

        for field_name, field_value in files.items():
            if isinstance(field_value, tuple) and len(field_value) == 2:
                filename, content = field_value
                value = str(content)
            else:
                value = str(field_value)

            # Match captured format: Content-Type before Content-Disposition
            part = f"--{boundary}\r\n"
            part += "Content-Type: text/plain; charset=utf-8\r\n"
            part += f"Content-Disposition: form-data; name={field_name}\r\n"
            part += "\r\n"
            part += f"{value}\r\n"
            body_parts.append(part)

        # Add final boundary
        body_parts.append(f"--{boundary}--\r\n")
        body = "".join(body_parts).encode("utf-8")

        return body, boundary

    def _send_request(self, prepared) -> Optional[requests.Response]:
        """Send a prepared request."""
        if not kappari_requests_available:
            raise RuntimeError("requests library not available")

        try:
            session = requests.Session()
            response = session.send(
                prepared,
                timeout=self.config.api_timeout,
                proxies=self.config.proxies if self.config.proxies else None,
                verify=self.config.verify_ssl,
            )

            if self.config.debug_api_requests:
                self._log_response(response)

            return response

        except requests.exceptions.RequestException as e:
            log.error("POST request failed: %s", e)
            return None

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[requests.Response]:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint (relative to base URL)
            data: Form data dictionary
            files: Files dictionary (for multipart/form-data)
            headers: HTTP headers

        Returns:
            Response object or None if dry run or error
        """
        url = f"{self.config.api_base_url}/{endpoint.lstrip('/')}"

        if headers is None:
            headers = {}

        self._add_default_headers(headers)

        if self.config.debug_api_requests:
            self._log_request("POST", url, headers, files or data)

        # Build request based on whether we have files
        if files:
            body, boundary = self._build_multipart_body(files)
            headers["Content-Type"] = (
                f'multipart/form-data; boundary="{boundary}"'
            )
            headers["Content-Length"] = str(len(body))
            req = requests.Request(
                method="POST", url=url, data=body, headers=headers
            )
        else:
            req = requests.Request(
                method="POST", url=url, data=data, headers=headers
            )

        prepared = req.prepare()

        if self.config.debug_api_requests:
            self._log_prepared_request(prepared)

        if self.config.dry_run:
            log.info("DRY RUN: Would POST to %s", url)
            if self.config.debug_api_requests:
                self._log_response(None)
            return None

        return self._send_request(prepared)

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[requests.Response]:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint (relative to base URL)
            params: URL parameters
            headers: HTTP headers

        Returns:
            Response object or None if dry run or error
        """
        url = f"{self.config.api_base_url}/{endpoint.lstrip('/')}"

        # Use default headers if none provided
        if headers is None:
            headers = {}

        # Add default User-Agent if not present
        if "User-Agent" not in headers:
            headers["User-Agent"] = self.config.user_agent

        # For debugging, log the request
        if self.config.debug_api_requests:
            self._log_request("GET", url, headers, params)

        # Check if we're in dry run mode
        if self.config.dry_run:
            log.info("DRY RUN: Would GET from %s", url)
            if params:
                log.info("  Params: %s", params)
            if self.config.debug_api_requests:
                self._log_response(None)
            return None

        # Check if requests is available
        if not kappari_requests_available:
            raise RuntimeError("requests library not available")

        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=self.config.api_timeout,
                proxies=self.config.proxies if self.config.proxies else None,
                verify=self.config.verify_ssl,
            )

            if self.config.debug_api_requests:
                self._log_response(response)

            return response

        except requests.exceptions.RequestException as e:
            log.error("GET request failed: %s", e)
            return None

    def authenticate(
        self, email: str, password: str, license_data: str, signature: str
    ) -> Optional[str]:
        """
        Authenticate with Paprika server and get JWT token.

        Args:
            email: User email
            password: User password
            license_data: JSON license data string
            signature: Base64-encoded RSA signature

        Returns:
            JWT token string or None if failed
        """
        # Prepare multipart form data
        files = {
            "email": (None, email),
            "password": (None, password),
            "data": (None, license_data),
            "signature": (None, signature),
        }

        response = self.post("account/login/", files=files)

        if response is None:
            # Dry run or request failed
            return None

        log.info("Server response: %d", response.status_code)

        if response.status_code == 200:
            try:
                result = response.json()
                if "result" in result and "token" in result["result"]:
                    jwt_token = result["result"]["token"]
                    log.info("Authentication successful")
                    return jwt_token
                log.error("Unexpected response format: %s", result)
                return None
            except json.JSONDecodeError:
                log.error("Non-JSON response: %s", response.text)
                return None
        else:
            log.error(
                "Authentication failed with status %d", response.status_code
            )
            try:
                error_data = response.json()
                log.error("Error details: %s", error_data)
            except (ValueError, json.JSONDecodeError):
                log.error("Error response: %s", response.text)
            return None

    def make_authenticated_request(
        self, endpoint: str, jwt_token: str, method: str = "GET", **kwargs
    ) -> Optional[requests.Response]:
        """
        Make an authenticated request to Paprika API.

        Args:
            endpoint: API endpoint
            jwt_token: JWT token for authentication
            method: HTTP method (GET, POST, etc.)
            **kwargs: Additional arguments for the request

        Returns:
            Response object or None if error
        """
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {jwt_token}"
        kwargs["headers"] = headers

        if method.upper() == "GET":
            return self.get(endpoint, **kwargs)
        if method.upper() == "POST":
            return self.post(endpoint, **kwargs)
        raise ValueError(f"Unsupported HTTP method: {method}")


# Create a singleton instance
kappari_client = NetworkClient()


def get_client() -> NetworkClient:
    """Get the singleton network client instance."""
    return kappari_client


if __name__ == "__main__":
    # Test the network client
    try:
        net_client = get_client()

        log.info("Network client initialized")
        log.info("Base URL: %s", net_client.config.api_base_url)
        log.info("Dry run mode: %s", net_client.config.dry_run)
        log.info(
            "Debug API requests: %s", net_client.config.debug_api_requests
        )

        # Test client functionality without making real requests
        log.info("Network client test complete - no requests made")
        log.info("Use auth.py to test actual authentication flow")

    except Exception as e:
        log.error("Error: %s", e)
        sys.exit(1)
