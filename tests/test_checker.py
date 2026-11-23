from unittest.mock import MagicMock

from doctolib_crawler.checker import (
    AvailabilityStatus,
    get_gkv_availability,
)
from doctolib_crawler.models import Doctor


def create_mock_page(body_text: str) -> MagicMock:
    """Create a mock Playwright page containing specified text."""

    page = MagicMock()
    page.locator.return_value.inner_text.return_value = body_text

    return page


def test_doctor_creation() -> None:
    """Test creating a Doctor instance."""

    doctor = Doctor(
        name="Example Doctor",
        url="https://example.com/doctor",
        insurance="public",
        appointment_type="Example appointment",
    )

    assert doctor.name == "Example Doctor"
    assert doctor.url == "https://example.com/doctor"
    assert doctor.insurance == "public"
    assert doctor.appointment_type == "Example appointment"


def test_returns_available_when_appointment_times_exist() -> None:
    """Detect appointment times in a rendered calendar."""

    body_text = """
    Wählen Sie das Datum für den Termin

    Mittwoch, 9. Dezember 2026
    11:00
    11:20
    11:40

    Ihre Termindetails
    Frauenarzt / Gynäkologe
    """

    page = create_mock_page(body_text)

    assert (
        get_gkv_availability(page)
        == AvailabilityStatus.AVAILABLE
    )


def test_returns_unavailable_when_no_appointments_exist() -> None:
    """Detect an explicit no-availability message."""

    body_text = """
    Es ist momentan leider nicht möglich,
    diesen Termin online zu buchen.
    Keine Termine online verfügbar
    """

    page = create_mock_page(body_text)

    assert (
        get_gkv_availability(page)
        == AvailabilityStatus.UNAVAILABLE
    )


def test_returns_unavailable_for_self_pay_appointments() -> None:
    """Ignore self-pay slots shown to GKV patients."""

    body_text = """
    Wählen Sie das Datum für den Termin

    Mittwoch, 9. Dezember 2026
    Sie sehen Selbstzahlertermine.
    11:00
    11:20
    """

    page = create_mock_page(body_text)

    assert (
        get_gkv_availability(page)
        == AvailabilityStatus.UNAVAILABLE
    )


def test_returns_unavailable_when_calendar_has_no_times() -> None:
    """Treat a rendered calendar with dates but no slots as unavailable."""

    body_text = """
    Wählen Sie das Datum für den Termin

    Mittwoch, 9. Dezember 2026
    Donnerstag, 10. Dezember 2026
    Freitag, 11. Dezember 2026

    Ihre Termindetails
    """

    page = create_mock_page(body_text)

    assert (
        get_gkv_availability(page)
        == AvailabilityStatus.UNAVAILABLE
    )


def test_returns_unknown_when_calendar_heading_is_missing() -> None:
    """Do not assume availability or unavailability on an unexpected page."""

    body_text = """
    Doctolib
    Einloggen
    Something unexpected happened.
    """

    page = create_mock_page(body_text)

    assert (
        get_gkv_availability(page)
        == AvailabilityStatus.UNKNOWN
    )


def test_returns_unknown_when_calendar_is_incomplete() -> None:
    """A heading without recognizable dates or appointment times is unknown."""

    body_text = """
    Wählen Sie das Datum für den Termin

    Loading...
    Bitte warten.
    """

    page = create_mock_page(body_text)

    assert (
        get_gkv_availability(page)
        == AvailabilityStatus.UNKNOWN
    )
