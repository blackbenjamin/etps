import json
import urllib.request
import urllib.error

API_BASE = "http://localhost:8000/api/v1"

def make_request(endpoint, data):
    url = f"{API_BASE}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    json_data = json.dumps(data).encode('utf-8')
    
    print(f"\nTesting {endpoint} with data: {data}")
    try:
        req = urllib.request.Request(url, data=json_data, headers=headers)
        with urllib.request.urlopen(req) as response:
            print("✅ Success")
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error {e.code}: {e.reason}")
        print(f"Response: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"❌ Request Failed: {e}")

# 1. Valid Request (Baseline)
# We need a valid job_profile_id first. 
# Assuming 668 exists from previous run.
valid_id = 668 

# 2. Invalid Job ID
make_request("/resume/generate", {"job_profile_id": 999999, "user_id": 1})

# 3. Invalid User ID
make_request("/resume/generate", {"job_profile_id": valid_id, "user_id": 999999})

# 4. Missing User ID
make_request("/resume/generate", {"job_profile_id": valid_id})

# 5. Missing Job ID
make_request("/resume/generate", {"user_id": 1})

# 6. Invalid Types (String instead of Int)
make_request("/resume/generate", {"job_profile_id": str(valid_id), "user_id": 1})
