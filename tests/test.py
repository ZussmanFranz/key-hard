import time
import random
import string
import requests  # Do obsługi API
from urllib.parse import urlparse, parse_qs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# --- KONFIGURACJA ---
BASE_URL = "https://localhost:8443"  # Bez /pl/ na końcu dla API
SHOP_URL = BASE_URL + "/pl/"
API_KEY = "ANDMVYS72WHPPLSEUBMHR13XAMJ19B8U"

# Ustawienia przeglądarki
options = Options()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--allow-insecure-localhost')
options.add_argument('--start-maximized')

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 10)


def generate_random_email():
    return ''.join(random.choices(string.ascii_lowercase, k=10)) + "@test.com"


def generate_random_password():
    return "Pass1234!"


def change_order_status_via_api(order_id, new_status_id=2):
    """
    Zmienia status zamówienia używając PrestaShop Webservice.
    Tworzy nowy wpis w zasobie order_histories.
    Status ID 2 = Płatność przyjęta.
    """
    print(f"--- API: Zmieniam status zamówienia #{order_id} na {new_status_id} ---")

    api_url = f"{BASE_URL}/api/order_histories"

    # XML wymagany do utworzenia historii zamówienia
    xml_payload = f"""<prestashop xmlns:xlink="http://www.w3.org/1999/xlink">
        <order_history>
            <id_order>{order_id}</id_order>
            <id_order_state>{new_status_id}</id_order_state>
        </order_history>
    </prestashop>"""

    try:
        # Wysyłamy POST request. verify=False bo to localhost (ignoruj SSL)
        response = requests.post(
            api_url,
            data=xml_payload,
            params={'ws_key': API_KEY},
            verify=False
        )

        if response.status_code in [200, 201]:
            print("--- API: Sukces! Status zmieniony. ---")
            return True
        else:
            print(f"--- API BŁĄD: Kod {response.status_code} ---")
            print(response.text)
            return False
    except Exception as e:
        print(f"--- API EXCEPTION: {e} ---")
        return False


try:
    print("--- ROZPOCZĘCIE TESTU ---")

    # 1. Dodanie 10 produktów (LOGIKA Z POPRZEDNIEGO KROKU)
    categories = ["15-ksiazki", "18-muzyka"]
    products_added = 0

    for category in categories:
        category_url = SHOP_URL + category
        driver.get(category_url)
        products = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-miniature")))
        loop_range = min(5, len(products))

        for i in range(loop_range):
            try:
                driver.get(category_url)
                products = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-miniature")))
                product = products[i]
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", product)
                product.find_element(By.CSS_SELECTOR, "a.thumbnail").click()

                qty = random.randint(1, 2)
                qty_input = wait.until(EC.element_to_be_clickable((By.ID, "quantity_wanted")))
                qty_input.send_keys(Keys.CONTROL + "a")
                qty_input.send_keys(str(qty))

                add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.add-to-cart")))
                add_btn.click()

                continue_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#blockcart-modal .btn-secondary"))
                )
                continue_btn.click()
                time.sleep(0.5)
                products_added += 1
                print(f"Dodano produkt {products_added}/10")
            except Exception as e:
                print(f"Błąd produktu: {e}")
                continue

    # 2. Wyszukanie i dodanie (LOGIKA Z POPRZEDNIEGO KROKU)
    print("--- WYSZUKIWANIE ---")
    driver.get(SHOP_URL)
    search_input = wait.until(EC.element_to_be_clickable((By.NAME, "s")))
    search_input.clear()
    search_input.send_keys("Hummingbird")
    search_input.send_keys(Keys.RETURN)

    found_products = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".product-miniature")))
    if found_products:
        random.choice(found_products).find_element(By.CSS_SELECTOR, "a.thumbnail").click()
        add_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.add-to-cart")))
        add_btn.click()
        checkout_modal_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#blockcart-modal .btn-primary")))
        checkout_modal_btn.click()
    else:
        driver.get(SHOP_URL + "koszyk")

    # 3. Usuwanie (LOGIKA Z POPRZEDNIEGO KROKU)
    print("--- USUWANIE Z KOSZYKA ---")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "cart-items")))
    for _ in range(3):
        try:
            delete_buttons = driver.find_elements(By.CLASS_NAME, "remove-from-cart")
            if delete_buttons:
                delete_buttons[0].click()
                time.sleep(1.5)
                print("Usunięto produkt.")
            else:
                break
        except:
            pass

    checkout_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.checkout a.btn-primary")))
    checkout_btn.click()

    # 4. Rejestracja
    print("--- REJESTRACJA ---")
    wait.until(EC.presence_of_element_located((By.ID, "customer-form")))
    driver.find_element(By.ID, "field-id_gender-1").click()
    driver.find_element(By.NAME, "firstname").send_keys("Jan")
    driver.find_element(By.NAME, "lastname").send_keys("Kowalski")
    driver.find_element(By.NAME, "email").send_keys(generate_random_email())
    driver.find_element(By.NAME, "password").send_keys(generate_random_password())
    driver.find_element(By.NAME, "birthday").send_keys("1990-01-01")

    for cb in driver.find_elements(By.NAME, "psgdpr"):
        if not cb.is_selected(): cb.click()
    for cb in driver.find_elements(By.NAME, "customer_privacy"):
        if not cb.is_selected(): cb.click()

    driver.find_element(By.CSS_SELECTOR, "button[data-link-action='register-new-customer']").click()

    # 5. Adres
    print("--- ADRES ---")
    wait.until(EC.visibility_of_element_located((By.NAME, "address1")))
    driver.find_element(By.NAME, "address1").send_keys("Ulica Testowa 123")
    driver.find_element(By.NAME, "postcode").send_keys("00-001")
    driver.find_element(By.NAME, "city").send_keys("Warszawa")
    wait.until(EC.element_to_be_clickable((By.NAME, "confirm-addresses"))).click()

    # 6. Dostawa
    print("--- DOSTAWA ---")
    wait.until(EC.presence_of_element_located((By.NAME, "confirmDeliveryOption")))
    delivery_options = driver.find_elements(By.CSS_SELECTOR, ".delivery-option .custom-radio")
    if len(delivery_options) >= 2:
        driver.execute_script("arguments[0].click();", delivery_options[1])
    elif delivery_options:
        driver.execute_script("arguments[0].click();", delivery_options[0])
    wait.until(EC.element_to_be_clickable((By.NAME, "confirmDeliveryOption"))).click()

    # 7. Płatność
    print("--- PŁATNOŚĆ ---")
    wait.until(EC.presence_of_element_located((By.ID, "payment-option-1")))
    payment_options = driver.find_elements(By.CSS_SELECTOR, ".payment-option")
    cod_found = False
    for option in payment_options:
        label = option.find_element(By.TAG_NAME, "label")
        if "odbiorze" in label.text.lower() or "cash" in label.text.lower():
            driver.execute_script("arguments[0].click();", option.find_element(By.CSS_SELECTOR, "input[type='radio']"))
            cod_found = True
            break
    if not cod_found and payment_options:
        driver.execute_script("arguments[0].click();",
                              payment_options[0].find_element(By.CSS_SELECTOR, "input[type='radio']"))

    terms = driver.find_element(By.ID, "conditions_to_approve[terms-and-conditions]")
    if not terms.is_selected(): terms.click()

    # 8. Zatwierdzenie
    time.sleep(1)
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#payment-confirmation button"))).click()

    # 9. Pobranie ID zamówienia i ZMIANA STATUSU PRZEZ API
    print("--- ZMIANA STATUSU PRZEZ API ---")
    wait.until(EC.presence_of_element_located((By.ID, "content-hook_order_confirmation")))

    # Pobieramy ID zamówienia z URL (parametr id_order lub id_order_formatted zależy od wersji/modułu,
    # w standardzie 1.7 na potwierdzeniu jest parametr w URL: ?controller=order-confirmation&id_cart=...&id_order=XYZ)
    current_url = driver.current_url
    parsed_url = urlparse(current_url)
    try:
        query_params = parse_qs(parsed_url.query)
        order_id = query_params.get('id_order', [None])[0]

        if order_id:
            print(f"Pobrano ID zamówienia: {order_id}")

            # Wywołanie API
            success = change_order_status_via_api(order_id, 2)  # 2 = Płatność przyjęta

            if success:
                print("Czekam 3 sekundy na przetworzenie zmian w sklepie...")
                time.sleep(3)
            else:
                print("Ostrzeżenie: Nie udało się zmienić statusu przez API.")
        else:
            print("Nie udało się znaleźć ID zamówienia w URL. Pomijam zmianę statusu.")

    except Exception as e:
        print(f"Błąd podczas obsługi API: {e}")

    # 10. Pobranie faktury
    print("--- POBIERANIE FAKTURY ---")
    driver.get(SHOP_URL + "historia-zamowien")

    try:
        # Odświeżamy stronę dla pewności
        driver.refresh()

        # Szukamy linku do PDF
        invoice_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//table//tr[1]//a[contains(@href, 'pdf-invoice')]")))
        print(f"Link do faktury: {invoice_link.get_attribute('href')}")
        invoice_link.click()
        print("Pobieranie faktury...")
        time.sleep(5)
    except Exception as e:
        print(f"Błąd pobierania faktury: {e}")

    print("--- KONIEC TESTU ---")

except Exception as e:
    print(f"BŁĄD KRYTYCZNY: {e}")
    driver.save_screenshot("final_error.png")

finally:
    # driver.quit() # Odkomentuj, żeby zamknąć
    pass