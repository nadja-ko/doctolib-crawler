
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from doctolib_crawler.checker import (
    AvailabilityStatus,
    check_appointments,
)
from doctolib_crawler.config import load_doctors
from doctolib_crawler.logging_config import configure_logging
from doctolib_crawler.notifications.telegram import (
    send_telegram_message,
)
from doctolib_crawler.state import (
    load_alerted_doctors,
    save_alerted_doctors,
)

CONFIG_PATH = Path("config/doctors.yaml")
STATE_PATH = Path("data/alerted_doctors.json")

logger = logging.getLogger(__name__)


def main() -> None:
    load_dotenv()
    configure_logging()

    logger.info("Starting Doctolib crawler.")

    doctors = load_doctors(CONFIG_PATH)
    alerted_doctors = load_alerted_doctors(STATE_PATH)

    summary = {
        "checked": 0,
        "available": 0,
        "unavailable": 0,
        "unknown": 0,
        "errors": 0,
        "notifications_sent": 0,
        "notification_errors": 0,
        "state_errors": 0,
    }

    with sync_playwright() as playwright:
        chrome_executable_path = os.getenv(
            "CHROME_EXECUTABLE_PATH"
        )

        if chrome_executable_path:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=chrome_executable_path,
            )
        else:
            browser = playwright.chromium.launch(
                headless=True,
            )

        page = browser.new_page(
            viewport={"width": 1440, "height": 900}
        )

        try:
            for doctor in doctors:
                summary["checked"] += 1

                logger.info(
                    "Checking doctor: %s | URL: %s",
                    doctor.name,
                    doctor.url,
                )

                # Check one doctor without stopping the remaining checks.
                try:
                    status = check_appointments(
                        page=page,
                        doctor=doctor,
                    )

                except Exception:
                    summary["unknown"] += 1
                    summary["errors"] += 1

                    # Keep the previous notification state unchanged.
                    logger.exception(
                        "Doctor check failed: %s. "
                        "Availability is UNKNOWN; alert history preserved.",
                        doctor.name,
                    )
                    continue

                # A. Appointments appear to be available.
                if status == AvailabilityStatus.AVAILABLE:
                    summary["available"] += 1

                    logger.info(
                        "Potential appointments detected: %s",
                        doctor.name,
                    )

                    if doctor.url in alerted_doctors:
                        logger.info(
                            "Duplicate notification suppressed: %s",
                            doctor.name,
                        )
                        continue

                    # Send the Telegram notification.
                    try:
                        send_telegram_message(
                            f"🚨 Potential appointment available!\n\n"
                            f"Doctor: {doctor.name}\n"
                            f"URL: {doctor.url}"
                        )

                    except Exception:
                        summary["notification_errors"] += 1

                        logger.exception(
                            "Telegram notification failed: %s",
                            doctor.name,
                        )
                        continue

                    summary["notifications_sent"] += 1

                    # Remember the doctor after Telegram succeeds.
                    alerted_doctors.add(doctor.url)

                    try:
                        save_alerted_doctors(
                            STATE_PATH,
                            alerted_doctors,
                        )

                        logger.info(
                            "Notification state saved: %s",
                            doctor.name,
                        )

                    except Exception:
                        summary["state_errors"] += 1

                        logger.exception(
                            "Telegram was sent, but notification state "
                            "could not be saved: %s",
                            doctor.name,
                        )

                # B. The calendar loaded and showed no available slots.
                elif status == AvailabilityStatus.UNAVAILABLE:
                    summary["unavailable"] += 1

                    logger.info(
                        "No appointments available: %s",
                        doctor.name,
                    )

                    # Reset the alert so future appointments can trigger
                    # a new notification.
                    if doctor.url in alerted_doctors:
                        alerted_doctors.remove(doctor.url)

                        try:
                            save_alerted_doctors(
                                STATE_PATH,
                                alerted_doctors,
                            )

                            logger.info(
                                "Notification status reset: %s",
                                doctor.name,
                            )

                        except Exception:
                            # Restore the in-memory state if saving failed.
                            alerted_doctors.add(doctor.url)
                            summary["state_errors"] += 1

                            logger.exception(
                                "Could not reset notification state: %s",
                                doctor.name,
                            )

                # C. The page loaded, but availability was inconclusive.
                elif status == AvailabilityStatus.UNKNOWN:
                    summary["unknown"] += 1

                    logger.warning(
                        "Availability UNKNOWN for %s. "
                        "Previous notification state preserved.",
                        doctor.name,
                    )

                else:
                    summary["unknown"] += 1

                    logger.error(
                        "Unexpected availability status for %s: %r. "
                        "Previous notification state preserved.",
                        doctor.name,
                        status,
                    )

        finally:
            browser.close()

    # Final run summary.
    logger.info(
        "RUN SUMMARY | checked=%d | available=%d | "
        "unavailable=%d | unknown=%d | errors=%d | "
        "notifications_sent=%d | notification_errors=%d | "
        "state_errors=%d",
        summary["checked"],
        summary["available"],
        summary["unavailable"],
        summary["unknown"],
        summary["errors"],
        summary["notifications_sent"],
        summary["notification_errors"],
        summary["state_errors"],
    )

    logger.info("Doctolib crawler finished.")


if __name__ == "__main__":
    main()
