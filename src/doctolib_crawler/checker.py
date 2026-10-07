from playwright.sync_api import Page

from doctolib_crawler.models import Doctor


def has_gkv_appointments(page: Page) -> bool:
    """Return True if the page appears to have usable GKV appointments."""

    # Get all visible text from the availability page
    page_text = page.locator("body").inner_text()

    # Ignore self-pay appointments shown to GKV patients
    if "Selbstzahlertermine" in page_text:
        return False

    # These messages indicate that no online appointment is available
    no_appointment_messages = [
        "Keine Termine online verfügbar",
        "Es ist momentan leider nicht möglich, diesen Termin online zu buchen.",
    ]

    for message in no_appointment_messages:
        if message in page_text:
            return False

    # The availability page itself is enough evidence that
    # there may be an appointment to check manually.
    return True


def check_appointments(page: Page, doctor: Doctor) -> bool:
    """Check whether GKV-covered appointments are available."""

    # 1. Open the doctor's Doctolib profile
    page.goto(doctor.url, wait_until="domcontentloaded")

    # Give the page time to load the booking elements
    page.wait_for_timeout(5000)

    # 2. Reject the cookie banner, if it is displayed
    cookie_button = page.locator("#didomi-notice-disagree-button")

    if cookie_button.count() > 0 and cookie_button.first.is_visible():
        cookie_button.first.click()

    # Give Doctolib time to update the page after dismissing cookies
    page.wait_for_timeout(3000)

    # 3. Click "Termin buchen"
    booking_links = page.locator(
        'a[aria-label="Termin buchen"]'
    )

    # Fallback if the aria-label is not available
    if booking_links.count() == 0:
        booking_links = page.get_by_role(
            "link",
            name="Termin buchen",
            exact=True,
        )

    booking_links.first.wait_for(
        state="visible",
        timeout=15000,
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

    # 4. Wait for Doctolib to enter the booking flow.
    # Different doctors can use different booking URLs.
    page.wait_for_url(
        "**/booking**",
        timeout=15000,
    )

    # The page can still be rendering after navigation.
    page.wait_for_timeout(5000)

    # 5.A Some practices ask for the medical specialty first.
    # For this practice, select "Frauenarzt / Gynäkologe".
    speciality_question = page.get_by_text(
        "Fachgebiet wählen",
        exact=True,
    )

    if (
        speciality_question.count() > 0
        and speciality_question.first.is_visible()
    ):
        page.get_by_text(
            "Frauenarzt / Gynäkologe",
            exact=True,
        ).click()

        # Give Doctolib time to load the next booking step
        page.wait_for_timeout(3000)   


    # 5.B Some doctors/practices ask whether we have visited
    # the doctor or practice before.
    # The wording varies between Doctolib booking flows.
    previous_visit_question = page.get_by_text(
        "bereits besucht?",
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

        # Give Doctolib time to load the next step
        page.wait_for_timeout(2000)


    # 6. Select the patient's insurance type
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

    # 7. Select the appointment type
    page.get_by_role(
        "button",
        name=doctor.appointment_type,
        exact=True,
    ).click()

    # Give the next page time to load
    page.wait_for_timeout(3000)

        # 8. Some group practices ask the patient to choose a doctor.
    # We accept any doctor by selecting "Ich habe keine Präferenz".
    doctor_preference = page.get_by_text(
        "Wählen Sie eine/n Ärzt:in oder Therapeut:in",
        exact=False,
    )

    if (
        doctor_preference.count() > 0
        and doctor_preference.first.is_visible()
    ):
        preference_option = page.get_by_text(
            "Ich habe keine Präferenz",
            exact=True,
        )

        preference_option.first.wait_for(
            state="visible",
            timeout=15000,
        )

        preference_option.first.click()

    # Give the availability page time to load
    page.wait_for_timeout(3000)

    # 9. Check whether GKV-covered appointments are available
    return has_gkv_appointments(page)
