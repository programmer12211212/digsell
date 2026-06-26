import requests
import time

# Create a new payment
create_url = "https://hamyon-api.uz/payment/create"
create_data = {
    "shop_id": "383",
    "shop_key": "e61538147450",
    "amount": 2000
}

print("Creating payment...")
create_res = requests.post(create_url, data=create_data)
create_json = create_res.json()
print("Payment created:", create_json)

payment_id = create_json.get("payment_id")
if payment_id:
    status_url = f"https://hamyon-api.uz/merchant/{payment_id}/json"
    print(f"Querying status with 35 seconds timeout: {status_url}")
    start_time = time.time()
    try:
        status_res = requests.get(status_url, timeout=35)
        print("Status code:", status_res.status_code)
        print("Response JSON:", status_res.json())
        print(f"Completed in {time.time() - start_time:.2f} seconds")
    except Exception as e:
        print("Error after", f"{time.time() - start_time:.2f} seconds:", e)
else:
    print("Could not create payment")
