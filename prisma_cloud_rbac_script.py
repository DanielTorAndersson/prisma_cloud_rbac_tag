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
    search_config_url = f"https://{pcc_url}/search/config"

    get_headers = setup_get_headers(token)

    request_data = {
        "query": "config from cloud.resource where cloud.type = 'azure' AND api.name = 'azure-subscription-list' AND json.rule = tags contains \"__AUTO_TEST\"",
        "timeRange": {
            "type": "relative",
            "value": {
                "unit": "hour",
                "amount": 24
            }
        }
    }

    response = requests.post(search_config_url, headers=get_headers, json=request_data)
    response.raise_for_status()

    if response.text:
        try:
            search_config_data = response.json()
            items = search_config_data.get("data", {}).get("items", [])
            extracted_data = [{"subscription_id": item.get("data", {}).get("subscriptionId"),
                              "auto_test_tag": item.get("data", {}).get("tags", {}).get("__AUTO_TEST")} for item in items]
            return extracted_data
        except json.JSONDecodeError:
            print("Error: The response does not contain valid JSON data.")
            return None
    else:
        print("Error: The response is empty.")
        return None

def check_account_group_exists(token, api_key, api_secret, pcc_url, subscription_id):
    get_account_groups_url = f"https://{pcc_url}/cloud/group"
    get_headers = setup_get_headers(token)

    response = requests.get(get_account_groups_url, headers=get_headers)
    response.raise_for_status()

    if response.text:
        try:
            account_groups_data = response.json()
            existing_account_groups = account_groups_data if isinstance(account_groups_data, list) else []

            for group in existing_account_groups:
                if group.get("name") == f"Account Group - {subscription_id}":
                    existing_account_group_id = group.get("id")
                    return existing_account_group_id  # Return the existing account group ID

            return None  # Return None if the account group doesn't exist
        except json.JSONDecodeError:
            print("Error: The response does not contain valid JSON data.")
            return None
    else:
        print("Error: The response is empty.")
        return None



def create_account_group(token, api_key, api_secret, pcc_url, extracted_data):
    get_headers = setup_get_headers(token)

    for item_data in extracted_data:
        subscription_id = item_data.get("subscription_id")

        if subscription_id:
            existing_account_group_id = check_account_group_exists(token, api_key, api_secret, pcc_url, subscription_id)

            if existing_account_group_id:
                print(f"Account Group already exists for Subscription ID: {subscription_id}. Account Group ID: {existing_account_group_id}")
            else:
                request_data = {
                    "accountIds": [subscription_id],
                    "description": f"Account Group for RBAC: {subscription_id}",
                    "name": f"Account Group - {subscription_id}"
                }

                create_account_group_url = f"https://{pcc_url}/cloud/group"
                response = requests.post(create_account_group_url, headers=get_headers, json=request_data)
                
                if response.status_code == 200:
                    print(f"Account Group created for Subscription ID: {subscription_id}")
                else:
                    print(f"Failed to create Account Group for Subscription ID: {subscription_id}")


def get_account_group_ids_by_name(token, api_key, api_secret, pcc_url, extracted_data):
    get_account_group_name_url = f"https://{pcc_url}/cloud/group/name"
    get_headers = setup_get_headers(token)
    response = requests.get(get_account_group_name_url, headers=get_headers)
    response.raise_for_status()
    response_data = response.json()

    matching_ids = []
    subscription_ids = [item_data.get("subscription_id") for item_data in extracted_data]

    for group in response_data:
        name = group.get("name")

        if name in subscription_ids:
            matching_ids.append(group.get("id"))

    print("Account Group IDs:", matching_ids)  # Print the Account group IDs

    # Update the extracted_data dictionary with matching account group IDs
    for item_data in extracted_data:
        if item_data["subscription_id"] in subscription_ids:
            item_data["account_group_id"] = matching_ids[subscription_ids.index(item_data["subscription_id"])]

    print("Extracted Data with Account Group IDs:", extracted_data)  # Print the updated extracted_data

    return matching_ids

def check_user_role_exists(token, api_key, api_secret, pcc_url, auto_test_tag):
    get_user_roles_url = f"https://{pcc_url}/user/role/name"
    get_headers = setup_get_headers(token)

    response = requests.get(get_user_roles_url, headers=get_headers)
    response.raise_for_status()

    if response.text:
        try:
            user_roles_data = response.json()

            for user_role in user_roles_data:
                if user_role.get("name") == auto_test_tag:
                    user_role_id = user_role.get("id")  # Get the user role ID                 
                    user_role_name = auto_test_tag  # Use the auto_test_tag as the user role name
                    #update_user_role(token, api_key, api_secret, pcc_url, user_role_id, user_role_name)
                    return user_role_id

            return None  # Return None if the role doesn't exist
        except json.JSONDecodeError:
            print("Error: The response does not contain valid JSON data.")
            return None
    else:
        print("Error: The response is empty.")
        return None

def update_user_role(token, api_key, api_secret, pcc_url, user_role_id, user_role_name):
    get_headers = setup_get_headers(token)
    update_user_role_url = f"https://{pcc_url}/user/role/{user_role_id}"

    # Collect all the account_group_ids based on auto_test_tag that matches the user role name
    matching_account_group_ids = []

    for item_data in extracted_data:  # You can fetch extracted_data here
        if item_data.get("auto_test_tag") == user_role_name:
            matching_account_group_id = item_data.get("account_group_id")
            matching_account_group_ids.append(matching_account_group_id)

    request_data = {
        "accountGroupIds": matching_account_group_ids
    }

    response = requests.put(update_user_role_url, headers=get_headers, json=request_data)
    response.raise_for_status()

    if response.status_code == 200:
        print(f"User Role {user_role_id} updated with Account Group IDs: {', '.join(matching_account_group_ids)}")
    else:
        print(f"Failed to update User Role {user_role_id} with Account Group IDs: {', '.join(matching_account_group_ids)}")

def create_user_roles(token, api_key, api_secret, pcc_url, extracted_data):
    get_headers = setup_get_headers(token)
    common_request_data = {
        "description": "",
        "roleType": "Account Group Admin",
        "restrictDismissalAccess": False,
        "additionalAttributes": {
            "onlyAllowCIAccess": False,
            "onlyAllowComputeAccess": False
        }
    }

    for item_data in extracted_data:
        subscription_id = item_data.get("subscription_id")
        auto_test_tag = item_data.get("auto_test_tag")
        account_group_id = item_data.get("account_group_id")

        if subscription_id:
            user_role_id = check_user_role_exists(token, api_key, api_secret, pcc_url, auto_test_tag)

            if user_role_id:
                # Update the existing role with account group IDs
                update_user_role(token, api_key, api_secret, pcc_url, user_role_id, auto_test_tag)
            else:
                # Create a new role with the single account group
                request_data = {
                    "accountGroupIds": [account_group_id],
                    "name": auto_test_tag,
                    **common_request_data
                }

                create_user_role_url = f"https://{pcc_url}/user/role"
                response = requests.post(create_user_role_url, headers=get_headers, json=request_data)
                response.raise_for_status()

                if response.status_code == 200:
                    print(f"User Role created for Subscription ID: {subscription_id}, Tag: {auto_test_tag}")
                else:
                    print(f"Failed to create User Role for Subscription ID: {subscription_id}, Tag: {auto_test_tag}")

if __name__ == "__main__":
    api_key = os.environ.get("PRISMACLOUD_USERNAME")
    api_secret = os.environ.get("PRISMACLOUD_PASSWORD")
    pcc_url = os.environ.get("PRISMACLOUD_URL")

    token = get_prismacloud_token(api_key, api_secret, pcc_url)
    extracted_data = fetch_search_config(token, api_key, api_secret, pcc_url)

    create_account_group(token, api_key, api_secret, pcc_url, extracted_data)

    # Check for matching account group names and collect IDs
    account_group_ids_by_name = get_account_group_ids_by_name(token, api_key, api_secret, pcc_url, extracted_data)

    create_user_roles(token, api_key, api_secret, pcc_url, extracted_data)
