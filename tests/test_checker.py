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
    