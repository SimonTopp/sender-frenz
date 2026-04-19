"""Playwright tests: install prompt banner."""

from playwright.sync_api import Browser, Page, expect

_IOS_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


def _boot(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)


def test_visit_count_increments_on_first_visit(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    count = page.evaluate("localStorage.getItem('sender-frenz-visit-count')")
    assert count == "1"


def test_visit_count_increments_on_second_visit(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    _boot(page, live_server)
    count = page.evaluate("localStorage.getItem('sender-frenz-visit-count')")
    assert count == "2"


def test_install_banner_hidden_on_first_visit(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    expect(page.locator("#install-banner")).to_be_hidden()


def test_ios_banner_shown_on_second_visit(
    browser: Browser, live_server: str
) -> None:
    ctx = browser.new_context(user_agent=_IOS_UA)
    page = ctx.new_page()
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    expect(page.locator("#install-banner")).to_be_visible()
    ctx.close()


def test_ios_banner_shows_share_instructions(
    browser: Browser, live_server: str
) -> None:
    ctx = browser.new_context(user_agent=_IOS_UA)
    page = ctx.new_page()
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    msg = page.inner_text("#install-banner-msg")
    assert "Add to Home Screen" in msg
    ctx.close()


def test_dismiss_hides_banner(browser: Browser, live_server: str) -> None:
    ctx = browser.new_context(user_agent=_IOS_UA)
    page = ctx.new_page()
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    page.click("#btn-dismiss-install")
    expect(page.locator("#install-banner")).to_be_hidden()
    ctx.close()


def test_dismissed_banner_stays_hidden_on_reload(
    browser: Browser, live_server: str
) -> None:
    ctx = browser.new_context(user_agent=_IOS_UA)
    page = ctx.new_page()
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    page.click("#btn-dismiss-install")
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    expect(page.locator("#install-banner")).to_be_hidden()
    ctx.close()
