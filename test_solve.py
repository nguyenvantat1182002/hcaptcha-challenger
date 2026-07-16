import requests
import base64
import time

# Small 1x1 transparent png
png_hex = "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
image_b64 = base64.b64encode(bytes.fromhex(png_hex)).decode('utf-8')

print("Sending createTask request...")
response = requests.post("http://127.0.0.1:8000/createTask", json={
    "prompt": "Please select all cats",
    "image": image_b64,
    "challenge_type": "image_label_single_select"
})

print(response.status_code)
data = response.json()
print(data)

if not data.get("success"):
    print("Failed to create task.")
    exit(1)

task_id = data.get("taskId")

print(f"Task created: {task_id}. Polling for results...")
max_attempts = 60
for attempt in range(max_attempts):
    res = requests.post("http://127.0.0.1:8000/getTaskResult", json={"taskId": task_id})
    res_data = res.json()
    print(f"Attempt {attempt+1}: {res_data}")
    
    if res_data.get("status") in ["ready", "failed"]:
        print("Final result received.")
        break
        
    time.sleep(1)
else:
    print("Timeout waiting for result.")
