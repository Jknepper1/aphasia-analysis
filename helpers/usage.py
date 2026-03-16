import requests
import time

# Set your API key (must have api.usage.read scope)
api_key = "ADMIN_API_KEY_HERE"

# Set the time range (e.g., the last 7 days)
end_time = int(time.time())
start_time = end_time - (7 * 24 * 60 * 60)

url = "https://api.openai.com/v1/organization/costs"

headers = {
    "Authorization": f"Bearer {api_key}"
}

params = {
    "start_time": start_time,
    "end_time": end_time,
    "limit": 100 # Adjust pagination limit as needed
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    cost_data = response.json()
    print("Cost Data Retrieved Successfully!")
    # The API returns an array of daily line items
    for item in cost_data.get('data', []):
        print(f"Amount: ${item['amount']} | Line Item: {item['line_item']}")
else:
    print(f"Error: {response.json()}")