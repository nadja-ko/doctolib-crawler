from playwright.sync_api import sync_playwright


URL = "https://www.doctolib.de/frauenarzt/berlin/christina-koch"


def check_availability_of_appointments(page):
    """Check a list of preferred doctors for a new-patient appointment."""

    print("Opening doctor profile...")

    page.goto(URL, wait_until="domcontentloaded")

    # Give Doctolib a moment to finish rendering
    page.wait_for_timeout(1000)
    # ---------------------------------------------------------
    # 1. Handle cookie banner
    # ---------------------------------------------------------

    cookie_button = page.locator("#didomi-notice-disagree-button")

    if cookie_button.count() > 0:
        print("Cookie dialog dismissed!")
        cookie_button.click()

    # ---------------------------------------------------------
    # 2. Click "Termin buchen"
    # ---------------------------------------------------------

    print("Opening booking...")

    booking_link = page.locator('a[aria-label="Termin buchen"]').filter(
        visible=True
    )

    booking_link.wait_for(state="visible", timeout=4000)
    booking_link.click()

    page.wait_for_load_state("domcontentloaded")

    # ---------------------------------------------------------
    # 3. Select statutory/public insurance
    # ---------------------------------------------------------

    print("Selecting statutory insurance...")

    insurance_button = page.get_by_role(
        "button",
        name="Gesetzlich versichert",
        exact=True,
    )

    insurance_button.wait_for(state="visible", timeout=15000)
    insurance_button.click()

    # ---------------------------------------------------------
    # 4. Select new-patient appointment
    # ---------------------------------------------------------

    print("Selecting 'Erstuntersuchung Neupatient:in'...")

    appointment_button = page.get_by_role(
        "button",
        name="Erstuntersuchung Neupatient:in",
        exact=True,
    )

    appointment_button.wait_for(state="visible", timeout=15000)
    appointment_button.click()

    # ---------------------------------------------------------
    # 5. Wait for availability page
    # ---------------------------------------------------------

    print("Checking availability...")

    page.wait_for_load_state("domcontentloaded")

    # Give Doctolib a moment to finish rendering the availability state.
    page.wait_for_timeout(1000)

    # ---------------------------------------------------------
    # 6. Detect availability
    # ---------------------------------------------------------

    page_text = page.locator("body").inner_text()

    if "Keine Termine online verfügbar" in page_text:
        print("\n❌ NO APPOINTMENTS AVAILABLE")
        available = False
    else:
        print("\n🎉 POSSIBLE APPOINTMENTS FOUND!")
        available = True

    # ---------------------------------------------------------
    # 7. Show result
    # ---------------------------------------------------------

    print("\nCurrent URL:")
    print(page.url)

    return available


def main():
    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False,
            executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        )

        page = browser.new_page()

        try:
            available = check_availability_of_appointments(page)

            print("\n--------------------------------")
            print(f"Appointment available: {available}")
            print("--------------------------------")

            input("\nPress ENTER to close...")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
    