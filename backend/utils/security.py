"""
Security Utility for RCD² Platform
==================================

Handles API Key authentication and security dependencies.
Uses constant-time comparison to prevent timing attacks.
"""

import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from backend.utils.logger import get_logger

logger = get_logger(__name__)

# Define the header key
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)


def get_api_key(
    api_key_header: str = Security(api_key_header),
) -> str:
    """
    Validate the API Key provided in the header.

    Security Measures:
    - Uses secrets.compare_digest for constant-time comparison (anti-timing attack).
    - Checks against environment variable RCD2_API_KEY.
    """
    # Retrieve the correct key from environment
    correct_key = os.getenv("RCD2_API_KEY")

    # Fail secure if no key is configured in the environment
    if not correct_key:
        logger.critical(
            "Security misconfiguration: RCD2_API_KEY environment variable not set."
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server security configuration error",
        )

    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key",
        )

    # Constant-time comparison
    if not secrets.compare_digest(api_key_header, correct_key):
        logger.warning("Failed authentication attempt with invalid key")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )

    return api_key_header
