"""
Pramana AI — Mock VClaim Response Helpers.

Standard VClaim 2.0 response envelope format.
"""
from typing import Any


def ok_response(data: Any) -> dict:
    """Build a successful VClaim response envelope.

    Args:
        data: Response payload.

    Returns:
        Standard VClaim 2.0 success response.
    """
    return {
        "metaData": {
            "code": "200",
            "message": "OK",
        },
        "response": data,
    }


def error_response(code: str, message: str) -> dict:
    """Build an error VClaim response envelope.

    Args:
        code: Error code (e.g., "400", "401", "500").
        message: Human-readable error message.

    Returns:
        Standard VClaim 2.0 error response.
    """
    return {
        "metaData": {
            "code": code,
            "message": message,
        },
        "response": None,
    }


def not_found_response(message: str = "Data tidak ditemukan") -> dict:
    """Build a 'not found' response (code 201 in VClaim convention).

    Args:
        message: Not found message.

    Returns:
        Standard VClaim 2.0 not-found response.
    """
    return {
        "metaData": {
            "code": "201",
            "message": message,
        },
        "response": None,
    }
