from pathlib import Path

from playwright.sync_api import sync_playwright

from doctolib_crawler.checker import check_appointments
from doctolib_crawler.config import load_doctors
from doctolib_crawler.notifications.telegram import send_telegram_message

CONFIG_PATH = Path("config/doctors.yaml")

def main() -> None:

    doctors = load_doctors(CONFIG_PATH)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            executable_path=(
                "/Applications/Google Chrome.app/"
                "Contents/MacOS/Google Chrome"
            ),
        )

        page = browser.new_page(
            viewport={"width": 1440, "height": 900}
        )

        try:
            for doctor in doctors:
                print(f"\nChecking: {doctor.name}")
                print(f"URL: {doctor.url}")

                available = check_appointments(page=page, doctor=doctor)

            if available:
                print("Appointments may be available!")

                send_telegram_message(
                    f"🚨 Appointment available!\n\n"
                    f"Doctor: {doctor.name}\n"
                    f"URL: {doctor.url}"
                )
            else:
                print("No appointments available.")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
       