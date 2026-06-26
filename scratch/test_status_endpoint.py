import requests

payment_id = "f9af8d96ce38"  # Use the payment ID generated from our previous run
url = f"https://hamyon-api.uz/merchant/{payment_id}/json"

print(f"Querying {url} ...")

headers_list = [
    {},  # No headers
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}, # Browser UA
]

for i, headers in enumerate(headers_list):
    try:
        print(f"\nAttempt {i+1} with headers: {headers}")
        response = requests.get(url, headers=headers, timeout=5)
        print("Status Code:", response.status_code)
        print("Response Text:", response.text[:200])
    except Exception as e:
        print("Error:", e)
