"""Playwright tests: level-up badge and upgrade picker."""

from playwright.sync_api import Page, expect


def _boot(page: Page, live_server: str) -> None:
    page.goto(live_server)
    expect(page.locator("#view-main")).to_be_visible(timeout=6000)


def _force_badge_visible(page: Page) -> None:
    """Show the level-up badge without requiring an eligible avatar."""
    page.evaluate(
        "document.getElementById('level-up-badge').classList.remove('level-up-badge--hidden')"
    )


def test_level_up_badge_hidden_for_new_avatar(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    expect(page.locator("#level-up-badge")).to_be_hidden()


def test_level_up_picker_opens_on_badge_click(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    _force_badge_visible(page)
    page.click("#level-up-badge")
    expect(page.locator("#view-level-up")).to_be_visible(timeout=4000)
    expect(page.locator("#view-main")).to_be_hidden()


def test_level_up_picker_shows_skin_options(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    _force_badge_visible(page)
    page.click("#level-up-badge")
    expect(page.locator("#view-level-up")).to_be_visible(timeout=4000)
    count = page.locator("#skin-options .option-card").count()
    assert count > 0


def test_level_up_picker_shows_room_options(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    _force_badge_visible(page)
    page.click("#level-up-badge")
    expect(page.locator("#view-level-up")).to_be_visible(timeout=4000)
    count = page.locator("#room-options .option-card").count()
    assert count > 0


def test_confirm_disabled_until_both_selected(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    _force_badge_visible(page)
    page.click("#level-up-badge")
    expect(page.locator("#view-level-up")).to_be_visible(timeout=4000)
    expect(page.locator("#btn-confirm-level-up")).to_be_disabled()

    page.locator("#skin-options .option-card").first.click()
    expect(page.locator("#btn-confirm-level-up")).to_be_disabled()

    page.locator("#room-options .option-card").first.click()
    expect(page.locator("#btn-confirm-level-up")).to_be_enabled()


def test_back_button_returns_to_main(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    _force_badge_visible(page)
    page.click("#level-up-badge")
    expect(page.locator("#view-level-up")).to_be_visible(timeout=4000)

    page.click("#btn-cancel-level-up")
    expect(page.locator("#view-main")).to_be_visible(timeout=3000)
    expect(page.locator("#view-level-up")).to_be_hidden()


def test_option_card_gets_selected_class(page: Page, live_server: str) -> None:
    _boot(page, live_server)
    _force_badge_visible(page)
    page.click("#level-up-badge")
    expect(page.locator("#view-level-up")).to_be_visible(timeout=4000)

    first_skin = page.locator("#skin-options .option-card").first
    first_skin.click()
    expect(first_skin).to_have_class("option-card option-card--selected")
