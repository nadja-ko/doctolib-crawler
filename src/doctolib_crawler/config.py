from pathlib import Path

import yaml

from doctolib_crawler.models import Doctor


def load_doctors(config_path: Path) -> list[Doctor]:
    """Load doctors from a YAML configuration file."""

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return [
        Doctor(
            name=doctor["name"],
            url=doctor["url"],
            insurance=doctor["insurance"],
            appointment_type=doctor["appointment_type"],
        )
        for doctor in data["doctors"]
    ]
