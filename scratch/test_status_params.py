import requests

payment_id = "f9af8d96ce38"
shop_id = "383"
shop_key = "e61538147450"

urls = [
    # Query parameters
    f"https://hamyon-api.uz/merchant/{payment_id}/json?shop_id={shop_id}&shop_key={shop_key}",
    f"https://hamyon-api.uz/merchant/{payment_id}/json?shop_key={shop_key}",
    # Just payment_id
    f"https://hamyon-api.uz/merchant/{payment_id}/json",
]

for url in urls:
    try:
        print(f"\nQuerying: {url}")
        # Try with headers
        headers = {
            "Shop-Id": shop_id,
            "Shop-Key": shop_key,
            "Authorization": f"Bearer {shop_key}"
        }
        res = requests.get(url, headers=headers, timeout=5)
        print("Status:", res.status_code)
        print("Content:", res.text[:200])
    except Exception as e:
        print("Error:", e)
