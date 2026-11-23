
import logging
import re
from enum import StrEnum

from playwright.sync_api import Page

from doctolib_crawler.models import Doctor

logger = logging.getLogger(__name__)


class AvailabilityStatus(StrEnum):
    """Possible outcomes of an appointment availability check."""

    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


CALENDAR_HEADING = "Wählen Sie das Datum für den Termin"

NO_APPOINTMENT_MESSAGES = [
    "Keine Termine online verfügbar",
    "Es ist momentan leider nicht möglich, diesen Termin online zu buchen.",
]

APPOINTMENT_TIME_PATTERN = re.compile(
    r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b"
)

WEEKDAY_PATTERN = re.compile(
    r"\b(?:Montag|Dienstag|Mittwoch|Donnerstag|"
    r"Freitag|Samstag|Sonntag)\b",
    re.IGNORECASE,
)


def get_gkv_availability(page: Page) -> AvailabilityStatus:
    """Classify GKV appointment availability from the calendar page."""

    page_text = page.locator("body").inner_text()
    normalized_text = " ".join(page_text.split())
    normalized_lower = normalized_text.casefold()

    # 1. Self-pay slots are not useful for a GKV patient.
    if "selbstzahlertermine" in normalized_lower:
        logger.info("Only self-pay appointments detected.")
        return AvailabilityStatus.UNAVAILABLE

    # 2. Check for explicit no-availability messages.
    for message in NO_APPOINTMENT_MESSAGES:
        if message.casefold() in normalized_lower:
            logger.info("Doctolib explicitly reports no availability.")
            return AvailabilityStatus.UNAVAILABLE

    # 3. Identify the actual appointment calendar.
    calendar_heading_lower = CALENDAR_HEADING.casefold()

    calendar_start = normalized_lower.find(calendar_heading_lower)

    if calendar_start == -1:
        logger.warning(
            "Expected appointment calendar heading not found."
        )
        return AvailabilityStatus.UNKNOWN

    calendar_text = normalized_text[
        calendar_start + len(CALENDAR_HEADING):
    ]

    # Ignore the practice and appointment details below the calendar.
    details_marker = "Ihre Termindetails"
    details_position = calendar_text.casefold().find(
        details_marker.casefold()
    )

    if details_position != -1:
        calendar_text = calendar_text[:details_position]

    # 4. Look for actual appointment times.
    if APPOINTMENT_TIME_PATTERN.search(calendar_text):
        logger.info("Appointment times detected in calendar.")
        return AvailabilityStatus.AVAILABLE

    # 5. A rendered calendar with dates but no times means that
    # no appointment slots are currently displayed.
    if WEEKDAY_PATTERN.search(calendar_text):
        logger.info("Calendar loaded, but no appointment times found.")
        return AvailabilityStatus.UNAVAILABLE

    # 6. Calendar structure is unexpected or incomplete.
    logger.warning(
        "Calendar heading found, but no recognizable dates or times."
    )
    return AvailabilityStatus.UNKNOWN


def check_appointments(
    page: Page,
    doctor: Doctor,
) -> AvailabilityStatus:
    """Navigate through Doctolib and check appointment availability."""

    # 1. Open the doctor's Doctolib profile
    page.goto(doctor.url, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    # 2. Reject the cookie banner, if displayed
    cookie_button = page.locator("#didomi-notice-disagree-button")

    if cookie_button.count() > 0 and cookie_button.first.is_visible():
        cookie_button.first.click()

    page.wait_for_timeout(3000)

    # 3. Click "Termin buchen"
    booking_links = page.locator(
        'a[aria-label="Termin buchen"]'
    )

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
    page.wait_for_url(
        "**/booking**",
        timeout=15000,
    )

    page.wait_for_timeout(5000)

    # 5.A Some practices ask for the medical specialty first.
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

        page.wait_for_timeout(3000)

    # 5.B Some practices ask whether the patient has visited before.
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

        page.wait_for_timeout(2000)

    # 6. Select the patient's insurance type.
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

    # 7. Select the appointment type.
    page.get_by_role(
        "button",
        name=doctor.appointment_type,
        exact=True,
    ).click()

    page.wait_for_timeout(3000)

    # 8. Some group practices ask the patient to choose a doctor.
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

    page.wait_for_timeout(3000)

    # 9. Classify the availability page.
    return get_gkv_availability(page)
