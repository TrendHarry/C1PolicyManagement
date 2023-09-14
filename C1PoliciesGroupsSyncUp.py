import requests
import json

def fetch_policies(api_key, region):
    url = f"https://workload.{region}.cloudone.trendmicro.com/api/policies"
    headers = {
        'Authorization': f'ApiKey {api_key}',
        'api-version': 'v1',
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)['policies']
    else:
        print(f"Failed to retrieve policies. HTTP Status Code: {response.status_code}")
        return None
    
def fetch_policy_by_id(api_key, region, policy_id):
    url = f"https://workload.{region}.cloudone.trendmicro.com/api/policies/{policy_id}"
    headers = {
        'Authorization': f'ApiKey {api_key}',
        'api-version': 'v1',
        'Content-Type': 'application/json',
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return json.loads(response.text)
    else:
        print(f"Failed to retrieve policy {policy_id}. HTTP Status Code: {response.status_code}")
        return None

def compare_policies(policies):
    policy_groups = {'dev-WinSvr': {}, 'prd-WinSvr': {}, 'qas-WinSvr': {}}
    for policy in policies:
        name = policy.get('name', '')
        policy_id = policy.get('ID', '')
        parent_id = policy.get('parentID', '')
        
        if name in policy_groups.keys():
            policy_groups[name]['ID'] = policy_id
        else:
            for group_name, group_data in policy_groups.items():
                if parent_id == group_data.get('ID'):
                    role_name = name.split('-')[-1]
                    policy_groups[group_name].setdefault('child_policies', {})[role_name] = policy_id
    
    comparison_results = {}
    for group_name, group_data in policy_groups.items():
        comparison_results[group_name] = {}
        child_policies = set(group_data.get('child_policies', {}).keys())
        
        for other_group_name, other_group_data in policy_groups.items():
            if group_name != other_group_name:
                other_child_policies = set(other_group_data.get('child_policies', {}).keys())
                missing_policies = child_policies - other_child_policies
                
                if missing_policies:
                    comparison_results[group_name][other_group_name] = list(missing_policies)
    
    return comparison_results, policy_groups

def remove_empty_lists(data):
    if isinstance(data, dict):
        return {key: remove_empty_lists(value) for key, value in data.items() if key != "lists"}
    elif isinstance(data, list):
        return [remove_empty_lists(item) for item in data]
    else:
        return data

    
def duplicate_policy(api_key, region, policy_id, new_name, parent_id):
    policy_data = fetch_policy_by_id(api_key, region, policy_id)
    if not policy_data:
        return False

    parent_policy_data = fetch_policy_by_id(api_key, region, parent_id)
    if not parent_policy_data:
        return False

    policy_data = remove_empty_lists(policy_data)

    policy_data['antiMalware']['realTimeScanConfigurationID'] = parent_policy_data['antiMalware']['realTimeScanConfigurationID']
    policy_data['antiMalware']['realTimeScanScheduleID'] = parent_policy_data['antiMalware']['realTimeScanScheduleID']
    policy_data['antiMalware']['manualScanConfigurationID'] = parent_policy_data['antiMalware']['manualScanConfigurationID']
    policy_data['antiMalware']['scheduledScanConfigurationID'] = parent_policy_data['antiMalware']['scheduledScanConfigurationID']

    policy_data['name'] = new_name
    policy_data['parentID'] = parent_id

    url = f"https://workload.{region}.cloudone.trendmicro.com/api/policies"
    payload = json.dumps(policy_data)
    headers = {
        'Authorization': f'ApiKey {api_key}',
        'api-version': 'v1',
        'Content-Type': 'application/json',
    }
    response = requests.post(url, headers=headers, data=payload)

    if response.status_code == 200:
        print(f"Successfully duplicated policy as {new_name}.")
        return True
    else:
        print(f"Failed to create policy. HTTP Status Code: {response.status_code}")
        return False


def main():
    region = input("Enter your region: ")
    api_key = input("Enter your C1 API key: ")
    
    policies = fetch_policies(api_key, region)
    if not policies:
        print("Exiting...")
        return
    
    comparison_results, policy_groups = compare_policies(policies)
    
    for group_name, missing_data in comparison_results.items():
        all_missing_policies = []
        
        for other_group_name, missing_policies in missing_data.items():
            for missing_policy in missing_policies:
                all_missing_policies.append((missing_policy, other_group_name))
        
        if all_missing_policies:
            print(f"Missing policies for {group_name}:")
            for i, (missing_policy, other_group_name) in enumerate(all_missing_policies):
                print(f"{i + 1}. {missing_policy} is missing in {other_group_name}")
            
            selected_indices = input("Select the policies to duplicate (comma-separated indices, e.g., 1,3,5): ").split(',')
            for index in selected_indices:
                if index.isdigit() and 0 < int(index) <= len(all_missing_policies):
                    missing_policy, other_group_name = all_missing_policies[int(index) - 1]
                    source_policy_id = policy_groups[group_name]['child_policies'][missing_policy]
                    new_name = f"{other_group_name}-{missing_policy}"
                    parent_id = policy_groups[other_group_name]['ID']
                    
                    duplicate_policy(api_key, region, source_policy_id, new_name, parent_id)

if __name__ == "__main__":
    main()


