import asyncio
import json

# uv pip install -U camoufox
from browserforge.fingerprints import Screen
from camoufox import AsyncCamoufox
from playwright.async_api import Page

from hcaptcha_challenger import AgentV, AgentConfig, CaptchaResponse
from riotgames import AccountRiotGames


async def challenge(page: Page) -> AgentV:
    """Automates the process of solving an hCaptcha challenge."""
    # [IMPORTANT] Initialize the Agent before triggering hCaptcha
    agent_config = AgentConfig()
    agent = AgentV(page=page, agent_config=agent_config)

    # In your real-world workflow, you may need to replace the `click_checkbox()`
    # It may be to click the Login button or the Submit button to a trigger challenge
    # await agent.robotic_arm.click_checkbox()

    # Wait for the challenge to appear and be ready for solving
    await agent.wait_for_challenge()

    return agent
    

# noinspection DuplicatedCode
async def main():
    # 1. Danh sách các domains gốc muốn đi qua proxy (tự động khớp cả subdomain)
    proxy_domains = ["authenticate.riotgames.com", "hcaptcha.com"]
    proxy_server = "gw.dataimpulse.com:823"
    
    # Thông tin đăng nhập proxy (Cần thiết để Playwright xử lý xác thực)
    proxy_auth = {
        'username': '147cb5ab145f6f60ba2a__cr.sg,in',
        'password': '110cdd5fa124476f'
    }

    # 2. Tạo logic PAC động dựa trên danh sách trên
    def generate_pac_data_uri(domains, server):
        import base64
        # Kiểm tra host chính xác OR là subdomain của nó
        # Ví dụ: (host == "example.com" || dnsDomainIs(host, ".example.com"))
        conditions = " || ".join([f'(host == "{d}" || dnsDomainIs(host, ".{d}"))' for d in domains])
        
        pac_script = f"""
        function FindProxyForURL(url, host) {{
            if ({conditions}) {{
                return "PROXY {server}";
            }}
            return "DIRECT";
        }}
        """
        pac_base64 = base64.b64encode(pac_script.encode()).decode()
        return f"data:application/x-ns-proxy-autoconfig;base64,{pac_base64}"

    user_prefs = {
        'network.proxy.type': 2,
        'network.proxy.autoconfig_url': generate_pac_data_uri(proxy_domains, proxy_server)
    }

    # 3. Khởi tạo Fingerprint tối ưu (Duy trì tính nhất quán cho profile)
    from hcaptcha_challenger.fingerprint import get_optimized_fingerprint_config
    
    user_data_dir = "tmp/.cache/camoufox"
    fingerprint_config = get_optimized_fingerprint_config(
        user_data_dir=user_data_dir,
        use_persistence=True
    )

    async with AsyncCamoufox(
        persistent_context=True,
        user_data_dir=user_data_dir,
        **fingerprint_config,
        screen=Screen(max_width=1920, max_height=1080),
        humanize=0.1,
        geoip=True,
        # Vẫn truyền proxy dict để Playwright xử lý Username/Password Authentication tự động
        proxy={
            'server': f"http://{proxy_server}",
            **proxy_auth
        },
        firefox_user_prefs=user_prefs
    ) as browser:
        page = browser.pages[-1] if hasattr(browser, "pages") and browser.pages else await browser.new_page()
        
        arg = AccountRiotGames(page, 'OwYlb8C4yz80e', '1dW9doaf9z$@#')
        
        result = await arg.login()
        print(result)
        
        input('Quit')

if __name__ == "__main__":
    asyncio.run(main())
