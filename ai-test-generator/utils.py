# ai_test_generator/utils.py
import json
import pandas as pd
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
OUTPUT_DIR = "outputs" # Define output directory

def save_elements_to_json(elements: list[dict], filename: str = "elements.json") -> str:
    """Saves extracted elements to a JSON file."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(elements, f, indent=4)
        logging.info(f"Successfully saved elements to {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Error saving elements to JSON file {filepath}: {e}", exc_info=True)
        return ""

def save_test_cases_to_excel(test_cases_df: pd.DataFrame, filename: str = "test_cases.xlsx") -> str:
    """Saves test cases DataFrame to an Excel file."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        test_cases_df.to_excel(filepath, index=False, engine='openpyxl')
        logging.info(f"Successfully saved test cases to {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Error saving test cases to Excel file {filepath}: {e}", exc_info=True)
        return ""

def save_scripts_to_excel(scripts_data: list[dict], filename: str = "test_scripts.xlsx") -> str:
    """Saves generated scripts along with Test Case IDs to an Excel file."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        df = pd.DataFrame(scripts_data)
        # Ensure consistent column order
        if not df.empty:
             df = df[['Test Case ID', 'Python Selenium Code']]
        else:
             # Create empty DataFrame with columns if no scripts were generated
             df = pd.DataFrame(columns=['Test Case ID', 'Python Selenium Code'])

        df.to_excel(filepath, index=False, engine='openpyxl')
        logging.info(f"Successfully saved scripts to {filepath}")
        return filepath
    except Exception as e:
        logging.error(f"Error saving scripts to Excel file {filepath}: {e}", exc_info=True)
        return ""