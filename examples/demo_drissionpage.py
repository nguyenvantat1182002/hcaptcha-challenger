import time
import threading

from DrissionPage import ChromiumPage, ChromiumOptions
from hcaptcha_challenger import AgentV, AgentConfig


opts = ChromiumOptions().auto_port()
page = ChromiumPage(addr_or_opts=opts)

page.get('https://account.riotgames.com/')


def start(page: ChromiumPage):
    print("Thread started, looking for challenge frames...")
    # Give it a moment to load if needed
    time.sleep(2) 
    
    frames = page.get_frames("css://iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') and contains(@src, 'frame=challenge')]")
    if not frames:
        print("Could not find challenge frame.")
        return
        
    frame = frames[-1]

    config = AgentConfig(MOUSE_SPEED=0.5)

    agent = AgentV(frame, config)
    agent.wait_for_challenge()
    print("Challenge solved in thread!")


if __name__ == '__main__':
    # Start the challenge solving in a background thread
    worker = threading.Thread(target=start, args=(page,))
    worker.start()

    # Main thread waits for user input so the script doesn't exit immediately
    input('Press Enter at any time to close the browser and exit...\n')
    page.quit(del_data=True)