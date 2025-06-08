import requests
from typing import Any, Dict


def fetch_calibration_data(base_url: str, username: str, password: str, api_key: str, filter_json: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch calibration data from calServer API."""
    params = {
        'username': username,
        'password': password,
        'api_key': api_key,
    }
    url = f"{base_url.rstrip('/')}/api/calibration"
    response = requests.get(url, params=params, json=filter_json, timeout=10)
    response.raise_for_status()
    return response.json()
