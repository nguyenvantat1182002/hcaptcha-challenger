import requests
import base64

# Small 1x1 transparent png
png_hex = "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
image_b64 = base64.b64encode(bytes.fromhex(png_hex)).decode('utf-8')

response = requests.post("http://127.0.0.1:8000/solve", json={
    "prompt": "Please select all cats",
    "image": image_b64,
    "challenge_type": "image_label_single_select"
})

print(response.status_code)
print(response.json())
