"""Playwright tests: SSE connection + animation engine.

The EventBus has no background publisher in Phase 9, so SSE is tested
in two ways:
  1. Connection: verify the browser opens an EventSource to /events/{id}.
  2. Animations: call window._applyEvent() directly (exposed by avatar.js)
     and assert the correct CSS class is applied and removed.
"""

from playwright.sync_api import Page, expect


def _boot(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)


def test_sse_request_made_after_boot(page: Page, live_server: str) -> None:
    sse_urls: list[str] = []
    def _capture(r: object) -> None:
        url = getattr(r, "url", "")
        if "/events/" in url:
            sse_urls.append(url)

    page.on("request", _capture)
    _boot(page, live_server)
    page.wait_for_timeout(500)
    assert any("/events/" in url for url in sse_urls), "No SSE request was made"


def test_apply_event_hunger_warning(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.evaluate("window._applyEvent('hunger_warning')")
    expect(page.locator("#avatar")).to_have_class("anim--hunger-warn", timeout=500)
    page.wait_for_timeout(1300)
    classes = page.get_attribute("#avatar", "class") or ""
    assert "anim--hunger-warn" not in classes


def test_apply_event_hunger_critical(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.evaluate("window._applyEvent('hunger_critical')")
    expect(page.locator("#avatar")).to_have_class("anim--hunger-crit", timeout=500)


def test_apply_event_hygiene_warning(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.evaluate("window._applyEvent('hygiene_warning')")
    expect(page.locator("#avatar")).to_have_class("anim--hygiene-warn", timeout=500)


def test_apply_event_hygiene_critical(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.evaluate("window._applyEvent('hygiene_critical')")
    expect(page.locator("#avatar")).to_have_class("anim--hygiene-crit", timeout=500)


def test_apply_event_social_warning(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.evaluate("window._applyEvent('social_warning')")
    expect(page.locator("#avatar")).to_have_class("anim--social-warn", timeout=500)


def test_apply_event_social_critical(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.evaluate("window._applyEvent('social_critical')")
    expect(page.locator("#avatar")).to_have_class("anim--social-crit", timeout=500)


def test_apply_event_vampiric_advance(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.evaluate("window._applyEvent('vampiric_advance')")
    expect(page.locator("#avatar")).to_have_class("anim--vampiric-advance", timeout=500)


def test_apply_event_vampiric_retreat(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.evaluate("window._applyEvent('vampiric_retreat')")
    expect(page.locator("#avatar")).to_have_class("anim--vampiric-retreat", timeout=500)


def test_apply_event_level_up_ready(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.evaluate("window._applyEvent('level_up_ready')")
    expect(page.locator("#level-up-badge")).to_be_visible(timeout=500)


def test_unknown_event_kind_is_ignored(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    # Should not throw
    page.evaluate("window._applyEvent('totally_unknown_event_kind_xyz')")
    expect(page.locator("#view-main")).to_be_visible()
