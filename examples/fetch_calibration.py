import json
from app.calserver_api import fetch_calibration_data

BASE_URL = "https://{{DOMAIN}}"  # replace with your calServer URL
USERNAME = "{{HTTP_X_REST_USERNAME}}"
PASSWORD = "{{HTTP_X_REST_PASSWORD}}"
API_KEY = "{{HTTP_X_REST_API_KEY}}"

FILTER = [
    {"property": "C2339", "value": "1", "operator": "="},
]

if __name__ == "__main__":
    data = fetch_calibration_data(BASE_URL, USERNAME, PASSWORD, API_KEY, FILTER)
    print(json.dumps(data, indent=2))
