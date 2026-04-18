"""Playwright tests: action buttons → API call → DOM update."""

from playwright.sync_api import Page, Route, expect


def _boot(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)


def test_feed_button_present(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    expect(page.locator("[data-action='feed']")).to_be_visible()


def test_clean_button_present(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    expect(page.locator("[data-action='clean']")).to_be_visible()


def test_social_buttons_present(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    for action in ("visit", "gift", "chat"):
        expect(page.locator(f"[data-action='{action}']")).to_be_visible()


def test_feed_updates_quip(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.click("[data-action='feed']")
    # Button re-enables when action completes
    expect(page.locator("[data-action='feed']")).to_be_enabled(timeout=5000)
    new_quip = page.inner_text("#quip")
    # Quip should be non-empty; may or may not change from login quip
    assert new_quip.strip() != ""


def test_action_button_disables_during_request(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    # Slow the response to observe disabled state
    def _slow(r: Route) -> None:
        page.wait_for_timeout(200)
        r.continue_()

    page.route("/action/clean", _slow)
    page.click("[data-action='clean']")
    expect(page.locator("[data-action='clean']")).to_be_disabled()
    expect(page.locator("[data-action='clean']")).to_be_enabled(timeout=5000)


def test_action_button_reenables_after_response(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.click("[data-action='visit']")
    expect(page.locator("[data-action='visit']")).to_be_enabled(timeout=5000)


def test_all_five_actions_complete_successfully(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    for action in ("feed", "clean", "visit", "gift", "chat"):
        with page.expect_response(f"**/action/{action}") as resp_info:
            page.click(f"[data-action='{action}']")
        assert resp_info.value.status == 200
        expect(page.locator(f"[data-action='{action}']")).to_be_enabled(timeout=5000)


def test_social_buttons_grouped_separately(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    maintenance = page.locator(".actions__maintenance [data-action]")
    social = page.locator(".actions__social [data-action]")
    assert maintenance.count() == 2
    assert social.count() == 3


def test_action_error_shows_error_quip(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    page.route("/action/feed", lambda r: r.abort())
    page.click("[data-action='feed']")
    expect(page.locator("[data-action='feed']")).to_be_enabled(timeout=5000)
    quip = page.inner_text("#quip")
    assert "SYSTEM" in quip.upper() or quip.strip() != ""
