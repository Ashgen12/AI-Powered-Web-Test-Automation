# ai_test_generator/genai_handler.py
import os
import json
import logging
import pandas as pd
from openai import OpenAI, APIError, RateLimitError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
# It's better practice to use environment variables for API keys,
# but using the provided key directly for this specific case.
API_KEY = ""
BASE_URL = "https://beta.sree.shop/v1"
MODEL_NAME = "Provider-5/gpt-4o" # Use the specified model

try:
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    logging.info(f"OpenAI client initialized for model: {MODEL_NAME}")
except Exception as e:
    logging.error(f"Failed to initialize OpenAI client: {e}", exc_info=True)
    client = None # Ensure client is None if initialization fails

# --- Helper Function to Parse AI Response for Test Cases ---
def parse_ai_test_cases(response_content: str) -> list[dict]:
    """Attempts to parse the AI response string into a list of test case dictionaries."""
    try:
        # Try parsing directly as JSON if the AI follows instructions perfectly
        parsed_data = json.loads(response_content)
        if isinstance(parsed_data, list) and all(isinstance(item, dict) for item in parsed_data):
             # Basic validation for expected keys (can be made more robust)
            if parsed_data and all(k in parsed_data[0] for k in ['Test Case ID', 'Test Scenario', 'Steps to Execute', 'Expected Result']):
                logging.info("Successfully parsed AI response as JSON list of test cases.")
                return parsed_data
    except json.JSONDecodeError:
        logging.warning("AI response is not a direct JSON list. Trying to extract from markdown or other formats.")
        # Add more sophisticated parsing here if needed (e.g., regex for markdown tables)
        # For now, return empty if direct JSON parsing fails
        pass # Fall through to return empty list

    logging.error("Failed to parse AI response into the expected test case format.")
    return []


# --- Test Case Generation ---
def generate_test_cases(elements_json_str: str, url: str, num_cases: int = 5) -> pd.DataFrame:
    """
    Generates test cases using GenAI based on extracted UI elements.

    Args:
        elements_json_str: A JSON string representing the extracted UI elements.
        url: The URL of the website being tested (for context).
        num_cases: The desired number of test cases (default 3-5, AI might vary).

    Returns:
        A pandas DataFrame containing the generated test cases, or an empty DataFrame on failure.
    """
    if not client:
        logging.error("GenAI client is not available.")
        return pd.DataFrame()

    prompt = f"""
    Analyze the following UI elements extracted from the website {url}:
    ```json
    {elements_json_str}
    ```

    Based on these elements, generate {num_cases} meaningful test cases covering common user interactions like navigation, form interaction (if any), viewing content, etc. Focus on positive and potentially simple negative scenarios relevant to the visible elements.

    Present the test cases ONLY as a valid JSON list of objects. Each object must have the following keys:
    - "Test Case ID": A unique identifier (e.g., TC001, TC002).
    - "Test Scenario": A brief description of the test objective.
    - "Steps to Execute": Numbered steps describing how to perform the test manually. Mention specific element identifiers (text, id, placeholder) where possible from the JSON above.
    - "Expected Result": What should happen after executing the steps.

    Example format for a single test case object:
    {{
      "Test Case ID": "TC001",
      "Test Scenario": "Verify user can navigate to the 'Contact' page",
      "Steps to Execute": "1. Go to the homepage.\n2. Click on the link with text 'Contact'.",
      "Expected Result": "The contact page should load successfully, displaying contact information or a contact form."
    }}

    Ensure the entire output is *only* the JSON list, starting with '[' and ending with ']'. Do not include any introductory text, explanations, or markdown formatting outside the JSON structure itself.
    """

    logging.info(f"Generating {num_cases} test cases for {url}...")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert QA engineer generating test cases from UI elements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5, # Lower temperature for more predictable structure
            max_tokens=1500  # Adjust as needed
        )

        response_content = response.choices[0].message.content.strip()
        logging.info("Raw AI Response for Test Cases:\n" + response_content) # Log the raw response

        # Parse the response
        test_cases_list = parse_ai_test_cases(response_content)

        if not test_cases_list:
             logging.error("Failed to parse test cases from AI response.")
             # Attempt to return raw response in a placeholder format if parsing fails
             return pd.DataFrame([{'Test Case ID': 'PARSE_ERROR', 'Test Scenario': 'Failed to parse AI response', 'Steps to Execute': response_content, 'Expected Result': 'N/A'}])


        df = pd.DataFrame(test_cases_list)
        # Ensure standard columns exist, even if AI missed some
        for col in ['Test Case ID', 'Test Scenario', 'Steps to Execute', 'Expected Result']:
            if col not in df.columns:
                df[col] = 'N/A' # Add missing columns with default value
        df = df[['Test Case ID', 'Test Scenario', 'Steps to Execute', 'Expected Result']] # Enforce order

        logging.info(f"Successfully generated and parsed {len(df)} test cases.")
        return df

    except RateLimitError as e:
        logging.error(f"API Rate Limit Error: {e}")
        return pd.DataFrame([{'Test Case ID': 'API_ERROR', 'Test Scenario': 'Rate Limit Reached', 'Steps to Execute': str(e), 'Expected Result': 'N/A'}])
    except APIError as e:
        logging.error(f"API Error during test case generation: {e}")
        return pd.DataFrame([{'Test Case ID': 'API_ERROR', 'Test Scenario': 'API Communication Issue', 'Steps to Execute': str(e), 'Expected Result': 'N/A'}])
    except Exception as e:
        logging.error(f"Unexpected error during test case generation: {e}", exc_info=True)
        return pd.DataFrame([{'Test Case ID': 'ERROR', 'Test Scenario': 'Unexpected Error', 'Steps to Execute': str(e), 'Expected Result': 'N/A'}])


# --- Selenium Script Generation ---
def generate_selenium_script(test_case: dict, elements_json_str: str, url: str) -> str:
    """
    Generates a Python Selenium script for a single test case using GenAI.

    Args:
        test_case: A dictionary representing a single test case (needs 'Test Case ID', 'Steps to Execute').
        elements_json_str: A JSON string of extracted UI elements for context.
        url: The target website URL.

    Returns:
        A string containing the generated Python Selenium script, or an error message string.
    """
    if not client:
        logging.error("GenAI client is not available.")
        return "Error: GenAI client not initialized."

    test_case_id = test_case.get('Test Case ID', 'Unknown TC')
    steps = test_case.get('Steps to Execute', 'No steps provided.')
    scenario = test_case.get('Test Scenario', 'No scenario provided.')

    prompt = f"""
    Generate a complete, runnable Python Selenium script to automate the following test case for the website {url}.

    Test Case ID: {test_case_id}
    Test Scenario: {scenario}
    Steps to Execute:
    {steps}

    Use the following UI element details extracted from the page for context when choosing selectors. Prefer using ID, then Name, then CSS Selector, then Link Text, then XPath. Handle potential waits for elements to be clickable or visible.
    ```json
    {elements_json_str}
    ```

    The script should:
    1. Include necessary imports (Selenium webdriver, By, time, etc.).
    2. Set up the ChromeDriver (using webdriver-manager is preferred). Run in headless mode.
    3. Navigate to the base URL: {url}.
    4. Implement the test steps described above using Selenium commands (find_element, click, send_keys, etc.). Use robust locators based on the provided element details. Include reasonable waits (e.g., `time.sleep(1)` or explicit waits) after actions like clicks or navigation.
    5. Include a basic assertion relevant to the 'Expected Result' or the final step (e.g., check page title, check for an element's presence/text). If the expected result is vague, make a reasonable assertion based on the steps.
    6. Print a success or failure message to the console based on the assertion.
    7. Include teardown code to close the browser (`driver.quit()`) in a `finally` block.
    8. Be fully contained within a single Python code block.

    Output *only* the Python code for the script. Do not include any explanations, introductory text, or markdown formatting like ```python ... ```.
    """

    logging.info(f"Generating Selenium script for Test Case ID: {test_case_id}...")
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert QA automation engineer generating Python Selenium scripts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3, # Low temperature for more deterministic code generation
            max_tokens=2000 # Allow ample space for code
        )

        script_code = response.choices[0].message.content.strip()

        # Basic cleanup: remove potential markdown fences if AI includes them
        if script_code.startswith("```python"):
            script_code = script_code[len("```python"):].strip()
        if script_code.endswith("```"):
            script_code = script_code[:-len("```")].strip()

        logging.info(f"Successfully generated script for {test_case_id}.")
        # Log first few lines of the script for verification
        logging.debug(f"Generated script (first 100 chars): {script_code[:100]}...")
        return script_code

    except RateLimitError as e:
        logging.error(f"API Rate Limit Error during script generation for {test_case_id}: {e}")
        return f"# Error: API Rate Limit Reached\n# {e}"
    except APIError as e:
        logging.error(f"API Error during script generation for {test_case_id}: {e}")
        return f"# Error: API Communication Issue\n# {e}"
    except Exception as e:
        logging.error(f"Unexpected error during script generation for {test_case_id}: {e}", exc_info=True)
        return f"# Error: Unexpected error during script generation\n# {e}"