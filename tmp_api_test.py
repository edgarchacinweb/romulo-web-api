import urllib.request
import json

url = "http://localhost:3000/auditory/filter"

try:
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE3NzUxNjYwMjAsImV4cCI6MTc3Njk4MDQyMCwiaWQiOiJlZjA1ODEyYi0xMGUyLTRlYzUtODM0MC0zYjdiMjYzMjk1NTMiLCJyb2xlIjoiQURNSU4ifQ.ANNsxSVCh3hLzPpimbLR-urak8r1zM3O6YJyAXeZc7A"
    
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
    with urllib.request.urlopen(req) as response:
        data = response.read()
        print("Status", response.getcode())
        parsed = json.loads(data.decode('utf-8'))
        print("Length:", len(parsed))
        if len(parsed) > 0:
            print("First item:", parsed[0])
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
