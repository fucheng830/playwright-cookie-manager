"""Playwright-based login helper."""
import asyncio, logging

logger = logging.getLogger(__name__)

PLATFORM_LOGIN_URLS = {
    "x": "https://x.com/login",
    "xhs": "https://www.xiaohongshu.com",
    "douyin": "https://www.douyin.com",
    "kuaishou": "https://www.kuaishou.com",
    "bilibili": "https://www.bilibili.com",
    "wechat": "https://channels.weixin.qq.com",
}

PLATFORM_LOGIN_DETECTORS = {
    "x": "auth_token",
    "xhs": "web_session",
    "douyin": "sessionid",
    "kuaishou": "kuaishou.api_st",
    "bilibili": "SESSDATA",
    "wechat": "token",
}


async def login_platform(platform: str, headless: bool = False, timeout: int = 180000) -> dict:
    """Open browser for user to login, capture storage_state. Returns the storage_state dict."""
    from playwright.async_api import async_playwright

    url = PLATFORM_LOGIN_URLS.get(platform, f"https://www.{platform}.com")
    cookie_name = PLATFORM_LOGIN_DETECTORS.get(platform, "session")

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=headless)
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto(url)
    logger.info(f"Please login to {platform} in the opened browser window...")

    try:
        # Wait until the auth cookie appears
        start = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start) * 1000 < timeout:
            cookies = await context.cookies()
            if any(c.get("name") == cookie_name for c in cookies):
                logger.info(f"Login detected for {platform}")
                break
            await asyncio.sleep(1)
        else:
            logger.warning(f"Login timeout for {platform}")
    except Exception as e:
        logger.error(f"Login wait error: {e}")

    state = await context.storage_state()
    await context.close()
    await browser.close()
    await pw.stop()

    return state
