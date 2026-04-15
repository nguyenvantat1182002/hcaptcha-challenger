from DrissionPage import ChromiumPage, ChromiumOptions
from hcaptcha_challenger import AgentV, AgentConfig

opts = ChromiumOptions()
page = ChromiumPage(addr_or_opts=opts)


page.get('https://democaptcha.com/demo-form-eng/hcaptcha.html')

frame = page.get_frame("css://iframe[starts-with(@src,'https://newassets.hcaptcha.com/captcha/v1/') and contains(@src, 'frame=challenge')]")

config = AgentConfig(ignore_request_types=['image_drag_multi', 'image_drag_single', 'image_label_multi_select', 'image_label_single_select'])

agent = AgentV(frame, config)
agent.wait_for_challenge()

input('Continue')
