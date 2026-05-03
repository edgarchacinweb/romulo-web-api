import urllib.request
from urllib.error import HTTPError

file_name = "carnet-03755c9e-9266-41ad-8326-061200880269.webp"
url = f"http://localhost:3000/docs/get/{file_name}?preview=1"

print("Testing HEAD...")
req = urllib.request.Request(url, method="HEAD")
try:
    with urllib.request.urlopen(req) as response:
        print(f"HEAD Status: {response.status}")
except HTTPError as e:
    print(f"HEAD failed with HTTP Error: {e.code}")
except Exception as e:
    print(f"HEAD failed: {e}")

print("Testing GET...")
req = urllib.request.Request(url, method="GET")
try:
    with urllib.request.urlopen(req) as response:
        print(f"GET Status: {response.status}")
except HTTPError as e:
    print(f"GET failed with HTTP Error: {e.code}")
except Exception as e:
    print(f"GET failed: {e}")
