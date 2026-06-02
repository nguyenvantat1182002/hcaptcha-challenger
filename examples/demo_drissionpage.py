import time

from DrissionPage import ChromiumPage, ChromiumOptions
from hcaptcha_challenger import AgentV, AgentConfig


opts = ChromiumOptions().auto_port()
page = ChromiumPage(addr_or_opts=opts)

page.get('https://account.riotgames.com/')


def start(page: ChromiumPage):
    frames = page.get_frames("css://iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') and contains(@src, 'frame=challenge')]")
    frame = frames[-1]

    config = AgentConfig(MOUSE_SPEED=0.5)

    agent = AgentV(frame, config)
    agent.wait_for_challenge()

    input('Continue')

    page.quit(del_data=True)
    