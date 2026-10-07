from playwright.sync_api import Page
from doctolib_crawler.models import Doctor


def check_appointments(
    page: Page,
    doctor: Doctor,
) -> bool:
    """
    Check whether appointments are available for a doctor.

    Returns:
        True if appointments appear to be available.
        False if no appointments are available.
    """


    # 1. Open the doctor's profile
    page.goto(
        doctor.url,
        wait_until="domcontentloaded",
    )

    page.wait_for_timeout(5000)

    # 2. Reject cookies if the dialog is present
    cookie_button = page.locator(
        "#didomi-notice-disagree-button"
    )

    if cookie_button.count() > 0:
        cookie_button.first.click()

    # 3. Find the visible "Termin buchen" button
    booking_links = page.locator(
        'a[aria-label="Termin buchen"]').filter(visible=True)

    booking_links.wait_for(state="visible", timeout=4000)
    visible_booking_link = None

    for i in range(booking_links.count()):
        link = booking_links.nth(i)

        if link.is_visible():
            visible_booking_link = link
            break

    if visible_booking_link is None:
        raise RuntimeError(
            f"Could not find 'Termin buchen' for {doctor.name}."
        )

    visible_booking_link.click()

    # 4. Select statutory/public insurance
    statutory_button = page.get_by_role(
        "button",
        name="Gesetzlich versichert",
        exact=True,
    )

    statutory_button.wait_for(
        state="visible",
        timeout=15000,
    )

    statutory_button.click()

    # 5. Select new-patient appointment
    new_patient_button = page.get_by_role(
        "button",
        name="Erstuntersuchung Neupatient:in",
        exact=True,
    )

    new_patient_button.wait_for(
        state="visible",
        timeout=15000,
    )

    new_patient_button.click()

    # 6. Give Doctolib time to load the availability page
    page.wait_for_timeout(3000)

    # 7. Determine whether appointments are available
    body_text = page.locator("body").inner_text()

    no_appointments_text = (
        "Keine Termine online verfügbar"
    )

    if no_appointments_text in body_text:
        return False

    return True
