import os
from pathlib import Path

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

from doctolib_crawler.checker import check_appointments
from doctolib_crawler.config import load_doctors
from doctolib_crawler.notifications.telegram import (
    send_telegram_message,
)
from doctolib_crawler.state import (
    load_alerted_doctors,
    save_alerted_doctors,
)

CONFIG_PATH = Path("config/doctors.yaml")
STATE_PATH = Path("data/alerted_doctors.json")

load_dotenv()


def main() -> None:
    doctors = load_doctors(CONFIG_PATH)
    alerted_doctors = load_alerted_doctors(STATE_PATH)

    with sync_playwright() as playwright:
        chrome_executable_path = os.getenv(
            "CHROME_EXECUTABLE_PATH"
        )

        if chrome_executable_path:
            # Use the installed browser on your Mac.
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=chrome_executable_path,
            )
        else:
            # Use Playwright's installed Chromium on the server.
            browser = playwright.chromium.launch(
                headless=True,
            )

        page = browser.new_page(
            viewport={"width": 1440, "height": 900}  
        )

        try:
            for doctor in doctors:
                print(f"\nChecking: {doctor.name}")
                print(f"URL: {doctor.url}")

                # Check this doctor without stopping the other checks.
                try:
                    available = check_appointments(
                        page=page,
                        doctor=doctor,
                    )
                except Exception as exc:
                    print(
                        f"ERROR checking {doctor.name}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    continue

                if available:
                    print("Appointments may be available!")

                    # Skip the notification if we already sent one
                    # during this availability period.
                    if doctor.url in alerted_doctors:
                        print(
                            "Already notified about this doctor. "
                            "Skipping duplicate notification."
                        )
                        continue

                    # Notify first. Only record the notification
                    # as sent if Telegram succeeds.
                    try:
                        send_telegram_message(
                            f"🚨 Potential appointment available!\n\n"
                            f"Doctor: {doctor.name}\n"
                            f"URL: {doctor.url}"
                        )
                    except Exception as exc:
                        print(
                            "ERROR sending Telegram notification: "
                            f"{type(exc).__name__}: {exc}"
                        )
                        continue

                    # Remember this doctor so the next run won't
                    # send the same notification again.
                    alerted_doctors.add(doctor.url)
                    save_alerted_doctors(
                        STATE_PATH,
                        alerted_doctors,
                    )

                    print("Telegram notification sent.")

                else:
                    print("No potential appointments detected.")

                    # Reset the alert status if availability disappears.
                    if doctor.url in alerted_doctors:
                        alerted_doctors.remove(doctor.url)
                        save_alerted_doctors(
                            STATE_PATH,
                            alerted_doctors,
                        )
                        print("Notification status reset.")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
