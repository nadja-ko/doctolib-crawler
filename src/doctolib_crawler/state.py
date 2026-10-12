import json
from pathlib import Path


def load_alerted_doctors(path: Path) -> set[str]:
    """Load the URLs of doctors we have already notified about."""

    if not path.exists():
        return set()

    data = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(data, list) or not all(
        isinstance(url, str) for url in data
    ):
        raise ValueError("Invalid notification state file.")

    return set(data)


def save_alerted_doctors(
    path: Path,
    alerted_doctors: set[str],
) -> None:
    """Save the URLs of doctors we have already notified about."""

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(sorted(alerted_doctors), indent=2) + "\n",
        encoding="utf-8",
    )
    