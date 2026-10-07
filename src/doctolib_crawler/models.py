from dataclasses import dataclass


@dataclass
class Doctor:
    name: str
    url: str
    insurance: str
    appointment_type: str
    