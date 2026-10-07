from playwright.sync_api import Page

from doctolib_crawler.models import Doctor


def has_gkv_appointments(page: Page) -> bool:
    """Return True if GKV-covered appointment slots are available."""

    page_text = page.locator("body").inner_text()

    if "Selbstzahlertermine" in page_text:
        return False

    buttons = page.get_by_role("button")

    for i in range(buttons.count()):
        button = buttons.nth(i)

        if not button.is_visible():
            continue

        text = button.inner_text().strip()

        if len(text) == 5 and text[2] == ":":
            if text[:2].isdigit() and text[3:].isdigit():
                return True

    return False


def check_appointments(page: Page, doctor: Doctor) -> bool:
    """Check whether GKV-covered appointments are available."""

    page.goto(doctor.url, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    cookie_button = page.locator("#didomi-notice-disagree-button")

    if cookie_button.count() > 0 and cookie_button.first.is_visible():
        cookie_button.first.click()

    booking_links = page.locator(
        'a[aria-label="Termin buchen"]'
    )

    for i in range(booking_links.count()):
        link = booking_links.nth(i)

        if link.is_visible():
            link.click()
            break
    else:
        raise RuntimeError(
            f'Could not find "Termin buchen" for {doctor.name}.'
        )

    page.wait_for_url(
        "**/booking/new-patient**",
        timeout=15000,
    )

    previous_visit_question = page.get_by_text(
        "Haben Sie diese:n Ärzt:in/Therapeut:in bereits besucht?",
        exact=False,
    )

    if (
        previous_visit_question.count() > 0
        and previous_visit_question.first.is_visible()
    ):
        page.get_by_role(
            "button",
            name="Nein",
            exact=True,
        ).click()

    if doctor.insurance == "public":
        insurance_name = "Gesetzlich versichert"
    elif doctor.insurance == "private":
        insurance_name = "Privat versichert"
    else:
        raise ValueError(
            f"Unknown insurance type: {doctor.insurance}"
        )

    page.get_by_role(
        "button",
        name=insurance_name,
        exact=True,
    ).click()

    page.get_by_role(
        "button",
        name=doctor.appointment_type,
        exact=True,
    ).click()

    page.wait_for_timeout(3000)

    return has_gkv_appointments(page)
