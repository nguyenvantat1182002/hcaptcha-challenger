from DrissionPage import ChromiumPage, ChromiumOptions
from hcaptcha_challenger import AgentV, AgentConfig

opts = ChromiumOptions()
page = ChromiumPage(addr_or_opts=opts)


page.get('https://account.riotgames.com/')

frame = page.get_frame("css://iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') and contains(@src, 'frame=challenge')]")

config = AgentConfig(ignore_request_types=['image_drag_multi', 'image_drag_single'], MOUSE_SPEED=0.5)

agent = AgentV(frame, config)
agent.wait_for_challenge()

input('Continue')
