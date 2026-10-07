from pathlib import Path

from doctolib_crawler.config import load_doctors


def test_load_doctors() -> None:
    config_path = Path("config/doctors.example.yaml")

    doctors = load_doctors(config_path)

    assert len(doctors) == 1

    doctor = doctors[0]

    assert doctor.name == "Example Doctor"
    assert doctor.url == "https://example.com/doctor"
    assert doctor.insurance == "public"
    assert doctor.appointment_type == "Example appointment"
    