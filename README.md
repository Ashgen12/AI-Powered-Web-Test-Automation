# AI-Driven Test Generation Prototype

This project implements a simplified AI-driven prototype that scrapes website UI elements, uses a Generative AI model (via an OpenAI-compatible API) to generate test cases, and then generates corresponding Python Selenium scripts for those test cases. The application provides a Gradio web interface for easy interaction.

<details>
  <summary>🔗 Live Demo Link</summary>
  
  [https://huggingface.co/spaces/Ashgen12/AI-Powered-Web-Test-Automation](https://huggingface.co/spaces/Ashgen12/AI-Powered-Web-Test-Automation)
</details>

## 📁 Project Structure

```bash
ai_test_generator/
│
├── 📄 app.py                 # Main Gradio application
├── 📄 scraper.py             # Web scraping logic
├── 📄 genai_handler.py       # GenAI interaction logic
├── 📄 utils.py               # Utility functions
├── 📄 requirements.txt       # Python dependencies
├── 📄 README.md              # Project documentation
│
└── 📂 outputs/               # Generated files directory
    ├── 📄 elements.json      # Extracted UI elements
    ├── 📄 test_cases.xlsx    # Generated test cases
    └── 📄 test_scripts.xlsx  # Selenium scripts
```

## Features

*   **Web Scraping:** Extracts buttons, links, input fields, and forms from a given public URL using Selenium and BeautifulSoup.
*   **UI Element Storage:** Saves extracted elements into a structured `elements.json` file.
*   **AI Test Case Generation:** Uses a specified GenAI model (`Provider-5/gpt-4o` via `beta.sree.shop`) to analyze extracted elements and generate 3-5 meaningful test cases.
*   **Test Case Export:** Exports generated test cases into a structured `test_cases.xlsx` file.
*   **AI Selenium Script Generation:** Uses the same GenAI model to generate Python Selenium scripts based on the generated test cases and element context.
*   **Script Export:** Exports generated Selenium scripts (as strings) into a `test_scripts.xlsx` file.
*   **Interactive UI:** Provides a user-friendly Gradio web interface to input the URL, trigger the process, view results, and download generated files.

## Technologies Used

*   **Python:** Core programming language.
*   **Gradio:** Framework for building the web UI.
*   **Selenium:** For browser automation and dynamic web scraping.
*   **BeautifulSoup4:** For parsing HTML content.
*   **webdriver-manager:** For automatically managing ChromeDriver.
*   **OpenAI Python Library:** For interacting with the OpenAI-compatible GenAI API.
*   **Pandas:** For data manipulation and exporting to Excel (`.xlsx`).
*   **openpyxl:** Required by Pandas for Excel file operations.
*   **GenAI Model:** `Provider-5/gpt-4o` accessed via `https://beta.sree.shop/v1` (using the provided API key).

## Setup and Installation

1.  **Prerequisites:**
    *   Python 3.8+ installed.
    *   Google Chrome browser installed.
    *   `pip` (Python package installer).

2.  **Clone the Repository (or create files):**
    ```bash
    # git clone <your-repo-url> # If using Git
    # cd ai-test-generator
    # Otherwise, create the directory structure and files as shown above.
    ```

3.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: This will install all necessary Python libraries, including `webdriver-manager` which handles ChromeDriver download.*

## How to Run

1.  Ensure you are in the project's root directory (`ai_test_generator`) and your virtual environment is activated.
2.  Run the Gradio application:
    ```bash
    python app.py
    ```
3.  The script will start a local web server. Open your web browser and navigate to the URL provided in the console (usually `http://127.0.0.1:7860`).
4.  In the web interface:
    *   Enter a valid public website URL (e.g., `https://demoblaze.com`).
    *   Adjust the slider for the desired number of test cases.
    *   Click the "✨ Analyze Website and Generate Tests ✨" button.
5.  Monitor the "Status & Logs" section for progress updates.
6.  Once processing is complete, the results will be displayed in the respective tabs:
    *   **Extracted UI Elements:** Shows a preview of `elements.json`.
    *   **Generated Test Cases:** Displays the test cases in a table.
    *   **Generated Selenium Scripts:** Shows the generated scripts alongside their Test Case IDs.
7.  Use the "Download" buttons below each section to save the generated `elements.json`, `test_cases.xlsx`, and `test_scripts.xlsx` files (these will be saved to your browser's default download location). The files are also saved temporarily in the `outputs/` directory within the project structure.

## GenAI Chat Conversation Link

*The Prototype has been deployed at this site [AI-Driven Test Generation Prototype](https://huggingface.co/spaces/Ashgen12/AI-Powered-Web-Test-Automation). Yo can try it*

## Approach and Architecture

1.  **Modular Design:** The code is split into modules:
    *   `scraper.py`: Handles web scraping logic.
    *   `genai_handler.py`: Manages all interactions with the GenAI API, including prompt definition and response parsing.
    *   `utils.py`: Contains utility functions for saving files.
    *   `app.py`: Sets up the Gradio interface and orchestrates the workflow by calling functions from other modules.
2.  **Workflow:**
    *   The Gradio app (`app.py`) takes the URL as input.
    *   It calls `scraper.extract_elements` to get UI element data. Selenium (headless Chrome) fetches the page, and BeautifulSoup parses the HTML.
    *   The extracted elements are structured as a list of dictionaries and saved to `elements.json` (via `utils.save_elements_to_json`). A JSON string representation is prepared.
    *   `genai_handler.generate_test_cases` is called with the elements JSON string and URL. It constructs a detailed prompt, calls the GenAI API, parses the response (expecting JSON), and returns a Pandas DataFrame.
    *   The test cases DataFrame is saved to `test_cases.xlsx` (via `utils.save_test_cases_to_excel`).
    *   The app iterates through the generated test cases. For each case, it calls `genai_handler.generate_selenium_script`, providing the test case details, element context (JSON string), and URL. This function prompts the AI to generate a runnable Python Selenium script.
    *   The generated scripts (strings) are collected along with their Test Case IDs.
    *   This script data is saved to `test_scripts.xlsx` (via `utils.save_scripts_to_excel`).
    *   All results (JSON preview, DataFrames, file paths for download) are returned to the Gradio interface for display.
3.  **Error Handling:** Basic `try...except` blocks are used for scraping, API calls, and file operations. Status updates and errors are reported back to the Gradio UI. The AI generation functions include specific error handling for API errors (like rate limits) and return placeholder DataFrames or error strings.
4.  **Prompt Engineering:** Prompts in `genai_handler.py` are designed to be specific:
    *   Clearly state the goal (generate test cases / generate Selenium script).
    *   Provide necessary context (URL, UI elements JSON).
    *   Specify the exact desired output format (JSON list for test cases, pure Python code for scripts).
    *   Guide the AI on preferred selectors (ID > Name > CSS > XPath) for script generation.
    *   Request complete, runnable scripts with setup, teardown, and basic assertions.
    *   Use lower temperatures (`0.3`-`0.5`) for more predictable/structured output.

## Challenges Faced

*   **AI Output Variability:** GenAI models can sometimes fail to adhere strictly to the requested format (e.g., adding extra text around JSON or code blocks), requiring parsing and cleanup logic.
*   **AI Hallucinations/Inaccuracies:** The AI might generate steps or selectors for elements that don't exist or are incorrectly identified based solely on the provided JSON. Generated scripts often require manual verification and debugging.
*   **Web Scraping Complexity:** Modern websites heavily reliant on JavaScript or using anti-scraping techniques can be difficult to scrape accurately with this simplified approach. 

## Potential Improvements

*   **More Robust Scraping:** Implement Selenium `WebDriverWait` for explicit waits instead of `time.sleep()` to handle dynamic content loading more reliably. Consider interacting with the page (e.g., scrolling) to reveal more elements.
*   **Enhanced Element Representation:** Include more element details (e.g., visibility state, computed styles, parent/child relationships) in `elements.json` to give the AI better context.
