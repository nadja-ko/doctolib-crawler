from playwright.sync_api import sync_playwright

URL = "https://www.doctolib.de/frauenarzt/berlin/christina-koch"


with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=False,
        executable_path="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    )

    page = browser.new_page(
        viewport={"width": 1440, "height": 900}
    )

    # =========================================================
    # 1. OPEN DOCTOR PROFILE
    # =========================================================

    print("Opening doctor profile...")

    page.goto(
        URL,
        wait_until="domcontentloaded"
    )

    print("Waiting 10 seconds...")
    page.wait_for_timeout(10000)

    # =========================================================
    # 2. REJECT COOKIES
    # =========================================================

    cookie_button = page.locator(
        "#didomi-notice-disagree-button"
    )

    if cookie_button.count() > 0:

        cookie_button.click()

        print("Cookie dialog dismissed!")

    print("Waiting 5 seconds...")
    page.wait_for_timeout(5000)

    # =========================================================
    # 3. CLICK "TERMIN BUCHEN"
    # =========================================================

    booking_links = page.locator(
        'a[aria-label="Termin buchen"]'
    )

    visible_booking_link = None

    for i in range(booking_links.count()):

        link = booking_links.nth(i)

        if link.is_visible():

            visible_booking_link = link

            break

    if visible_booking_link is None:

        print("ERROR: No visible booking link found.")

        input("\nPress ENTER to close...")
        browser.close()
        raise SystemExit

    print("\nClicking 'Termin buchen'...")

    visible_booking_link.click()

    print("Waiting...")
    page.wait_for_timeout(4000)

    # =========================================================
    # 4. CLICK "GESETZLICH VERSICHERT"
    # =========================================================

    statutory_button = page.get_by_role(
        "button",
        name="Gesetzlich versichert",
        exact=True
    )

    print(
        "\nStatutory insurance buttons:",
        statutory_button.count()
    )

    if statutory_button.count() == 0:

        print("ERROR: Could not find 'Gesetzlich versichert'.")

        input("\nPress ENTER to close...")
        browser.close()
        raise SystemExit

    print("Clicking 'Gesetzlich versichert'...")

    statutory_button.click()

    print("Waiting...")
    page.wait_for_timeout(4000)

    # =========================================================
    # 5. CLICK "ERSTUNTERSUCHUNG NEUPATIENT:IN"
    # =========================================================

    new_patient_button = page.get_by_role(
        "button",
        name="Erstuntersuchung Neupatient:in",
        exact=True
    )

    print(
        "\nNew-patient appointment buttons:",
        new_patient_button.count()
    )

    if new_patient_button.count() == 0:

        print(
            "ERROR: Could not find "
            "'Erstuntersuchung Neupatient:in'."
        )

        print("\nVisible buttons:")

        buttons = page.locator("button")

        for i in range(buttons.count()):

            button = buttons.nth(i)

            if button.is_visible():

                print(
                    f"{i}: "
                    f"text={button.inner_text()!r}"
                )

        input("\nPress ENTER to close...")
        browser.close()
        raise SystemExit

    print(
        "Clicking "
        "'Erstuntersuchung Neupatient:in'..."
    )

    new_patient_button.click()

    # =========================================================
    # 6. WAIT FOR APPOINTMENT AVAILABILITY
    # =========================================================

    print("\nWaiting for appointment availability...")

    page.wait_for_timeout(5000)

    # =========================================================
    # 7. INSPECT THE RESULT
    # =========================================================

    print("\n\n==============================================")
    print("       APPOINTMENT AVAILABILITY PAGE")
    print("==============================================")

    print("\nURL:")
    print(page.url)

    print("\nTITLE:")
    print(page.title())

    print("\nPAGE TEXT:")
    print(
        page.locator("body").inner_text()[:15000]
    )

    # =========================================================
    # 8. VISIBLE BUTTONS
    # =========================================================

    print("\n\n========== VISIBLE BUTTONS ==========")

    buttons = page.locator("button")

    print(
        "Number of buttons:",
        buttons.count()
    )

    for i in range(buttons.count()):

        button = buttons.nth(i)

        if button.is_visible():

            try:
                text = button.inner_text().strip()
            except:
                text = ""

            print(
                f"{i}: text={text!r}, "
                f"aria={button.get_attribute('aria-label')!r}"
            )

    # =========================================================
    # 9. VISIBLE LINKS
    # =========================================================

    print("\n\n========== VISIBLE LINKS ==========")

    links = page.locator("a")

    for i in range(links.count()):

        link = links.nth(i)

        if link.is_visible():

            try:
                text = link.inner_text().strip()
            except:
                text = ""

            href = link.get_attribute("href")

            if text or href:

                print(
                    f"{i}: "
                    f"text={text!r}, "
                    f"href={href!r}"
                )

    print("\n==============================================")

    input("\nPress ENTER to close...")

    browser.close()
    