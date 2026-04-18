"""Playwright tests: POST /session/open → correct DOM state."""

from playwright.sync_api import Page, expect


def test_main_view_shown_after_boot(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    expect(page.locator("#view-loading")).to_be_hidden()
    expect(page.locator("#view-error")).to_be_hidden()


def test_avatar_element_has_stage_attribute(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    stage = page.get_attribute("#avatar", "data-stage")
    assert stage is not None
    assert stage != ""


def test_hunger_meter_has_width(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    width = page.eval_on_selector(
        "#meter-hunger", "el => el.style.width"
    )
    assert width is not None
    assert width != "0%"


def test_hygiene_meter_has_width(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    width = page.eval_on_selector(
        "#meter-hygiene", "el => el.style.width"
    )
    assert width is not None
    assert width != "0%"


def test_quip_is_populated(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    quip = page.inner_text("#quip")
    assert quip.strip() != ""


def test_avatar_id_stored_in_localstorage(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    stored = page.evaluate("localStorage.getItem('sender-frenz-avatar-id')")
    assert stored is not None
    # Should be a valid UUID
    import re
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        stored,
    )


def test_second_visit_reuses_avatar_id(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    first_id = page.evaluate("localStorage.getItem('sender-frenz-avatar-id')")

    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)
    second_id = page.evaluate("localStorage.getItem('sender-frenz-avatar-id')")

    assert first_id == second_id
