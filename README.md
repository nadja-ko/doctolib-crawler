# Doctolib Appointment Monitor

A Python-based appointment availability monitor for configured Doctolib profiles. It uses Playwright to navigate the booking flow, checks whether a profile appears to have potentially bookable appointments for the selected insurance type, and can send a Telegram notification.

> **Important:** This is an independent personal and portfolio project. It is not affiliated with, endorsed by, or supported by Doctolib. It does not book appointments. Notifications are prompts to open Doctolib and verify availability yourself.

## Features

- Reads provider profiles and booking preferences from a YAML configuration file.
- Uses Playwright to navigate the Doctolib booking flow in Chromium.
- Handles several observed booking-flow variations, including optional previous-visit questions and group-practice practitioner preferences.
- Selects the configured insurance type and exact appointment-type label.
- Filters pages explicitly marked as self-pay (`Selbstzahlertermine`) and pages containing known no-availability messages.
- Sends potential-availability notifications through the Telegram Bot API.
- Avoids repeated notifications for a profile while it remains flagged as potentially available, using a local JSON state file.
- Includes automated tests and Ruff linting.

## How it works

```text
YAML configuration
        |
        v
    main.py
        |
        v
  check_appointments()
        |
        v
 Playwright / Chromium
        |
        v
 Doctolib booking flow
        |
        v
 has_gkv_appointments()
        |
        +---- no potential availability ----> no alert
        |
        +---- potential availability --------> Telegram
                                               |
                                               v
                                      notification state
```

The implementation is intentionally browser-driven because Doctolib's booking flow is dynamic and can vary between profiles. The crawler does not attempt to complete a booking.

## Current limitations

- **Availability is heuristic.** The current checker excludes pages with known self-pay and no-availability messages. Other pages may be classified as potentially available. A notification is not proof that a suitable appointment can actually be booked.
- **Manual verification is required.** Open the profile link in the Telegram message and confirm the date, time, insurance coverage, appointment type, and eligibility before booking.
- **Doctolib's website can change.** Text labels, page structure, and booking URLs may change and require selector updates.
- **Booking flows vary.** Some practices ask whether the patient has visited before; some group practices ask for a practitioner preference; specialty selection may also be required for some profiles.
- **No automatic booking or patient login.** The project only checks public-facing booking flows and sends notifications.
- **No guarantee of availability.** Appointment slots can disappear between a check and manual verification.

## Requirements

- Python 3.13 (the project lockfile and deployment workflow should be kept aligned with the supported Python version).
- [uv](https://docs.astral.sh/uv/) for dependency and environment management.
- Playwright and Chromium, installed through the project dependencies and Playwright browser installer.
- A Telegram bot and chat ID if Telegram notifications are desired.

## Local setup

Clone the public repository:

```bash
git clone https://github.com/nadja-ko/doctolib-crawler.git
cd doctolib-crawler
```

Install dependencies and the Playwright browser:

```bash
uv sync --frozen
uv run playwright install chromium
```

Create a private local configuration from the example:

```bash
cp config/doctors.example.yaml config/doctors.yaml
```

Edit `config/doctors.yaml` with your own profiles. Do not commit this file.

Create a local `.env` file in the project root if Telegram notifications are required:

```dotenv
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Optional: use an already-installed browser instead of Playwright's Chromium.
# CHROME_EXECUTABLE_PATH=/path/to/Chrome
```

Do not commit `.env` or share its contents. The local `.env` is loaded by the application; the GitHub Actions deployment supplies the Telegram values as repository secrets instead.

Run the crawler:

```bash
uv run python main.py
```

Run tests and lint checks:

```bash
uv run pytest
uv run ruff check .
```

## Configuration

The real configuration is stored in `config/doctors.yaml`, which is ignored by Git. The public repository contains only `config/doctors.example.yaml`.

Example structure:

```yaml
doctors:
  - name: Example Doctor
    url: https://www.doctolib.de/...
    insurance: public
    appointment_type: "Exact appointment label shown by Doctolib"
```

Configuration notes:

- `name`: a descriptive label used in terminal output and Telegram messages.
- `url`: the provider's Doctolib profile URL.
- `insurance`: currently `public` or `private`.
- `appointment_type`: match the appointment label displayed by Doctolib. Wording and punctuation can differ between profiles.

The current configuration model and checker are primarily built around the initial gynaecology use case. Supporting additional specialties cleanly is a planned extension; see the roadmap below.

## Notifications and state

The Telegram integration is implemented in `src/doctolib_crawler/notifications/telegram.py`.

The local notification state is stored in:

```text
data/alerted_doctors.json
```

This file records the profile URLs for which a potential-availability notification has already been sent. It is runtime state, not source code, and is ignored by Git.

Expected behaviour:

1. If a profile is flagged as potentially available and has not been alerted, send a Telegram message and record its URL.
2. If the profile remains flagged as potentially available, suppress duplicate notifications.
3. If a successful check returns `False`, remove the URL from the alerted set. A later transition back to potential availability can then trigger a new alert.
4. If the check raises an exception, preserve the previous alert state. An inaccessible page is **unknown**, not proof that appointments have disappeared.

Because the availability detector is heuristic, the state-reset behaviour depends on its result. The detector should be strengthened with explicit available/unavailable/unknown outcomes before relying on it as a precise slot tracker.

## Project structure

```text
doctolib-crawler/
├── config/
│   └── doctors.example.yaml
├── src/
│   └── doctolib_crawler/
│       ├── __init__.py
│       ├── checker.py
│       ├── config.py
│       ├── models.py
│       ├── state.py
│       └── notifications/
│           ├── __init__.py
│           └── telegram.py
├── tests/
├── main.py
├── pyproject.toml
├── uv.lock
├── .gitignore
└── README.md
```

The exact set of modules may evolve as the project is refactored.

## Privacy and responsible use

- Never commit `.env`, `config/doctors.yaml`, Telegram tokens, chat IDs, or personal notification state to the public repository.
- Keep personal deployment configuration in the separate private `doctolib-crawler-runner` repository.
- Do not put real doctor names or profile URLs into public test fixtures, screenshots, example output, or issue reports without a good reason.
- Use a conservative checking frequency and respect the website's terms and technical controls. Do not attempt to bypass authentication, CAPTCHAs, rate limits, or access restrictions.
- This project is for personal monitoring and learning. Users must verify availability and make bookings themselves.

## Development and CI ideas

The public repository is the source-code and portfolio project. A useful continuous-integration workflow can run on pushes and pull requests to:

- install the locked dependencies with `uv sync --frozen`;
- run `ruff check`;
- run `pytest`;
- optionally measure test coverage;
- run static security analysis (for example, GitHub CodeQL for Python and GitHub Actions workflows).

Tests should use mocked pages or saved, sanitised HTML fixtures rather than making live booking requests to real profiles. Dependency updates should be reviewed before merging.

## Roadmap

- Add explicit `AVAILABLE`, `UNAVAILABLE`, and `UNKNOWN` checker outcomes to avoid treating page errors or unexpected layouts as availability changes.
- Improve availability detection using the actual appointment-slot elements and sanitised DOM fixtures.
- Add structured per-profile error reporting and a concise GitHub Actions job summary.
- Add CI for Ruff, pytest, coverage, dependency updates, and static analysis.
- Generalise the configuration and domain model from `Doctor` to a provider/appointment target so other specialties can be configured without hard-coded gynaecology assumptions.
- Add more booking-flow fixtures for specialty selection, group practices, and new-patient variants.

## Disclaimer

This project is provided for educational and personal use. It is an unofficial automation tool and may stop working if Doctolib changes its website. It does not provide medical advice, guarantee appointment availability, or perform bookings.
