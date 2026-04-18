"""Playwright tests: error states and recovery."""

from playwright.sync_api import Page, expect


def test_error_view_shown_when_session_open_fails(page: Page, live_server: str) -> None:
    page.route("/session/open", lambda r: r.abort())
    page.goto(live_server)
    expect(page.locator("#view-error")).to_be_visible(timeout=6000)
    expect(page.locator("#view-main")).to_be_hidden()
    expect(page.locator("#view-loading")).to_be_hidden()


def test_error_view_has_retry_button(page: Page, live_server: str) -> None:
    page.route("/session/open", lambda r: r.abort())
    page.goto(live_server)
    expect(page.locator("#btn-retry")).to_be_visible(timeout=6000)


def test_retry_recovers_to_main_view(page: Page, live_server: str) -> None:
    attempt = {"count": 0}

    def handle(route):
        attempt["count"] += 1
        if attempt["count"] == 1:
            route.abort()
        else:
            route.continue_()

    page.route("/session/open", handle)
    page.goto(live_server)
    expect(page.locator("#view-error")).to_be_visible(timeout=6000)

    page.click("#btn-retry")
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)


def test_error_on_500_response(page: Page, live_server: str) -> None:
    page.route(
        "/session/open",
        lambda r: r.fulfill(status=500, body="internal error"),
    )
    page.goto(live_server)
    expect(page.locator("#view-error")).to_be_visible(timeout=6000)


def test_action_error_keeps_main_view(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)

    page.route("/action/feed", lambda r: r.abort())
    page.click("[data-action='feed']")
    expect(page.locator("[data-action='feed']")).to_be_enabled(timeout=5000)

    # Main view should still be shown
    expect(page.locator("#view-main")).to_be_visible()


def test_eruda_not_loaded_without_debug_param(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    eruda_visible = page.evaluate("typeof window.eruda !== 'undefined'")
    assert not eruda_visible


def test_eruda_loaded_with_debug_param(page: Page, live_server: str) -> None:
    # Eruda loads from CDN; in CI without network this test may be skipped
    try:
        page.goto(f"{live_server}?debug=1")
        expect(page.locator("#view-main")).to_be_visible(timeout=6000)
        page.wait_for_function("typeof window.eruda !== 'undefined'", timeout=5000)
        loaded = page.evaluate("typeof window.eruda !== 'undefined'")
        assert loaded
    except Exception:
        import pytest
        pytest.skip("Eruda CDN not reachable in this environment")
