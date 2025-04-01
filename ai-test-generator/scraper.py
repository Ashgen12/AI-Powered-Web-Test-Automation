# ai_test_generator/scraper.py
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_elements(url: str) -> list[dict]:
    """
    Scrapes a website URL to extract buttons, links, input fields, and forms.

    Args:
        url: The public URL of the website to scrape.

    Returns:
        A list of dictionaries, each representing an extracted UI element.
        Returns an empty list if scraping fails.
    """
    logging.info(f"Starting scraping for URL: {url}")
    extracted_elements = []

    chrome_options = Options()
    chrome_options.add_argument("--headless") # Run headless (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu") # Recommended for headless
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36") # Set user agent

    service = Service(ChromeDriverManager().install())
    driver = None

    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(30) # Set timeout for page load
        driver.get(url)
        # Allow some time for dynamic content to potentially load
        # A more robust solution might use WebDriverWait
        time.sleep(3)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'lxml') # Use lxml parser

        # --- Extract Buttons ---
        buttons = soup.find_all('button')
        for btn in buttons:
            element_data = {
                'type': 'button',
                'text': btn.get_text(strip=True),
                'id': btn.get('id'),
                'name': btn.get('name'),
                'class': btn.get('class'),
                'attributes': {k: v for k, v in btn.attrs.items() if k not in ['id', 'name', 'class']}
            }
            extracted_elements.append(element_data)
        logging.info(f"Found {len(buttons)} buttons.")

        # --- Extract Links ---
        links = soup.find_all('a')
        for link in links:
            element_data = {
                'type': 'link',
                'text': link.get_text(strip=True),
                'href': link.get('href'),
                'id': link.get('id'),
                'class': link.get('class'),
                'attributes': {k: v for k, v in link.attrs.items() if k not in ['id', 'class', 'href']}
            }
            extracted_elements.append(element_data)
        logging.info(f"Found {len(links)} links.")

        # --- Extract Input Fields ---
        inputs = soup.find_all('input')
        for inp in inputs:
            element_data = {
                'type': 'input',
                'input_type': inp.get('type', 'text'), # Default to 'text' if type not specified
                'id': inp.get('id'),
                'name': inp.get('name'),
                'placeholder': inp.get('placeholder'),
                'value': inp.get('value'),
                'class': inp.get('class'),
                'attributes': {k: v for k, v in inp.attrs.items() if k not in ['id', 'name', 'class', 'type', 'placeholder', 'value']}
            }
            extracted_elements.append(element_data)
        logging.info(f"Found {len(inputs)} input fields.")

        # --- Extract Forms ---
        forms = soup.find_all('form')
        for form in forms:
            form_elements = []
            # Find elements within this specific form
            for child_input in form.find_all('input'):
                 form_elements.append({
                    'tag': 'input',
                    'type': child_input.get('type'),
                    'id': child_input.get('id'),
                    'name': child_input.get('name')
                 })
            for child_button in form.find_all('button'):
                 form_elements.append({
                    'tag': 'button',
                    'type': child_button.get('type'),
                    'id': child_button.get('id'),
                    'name': child_button.get('name'),
                    'text': child_button.get_text(strip=True)
                 })
            # Add other form element types if needed (select, textarea)

            element_data = {
                'type': 'form',
                'id': form.get('id'),
                'action': form.get('action'),
                'method': form.get('method'),
                'class': form.get('class'),
                'contained_elements': form_elements,
                'attributes': {k: v for k, v in form.attrs.items() if k not in ['id', 'class', 'action', 'method']}
            }
            extracted_elements.append(element_data)
        logging.info(f"Found {len(forms)} forms.")

        logging.info(f"Successfully extracted {len(extracted_elements)} elements in total.")

    except Exception as e:
        logging.error(f"Error during scraping URL {url}: {e}", exc_info=True)
        # Return empty list on error, Gradio app will handle this
        return []
    finally:
        if driver:
            driver.quit()
            logging.info("WebDriver closed.")

    return extracted_elements

# Example usage (optional, for testing scraper independently)
# if __name__ == '__main__':
#     test_url = "https://demoblaze.com/"
#     elements = extract_elements(test_url)
#     if elements:
#         print(f"Extracted {len(elements)} elements.")
#         # Save to a temporary file for inspection
#         with open("temp_elements.json", "w", encoding="utf-8") as f:
#             json.dump(elements, f, indent=4)
#         print("Saved results to temp_elements.json")
#     else:
#         print("Scraping failed.")