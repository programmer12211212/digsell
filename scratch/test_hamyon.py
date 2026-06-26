import urllib.request
import urllib.error
import json

try:
    print("Testing connection to https://hamyon-api.uz...")
    response = urllib.request.urlopen("https://hamyon-api.uz", timeout=5)
    print("Status:", response.status)
    print("Content:", response.read().decode('utf-8')[:200])
except Exception as e:
    print("Error:", e)
