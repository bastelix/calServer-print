"""Small wrapper around the calServer REST API."""

import requests
from typing import Any, Dict


def fetch_calibration_data(
    base_url: str,
    username: str,
    password: str,
    api_key: str,
    filter_json: Dict[str, Any],
) -> Dict[str, Any]:
    """Fetch calibration information from the API.

    The function performs a ``GET`` request against ``/api/calibration`` and
    returns the parsed JSON content of the response.

    Parameters
    ----------
    base_url:
        Base URL of the calServer instance.
    username:
        User name for authentication.
    password:
        Password for authentication.
    api_key:
        Additional API key to use.
    filter_json:
        JSON payload used as a query filter.

    Returns
    -------
    dict
        Parsed JSON content of the successful API response.
    """
    params = {
        'HTTP_X_REST_USERNAME': username,
        'HTTP_X_REST_PASSWORD': password,
        'HTTP_X_REST_API_KEY': api_key,
    }
    url = f"{base_url.rstrip('/')}/api/calibration"
    response = requests.get(url, params=params, json=filter_json, timeout=10)
    response.raise_for_status()
    return response.json()
