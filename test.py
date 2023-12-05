import os
import requests
import json
import time

def get_prismacloud_token(api_key, api_secret, pcc_url):
    auth_url = f"https://{pcc_url}/login"

    auth_headers = {"Content-Type": "application/json"}
    auth_data = {"username": api_key, "password": api_secret}

    auth_response = requests.post(auth_url, headers=auth_headers, json=auth_data)
    auth_response.raise_for_status()
    token = auth_response.json()["token"]
    return token

def setup_get_headers(token):
    get_headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    return get_headers

def fetch_search_config(token, api_key, api_secret, pcc_url):
    base_url = f"https://{pcc_url}"
    search_config_url = f"{base_url}/search/config"
    search_config_page_url = f"{base_url}/search/config/page"

    get_headers = setup_get_headers(token)

    limit = 100
    items = []
    next_page_token = None

    while True:
        request_data = {
            "query": "config from cloud.resource where cloud.type = 'azure' AND cloud.service = 'Azure Virtual Network'",
            "timeRange": {
                "type": "relative",
                "value": {
                    "unit": "hour",
                    "amount": 24
                }
            },
            "limit": limit,
            "nextPageToken": next_page_token
        }

        response = requests.post(search_config_url, headers=get_headers, json=request_data)
        response.raise_for_status()

        if response.text:
            try:
                search_config_data = response.json()
                current_page_items = search_config_data.get("data", {}).get("items", [])
                items.extend([{
                    "subscription_id": item.get("data", {}).get("subscriptionId"),
                    "auto_test_tag": item.get("data", {}).get("tags", {}).get("__AUTO_TEST")
                } for item in current_page_items])

                # Print the number of resources obtained in the current response
                print(f"Number of resources in response: {len(current_page_items)}")

                # Check if there are more pages
                next_page_token = search_config_data.get("data", {}).get("nextPageToken")
                if not next_page_token:
                    break  # Break the loop if there are no more pages

            except json.JSONDecodeError:
                print("Error: The response does not contain valid JSON data.")
                return None
        else:
            print("Error: The response is empty.")
            return None

    print(f"Total subscriptions: {len(items)}")
    return items


if __name__ == "__main__":
    api_key = os.environ.get("PRISMACLOUD_USERNAME")
    api_secret = os.environ.get("PRISMACLOUD_PASSWORD")
    pcc_url = os.environ.get("PRISMACLOUD_URL")

    token = get_prismacloud_token(api_key, api_secret, pcc_url)
    extracted_data = fetch_search_config(token, api_key, api_secret, pcc_url)
