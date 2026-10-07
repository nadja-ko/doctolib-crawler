from doctolib_crawler.checker import has_appointments 
from doctolib_crawler.models import Doctor
 

def test_doctor_creation() -> None:
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


def test_has_appointments_returns_false_when_no_appointments() -> None:
    body_text = """
    Es ist momentan leider nicht möglich, diesen Termin online zu buchen.
    Keine Termine online verfügbar
    """

    assert has_appointments(body_text) is False

def test_has_appointments_returns_true_when_appointments_exist() -> None:
    body_text = """
    Termine verfügbar
    Mittwoch, 14. Oktober
    10:30
    11:00
    """

    assert has_appointments(body_text) is True
        