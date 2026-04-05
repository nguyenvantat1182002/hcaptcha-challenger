from playwright.async_api import Page, expect, Response
from hcaptcha_challenger import AgentV, AgentConfig
from hcaptcha_challenger.models import ChallengeSignal
from contextlib import suppress


class AccountRiotGames:
    def __init__(self, page: Page, username: str, password: str):
        self.page = page
        self.username = username
        self.password = password

        agent_config = AgentConfig()
        self.agent = AgentV(page=self.page, agent_config=agent_config)

    async def login(self, retries: int = 3) -> dict:
        if retries < 1:
            return {}

        await self.page.goto('https://xsso.riotgames.com/login', referer='https://www.riotgames.com/')

        username_inpt = self.page.locator('input[name="username"]')
        await username_inpt.click()
        await username_inpt.fill(self.username)

        password_inpt = self.page.locator('input[name="password"]')
        await password_inpt.click()
        await password_inpt.fill(self.password)
        
        # await self.page.fill('input[name="username"]', self.username)
        # await self.page.fill('input[name="password"]', self.password)
        
        signin_btn = self.page.locator('button[data-testid="btn-signin-submit"]')
        await expect(signin_btn).to_be_enabled()
        await signin_btn.click()
        
        result = await self.agent.wait_for_challenge()
        if result != ChallengeSignal.SUCCESS:
            return await self.login(retries - 1)

        def login_response(response: Response) -> bool:
            url = 'https://authenticate.riotgames.com/api/v1/login'
            return response.url == url and response.request.method == 'PUT'
        
        with suppress(Exception):
            async with self.page.expect_response(login_response, timeout=10000) as response:
                value = await response.value
                result = await value.json()
                if 'success' in result:
                    return result
                    
        return {}
