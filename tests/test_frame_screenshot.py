from DrissionPage import ChromiumPage
import base64
from pathlib import Path
import time

def test_screenshot():
    page = ChromiumPage()
    try:
        page.get("https://accounts.hcaptcha.com/demo")
        time.sleep(3)
        
        # Find the iframe
        frame = page.get_frame('@title=widget containing checkbox for hCaptcha security challenge')
        if not frame:
            print("Could not find hcaptcha frame")
            return
            
        print("Found frame. Attempting to capture from frame target...")
        
        # Get bounding rect of a target element in the frame (e.g. the checkbox)
        checkbox = frame.ele('#checkbox')
        rect = checkbox._run_js('return this.getBoundingClientRect().toJSON();')
        print(f"Rect: {rect}")
        
        try:
            data = frame._run_cdp(
                'Page.captureScreenshot',
                format='png',
                clip={'x': rect['x'], 'y': rect['y'], 'width': rect['width'], 'height': rect['height'], 'scale': 1}
            )
            img_bytes = base64.b64decode(data['data'])
            Path("tmp/test_frame_capture.png").parent.mkdir(exist_ok=True)
            Path("tmp/test_frame_capture.png").write_bytes(img_bytes)
            print("Successfully captured screenshot via frame target!")
        except Exception as e:
            print(f"Failed to capture via frame target: {e}")
            
    finally:
        page.quit()

if __name__ == "__main__":
    test_screenshot()
