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
4. Send an HTTP POST request to `http://127.0.0.1:8000/solve`.
5. Receive the exact X, Y coordinates to click on the image.

## 2. API Specifications

### 2.1 POST /solve

**Endpoint**: `POST http://127.0.0.1:8000/solve`
**Content-Type**: `application/json`

#### Request Payload (JSON)
| Field | Type | Required | Description |
|---|---|---|---|
| `prompt` | string | **Yes** | The challenge question (e.g., "Click on images that contain a dog"). |
| `image` | string | **Yes** | Base64 encoded string of the challenge image. Do **not** include the `data:image/jpeg;base64,` prefix. |
| `challenge_type` | string | No | Type of challenge if known (e.g., `image_label_single_select`, `image_label_multiple_select`). |
| `timeout` | float | No | Override the internal LLM timeout in seconds. |

#### Response Payload (JSON)
| Field | Type | Description |
|---|---|---|
| `success` | boolean | `true` if the agent successfully analyzed the image, `false` otherwise. |
| `coordinates` | array | Array of objects containing `x` and `y` coordinates representing where to click on the original image. |

**Example Response**:
```json
{
  "success": true,
  "coordinates": [
    { "x": 125, "y": 80 },
    { "x": 300, "y": 210 }
  ]
}
```

### 2.2 POST /report

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

You must adapt one of the following code snippets to fit into your active script when you need to solve an hCaptcha.

### Python Example
Use this snippet if your current script environment uses Python. It uses the standard `requests` library.

```python
import base64
import requests

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

    # 3. Send the request to the local solver API
    try:
        response = requests.post("http://127.0.0.1:8000/solve", json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        if result.get("success"):
            return result.get("coordinates", [])
        else:
            print("Failed to solve captcha.")
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
Use this snippet if your current script environment uses Node.js. It uses the native `fetch` API and `fs` module.

```javascript
const fs = require('fs');

async function solveHcaptcha(imagePath, prompt) {
    /**
     * Solves an hCaptcha challenge and returns an array of click coordinates.
     */
    try {
        // 1. Read and base64 encode the image
        const imageBuffer = fs.readFileSync(imagePath);
        const base64Image = imageBuffer.toString('base64');

        // 2. Prepare the payload
        const payload = {
            prompt: prompt,
            image: base64Image
        };

        // 3. Send the request to the local solver API
        const response = await fetch("http://127.0.0.1:8000/solve", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        
        if (result.success) {
            return result.coordinates || [];
        } else {
            console.error("Failed to solve captcha.");
            return [];
        }
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
