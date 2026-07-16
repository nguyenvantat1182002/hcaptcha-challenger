---
name: hcaptcha-solver
description: "Instruction manual for integrating with the local hcaptcha-challenger API to autonomously bypass hCaptcha challenges."
---

# System Prompt / AI Agent Skill: hCaptcha Solver API

> **Notice to AI Agents**: This document is an instruction manual for integrating with the local `hcaptcha-challenger` API. Read these instructions carefully to autonomously bypass hCaptcha challenges during your execution workflows. Do **not** look for external helper scripts; you are expected to write and execute the HTTP request code yourself using the language of your current environment (e.g., Python or Node.js).

## 1. Objective
Your goal is to solve hCaptcha visual challenges encountered during automated browser sessions. Instead of manually interacting with the hCaptcha iframe elements to guess the answers, you must use the local `hcaptcha-challenger` API running on `http://127.0.0.1:8000`.

When you encounter an hCaptcha challenge:
1. Capture a screenshot or extract the source image of the captcha payload.
2. Read the text prompt of the challenge (e.g., "Please select all cats").
3. Base64 encode the image.
4. Send an HTTP POST request to `http://127.0.0.1:8000/createTask`.
5. Continuously poll `http://127.0.0.1:8000/getTaskResult` with a max timeout (e.g., 60 seconds) to receive the exact X, Y coordinates to click on the image.

## 2. API Specifications

### 2.1 POST /createTask

**Endpoint**: `POST http://127.0.0.1:8000/createTask`
**Content-Type**: `application/json`

#### Request Payload (JSON)
| Field | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | **Yes** | The challenge question (e.g., "Click on images that contain a dog"). |
| `image` | string | **Yes** | Base64 encoded string of the challenge image. Do **not** include the `data:image/jpeg;base64,` prefix. |
| `challenge_type` | string | No | Type of challenge if known (e.g., `image_label_single_select`, `image_label_multiple_select`). |
| `timeout` | float | No | Override the internal LLM timeout in seconds (default 300). |

#### Response Payload (JSON)
| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` if the task was successfully created. |
| `taskId` | string | A unique identifier for the task, used to retrieve results. |

**Example Response**:
```json
{
  "success": true,
  "taskId": "88624b18-c9d2-4fe2-85b1-bd6394329b9d"
}
```

### 2.2 POST /getTaskResult

**Endpoint**: `POST http://127.0.0.1:8000/getTaskResult`
**Content-Type**: `application/json`

#### Request Payload (JSON)
| Field | Type | Required | Description |
|---|---|---|---|
| `taskId` | string | **Yes** | The task ID returned from `/createTask`. |

#### Response Payload (JSON)
| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` if the request was handled properly. |
| `status` | string | Status of the task: `"processing"`, `"ready"`, or `"failed"`. |
| `solution` | object | (Only if `status="ready"`) Contains the `coordinates` array. |
| `error` | string | (Only if `status="failed"`) The error message. |

**Example Response (ready)**:
```json
{
  "success": true,
  "status": "ready",
  "solution": {
    "coordinates": [
      { "x": 125, "y": 80 },
      { "x": 300, "y": 210 }
    ]
  }
}
```

### 2.3 POST /report

**Endpoint**: `POST http://127.0.0.1:8000/report`
**Content-Type**: `application/json`

**Description**: Used to report the final outcome of the challenge. Reporting helps the internal Supervisor AI learn from failures and dynamically update its rules.

#### Request Payload (JSON)
| Field | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | **Yes** | The challenge question you attempted to solve. |
| `success` | boolean | **Yes** | `true` if hCaptcha accepted the solution, `false` if the challenge failed/rejected the clicks. |

**Example Request**:
```json
{
  "prompt": "Click on images that contain a dog",
  "success": false
}
```

## 3. Implementation Examples

You must adapt one of the following code snippets to fit into your active script when you need to solve an hCaptcha. Ensure you respect the maximum polling iterations to avoid infinite loops.

### Python Example
Use this snippet if your current script environment uses Python. It uses the standard `requests` library and polls the async API.

```python
import base64
import requests
import time

def solve_hcaptcha(image_path: str, prompt: str) -> list:
    """
    Solves an hCaptcha challenge and returns a list of click coordinates.
    """
    # 1. Read and base64 encode the image
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    # 2. Prepare the payload
    payload = {
        "prompt": prompt,
        "image": base64_image
    }

    try:
        # 3. Create the task
        create_resp = requests.post("http://127.0.0.1:8000/createTask", json=payload, timeout=10)
        create_resp.raise_for_status()
        
        task_data = create_resp.json()
        if not task_data.get("success"):
            print("Failed to create task.")
            return []
            
        task_id = task_data.get("taskId")
        
        # 4. Poll for the result (max 60 seconds)
        max_attempts = 60
        for attempt in range(max_attempts):
            result_resp = requests.post("http://127.0.0.1:8000/getTaskResult", json={"taskId": task_id}, timeout=10)
            result_resp.raise_for_status()
            
            res_data = result_resp.json()
            status = res_data.get("status")
            
            if status == "ready":
                return res_data.get("solution", {}).get("coordinates", [])
            elif status == "failed":
                print(f"Task failed: {res_data.get('error')}")
                return []
                
            time.sleep(1) # Wait before polling again
            
        print("Timeout waiting for captcha to solve.")
        return []
    except Exception as e:
        print(f"Error communicating with solver API: {e}")
        return []

def report_hcaptcha(prompt: str, success: bool) -> bool:
    """
    Reports the success or failure of a challenge attempt.
    """
    payload = {
        "prompt": prompt,
        "success": success
    }
    try:
        response = requests.post("http://127.0.0.1:8000/report", json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error reporting challenge status: {e}")
        return False

# Example usage:
# prompt = "Please select all cats"
# coords = solve_hcaptcha("captcha_screenshot.jpg", prompt)
# print(coords) # [{'x': 120, 'y': 250}, ...]
# 
# # After clicking the coordinates and verifying if the captcha was solved:
# is_solved = True # Replace with actual check
# report_hcaptcha(prompt, is_solved)
```

### Node.js Example
Use this snippet if your current script environment uses Node.js. It uses the native `fetch` API and a custom sleep function to avoid blocking the main loop.

```javascript
const fs = require('fs');

const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

async function solveHcaptcha(imagePath, prompt) {
    /**
     * Solves an hCaptcha challenge and returns an array of click coordinates.
     */
    try {
        // 1. Read and base64 encode the image
        const imageBuffer = fs.readFileSync(imagePath);
        const base64Image = imageBuffer.toString('base64');

        // 2. Create the task
        const payload = {
            prompt: prompt,
            image: base64Image
        };

        const createResp = await fetch("http://127.0.0.1:8000/createTask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!createResp.ok) throw new Error(`HTTP error! status: ${createResp.status}`);
        
        const createData = await createResp.json();
        if (!createData.success) {
            console.error("Failed to create task.");
            return [];
        }

        const taskId = createData.taskId;
        
        // 3. Poll for the result (max 60 seconds)
        const maxAttempts = 60;
        for (let i = 0; i < maxAttempts; i++) {
            const resultResp = await fetch("http://127.0.0.1:8000/getTaskResult", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ taskId: taskId })
            });
            
            if (!resultResp.ok) throw new Error(`HTTP error! status: ${resultResp.status}`);
            
            const resData = await resultResp.json();
            
            if (resData.status === "ready") {
                return resData.solution?.coordinates || [];
            } else if (resData.status === "failed") {
                console.error(`Task failed: ${resData.error}`);
                return [];
            }
            
            await delay(1000); // Wait 1 second before polling again
        }
        
        console.error("Timeout waiting for captcha to solve.");
        return [];
    } catch (error) {
        console.error(`Error communicating with solver API: ${error.message}`);
        return [];
    }
}

async function reportHcaptcha(prompt, success) {
    /**
     * Reports the success or failure of a challenge attempt.
     */
    try {
        const payload = {
            prompt: prompt,
            success: success
        };

        const response = await fetch("http://127.0.0.1:8000/report", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return true;
    } catch (error) {
        console.error(`Error reporting challenge status: ${error.message}`);
        return false;
    }
}

// Example usage:
// const prompt = "Please select all cats";
// solveHcaptcha("captcha_screenshot.jpg", prompt).then(async (coords) => {
//     console.log(coords); // [{ x: 120, y: 250 }, ...]
//     
//     // After clicking the coordinates and verifying if the captcha was solved:
//     const isSolved = true; // Replace with actual check
//     await reportHcaptcha(prompt, isSolved);
// });
```

---
**Agent Action Required**:
If you are automating a browser session, use the provided coordinates to move the mouse and click exactly on the targets. Do not offset the coordinates unless you cropped the original screenshot incorrectly.
