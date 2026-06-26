import socket

try:
    ip = socket.gethostbyname("hamyon-api.uz")
    print("IP Address of hamyon-api.uz:", ip)
except Exception as e:
    print("Resolution error:", e)
