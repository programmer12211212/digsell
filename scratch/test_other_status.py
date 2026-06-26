import requests

# Test a non-existent random payment ID
url_fake = "https://hamyon-api.uz/merchant/fake_payment_id_12345/json"
print(f"Querying fake payment ID: {url_fake}")
try:
    res = requests.get(url_fake, timeout=5)
    print("Status code:", res.status_code)
    print("Response text:", res.text[:200])
except Exception as e:
    print("Error:", e)
