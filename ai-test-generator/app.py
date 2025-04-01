# ai_test_generator/app.py
import gradio as gr
import pandas as pd
import json
import logging
import os
import html # Keep for potential future use, though not strictly needed now

from scraper import extract_elements
from genai_handler import generate_test_cases, generate_selenium_script
from utils import save_elements_to_json, save_test_cases_to_excel, save_scripts_to_excel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure output directory exists
OUTPUT_DIR = "outputs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- Custom CSS (Keep the enhanced CSS from the previous version) ---
custom_css = """
/* === Body and General Styles === */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(to bottom right, #e0f2f7, #ffffff); /* Light blue gradient */
    color: #333;
    margin: 0;
    padding: 0;
}

/* Gradio container adjustments */
.gradio-container {
    max-width: 1200px; /* Increase max width */
    margin: 0 auto !important; /* Center the container */
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    background-color: #ffffff; /* White background for content area */
    overflow: hidden; /* Ensure shadows are contained */
}

/* === Header Simulation === */
.app-header {
    background: linear-gradient(to right, #007bff, #0056b3); /* Blue gradient header */
    color: white;
    padding: 20px 30px;
    text-align: center;
    border-bottom: 3px solid #004085;
}
.app-header h1 {
    margin: 0;
    font-size: 2.2em;
    font-weight: 600;
    letter-spacing: 1px;
}
.app-header p {
    margin-top: 8px;
    font-size: 1.1em;
    opacity: 0.9;
}

/* === Content Area Styling === */
.control-section {
    padding: 25px 30px;
    background-color: #f8f9fa; /* Light grey for control section */
    border-bottom: 1px solid #dee2e6;
    border-radius: 8px;
    margin: 20px;
    box-shadow: 0 2px 5px rgba(0,0,0, 0.05);
}

.control-section label {
    font-weight: 600;
    color: #0056b3; /* Darker blue for labels */
    margin-bottom: 8px !important;
    display: block;
}

/* Input fields styling */
.gradio-textbox input[type="text"], .gradio-slider input[type="number"] {
    border: 1px solid #ced4da;
    border-radius: 5px;
    padding: 10px 12px;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
.gradio-textbox input[type="text"]:focus, .gradio-slider input[type="number"]:focus {
    border-color: #007bff;
    box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
    outline: none;
}

/* Button Styling */
#generate-button { /* Use ID selector for more specificity */
    background: linear-gradient(to right, #28a745, #218838); /* Green gradient */
    color: white !important; /* Ensure text is white */
    font-weight: bold;
    border-radius: 25px !important; /* More rounded */
    padding: 12px 25px !important;
    border: none !important;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.15);
    transition: background 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
    cursor: pointer;
    font-size: 1.1em !important;
    display: block !important; /* Center button */
    margin: 15px auto 0 auto !important; /* Center with margin */
    width: fit-content !important; /* Fit content width */
}
#generate-button:hover {
    background: linear-gradient(to right, #218838, #1e7e34);
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

/* Status/Logs Accordion */
.gradio-accordion {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin: 20px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0, 0.05);
}
.gradio-accordion > .gr-button { /* Targeting the accordion header button more specifically */
    background-color: #f1f3f5 !important;
    border-bottom: 1px solid #e0e0e0 !important;
    font-weight: 600 !important;
    color: #495057 !important;
    padding: 12px 20px !important;
}
.gradio-accordion > div { /* Targeting the accordion content */
     padding: 15px 20px;
}

/* === Results Section === */
.results-section {
    padding: 10px 30px 30px 30px; /* Less top padding, more bottom */
}
.results-section h2 {
    text-align: center;
    color: #0056b3;
    margin-bottom: 25px;
    font-size: 1.8em;
}

/* Tab Styling */
.gradio-tabs > .tab-nav button { /* More specific selector for tab buttons */
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 12px 20px;
    font-weight: 600;
    color: #495057;
    transition: background-color 0.2s ease, color 0.2s ease;
}
.gradio-tabs > .tab-nav button.selected {
    background-color: #ffffff;
    border-color: #dee2e6;
    color: #007bff;
    border-bottom: 1px solid #ffffff; /* Hide bottom border of selected tab */
    position: relative;
    top: 1px; /* Align with content border */
}
.tabitem { /* Style the content area of the tab */
    border: 1px solid #dee2e6;
    border-radius: 0 0 8px 8px;
    padding: 20px;
    background-color: #ffffff;
    margin-top: -1px; /* Overlap with tab navigation border */
}

/* Specific Component Styling within Tabs */

/* JSON Output Code Block */
.json-output-code .cm-editor { /* Target CodeMirror instance used by gr.Code */
    max-height: 400px; /* Limit height */
    border: 1px solid #ced4da;
    border-radius: 5px;
}
/* Force horizontal scroll on the container Gradio puts around the CodeMirror editor */
.json-output-code > div:first-of-type {
    overflow-x: auto !important;
}
.json-output-code pre { /* Ensure preformatted text scrolls */
    /* white-space: pre; Remove this as CodeMirror handles it */
    /* overflow-x: auto !important; Move overflow to container */
    word-wrap: normal; /* Prevent wrapping */
    background-color: #f8f9fa; /* Slight background for code */
    padding: 10px;
}


/* DataFrame Styling */
.gradio-dataframe table {
    width: 100%;
    border-collapse: collapse;
    box-shadow: 0 1px 3px rgba(0,0,0, 0.1);
    border-radius: 5px;
    overflow: hidden; /* Clip shadows */
}
.gradio-dataframe th, .gradio-dataframe td {
    padding: 12px 15px;
    text-align: left;
    border-bottom: 1px solid #e0e0e0;
    vertical-align: top; /* Align content to top */
}
.gradio-dataframe th {
    background-color: #e9ecef; /* Header background */
    font-weight: 600;
    color: #495057;
}
.gradio-dataframe tr:last-child td {
    border-bottom: none;
}
.gradio-dataframe tr:hover {
    background-color: #f1f3f5; /* Row hover effect */
}

/* DataFrame: Test Cases - Steps Column Formatting */
/* Assumes 'Steps to Execute' is the 4th column (index, ID, Scenario, Steps) */
.test-cases-df td:nth-child(4) { /* Check index if needed */
    white-space: pre-wrap; /* Wrap text and respect newlines */
    word-break: break-word; /* Break long words if needed */
    min-width: 300px; /* Ensure minimum width */
    max-width: 500px; /* Add max width */
}

/* DataFrame: Scripts - Code Column Formatting */
/* Assumes 'Python Selenium Code' is the 3rd column (index, ID, Code) */
.scripts-df td:nth-child(3) { /* Check index if needed */
    white-space: pre;       /* Preserve whitespace (indentation, newlines) */
    overflow-x: auto;       /* Allow horizontal scrolling for long lines */
    max-width: 600px;       /* Limit max width before scrolling */
    font-family: 'Courier New', Courier, monospace; /* Monospace font for code */
    background-color: #fdfdfe; /* Very light background for code cell */
    font-size: 0.9em;
    display: block; /* Treat cell content as a block for scrolling */
}

/* Download Buttons */
.gradio-file button {
    background-color: #6c757d; /* Grey */
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 15px;
    font-size: 0.9em;
    transition: background-color 0.2s ease;
    margin-top: 10px; /* Add some space above download buttons */
}
.gradio-file button:hover {
    background-color: #5a6268;
}

/* === Footer Simulation === */
.app-footer {
    text-align: center;
    padding: 15px;
    margin-top: 30px;
    font-size: 0.9em;
    color: #6c757d;
    border-top: 1px solid #dee2e6;
}
"""

# Corrected process_website function
def process_website(url: str, num_test_cases: int):
    """
    Main processing function - Corrected for dynamic updates using yield.
    Orchestrates scraping, test case generation, and script generation.
    """
    # --- Initial State ---
    elements_json_str = "{}" # Start with empty JSON string representation
    elements_filepath = None
    test_cases_df = pd.DataFrame(columns=['Test Case ID', 'Test Scenario', 'Steps to Execute', 'Expected Result'])
    test_cases_filepath = None
    scripts_df = pd.DataFrame(columns=['Test Case ID', 'Python Selenium Code'])
    scripts_filepath = None
    status_updates = []

    def current_outputs():
        # Helper to package the current state for yielding
        return (
            elements_json_str,
            test_cases_df,
            scripts_df,
            elements_filepath,
            test_cases_filepath,
            scripts_filepath,
            "\n".join(status_updates)
        )

    # --- Input Validation ---
    if not url or not url.startswith(('http://', 'https://')):
        status_updates.append("❌ Error: Please enter a valid URL starting with http:// or https://")
        yield current_outputs()
        return

    try:
        status_updates.append("▶️ Processing started...")
        yield current_outputs()

        # --- Task 1: Web Scraping ---
        status_updates.append(f"\n🔄 [1/3] Scraping UI elements from {url}...")
        yield current_outputs() # Update status BEFORE the long call

        elements_data = extract_elements(url)

        if not elements_data:
            status_updates.append("❌ Error: Failed to extract elements. Check URL or website structure.")
            yield current_outputs() # Show error
            return

        elements_json_str = json.dumps(elements_data, indent=4)
        temp_elements_filename = os.path.join(OUTPUT_DIR, f"elements_{os.path.basename(url).split('.')[0]}.json")
        elements_filepath = save_elements_to_json(elements_data, filename=os.path.basename(temp_elements_filename))
        status_updates.append(f"   ✅ Extracted {len(elements_data)} elements. Saved to {elements_filepath}")
        yield current_outputs() # Update status AND show elements JSON

        # Limit element data size sent to AI
        max_elements_for_ai = 100
        if len(elements_data) > max_elements_for_ai:
             elements_json_str_for_ai = json.dumps(elements_data[:max_elements_for_ai], indent=2)
             status_updates.append(f"   ℹ️ Note: Using first {max_elements_for_ai} elements for AI analysis due to size.")
             yield current_outputs() # Show the note immediately
        else:
             elements_json_str_for_ai = json.dumps(elements_data, indent=2)

        # --- Task 2: Test Case Generation ---
        status_updates.append(f"\n🧠 [2/3] Generating {num_test_cases} test cases using GenAI...")
        yield current_outputs() # Update status BEFORE the long call

        generated_tc_df = generate_test_cases(elements_json_str_for_ai, url, num_test_cases)

        # Check for generation errors reflected in the DataFrame
        generation_failed = generated_tc_df.empty or \
                            generated_tc_df['Test Case ID'].isin(['PARSE_ERROR', 'API_ERROR', 'ERROR']).any()

        if generation_failed:
            status_updates.append("   ⚠️ Warning: Failed to generate valid test cases or encountered an error. See table for details.")
            if not generated_tc_df.empty:
                 test_cases_df = generated_tc_df # Display the error DF
                 temp_tc_filename = os.path.join(OUTPUT_DIR, f"test_cases_{os.path.basename(url).split('.')[0]}_error.xlsx")
                 test_cases_filepath = save_test_cases_to_excel(test_cases_df, filename=os.path.basename(temp_tc_filename))
            else:
                 test_cases_filepath = None # No file if df is completely empty
            yield current_outputs() # Update status and show error DF

            # Stop if parsing failed completely or DF is empty
            if test_cases_df.empty or 'PARSE_ERROR' in test_cases_df['Test Case ID'].values:
                 status_updates.append("   🛑 Stopping process due to critical test case generation failure.")
                 yield current_outputs()
                 return
        else:
            test_cases_df = generated_tc_df # Update the main DF with successful results
            temp_tc_filename = os.path.join(OUTPUT_DIR, f"test_cases_{os.path.basename(url).split('.')[0]}.xlsx")
            test_cases_filepath = save_test_cases_to_excel(test_cases_df, filename=os.path.basename(temp_tc_filename))
            status_updates.append(f"   ✅ Generated {len(test_cases_df)} test cases. Saved to {test_cases_filepath}")
            yield current_outputs() # Update status and show test cases DF


        # --- Task 3: Selenium Script Generation ---
        status_updates.append(f"\n🐍 [3/3] Generating Selenium scripts...")
        yield current_outputs() # Update status BEFORE starting script generation

        scripts_data = []
        # Filter out potential error rows before iterating
        valid_test_cases_df = test_cases_df[~test_cases_df['Test Case ID'].isin(['API_ERROR', 'ERROR', 'PARSE_ERROR'])]

        if valid_test_cases_df.empty and not generation_failed:
             status_updates.append("   ℹ️ No valid test cases found to generate scripts for (check previous warnings).")
             yield current_outputs()
        elif not valid_test_cases_df.empty:
            status_updates.append(f"    Mapping {len(valid_test_cases_df)} test cases to scripts...")
            yield current_outputs() # Show count before starting loop

            for index, test_case in valid_test_cases_df.iterrows():
                tc_id = test_case.get('Test Case ID', f'Row_{index}')
                status_updates.append(f"      ⏳ Generating script for: {tc_id}...")
                # Yield BEFORE the AI call for this script to show "Generating..." status
                yield current_outputs()

                script_code = generate_selenium_script(test_case.to_dict(), elements_json_str_for_ai, url)
                scripts_data.append({
                    'Test Case ID': tc_id,
                    'Python Selenium Code': script_code
                })
                # Note: We collect all scripts first, then update the DataFrame *once* after the loop
                # This prevents the DataFrame UI from flickering heavily during the loop.
                # The status log will show progress for each script.

            # After the loop, create and yield the final scripts DataFrame
            scripts_df = pd.DataFrame(scripts_data)
            temp_scripts_filename = os.path.join(OUTPUT_DIR, f"test_scripts_{os.path.basename(url).split('.')[0]}.xlsx")
            scripts_filepath = save_scripts_to_excel(scripts_data, filename=os.path.basename(temp_scripts_filename))
            status_updates.append(f"   ✅ Generated {len(scripts_data)} scripts. Saved to {scripts_filepath}")
            yield current_outputs() # Update status AND show the scripts DF

        else: # Case where TC generation had errors but didn't stop the process
             status_updates.append("   ℹ️ Skipping script generation due to previous errors in test case generation.")
             yield current_outputs()


        status_updates.append("\n\n🎉 Processing finished successfully!")
        yield current_outputs() # Final successful state

    except Exception as e:
        logging.error(f"Critical error in process_website for {url}: {e}", exc_info=True)
        status_updates.append(f"\n\n❌ CRITICAL ERROR: An unexpected error occurred: {str(e)}")
        yield current_outputs() # Yield final state with error message


# --- Gradio Interface Definition (Keep the layout from the previous version) ---
with gr.Blocks(theme=gr.themes.Soft(primary_hue="blue", secondary_hue="sky"), css=custom_css) as demo:

    # --- Header ---
    with gr.Row():
        gr.HTML("""
            <div class="app-header">
                <h1>🤖 AI-Driven Test Generation Prototype 🧪</h1>
                <p>Extract UI Elements → Generate Test Cases → Create Selenium Scripts</p>
            </div>
        """)

    # --- Input Controls ---
    with gr.Group(elem_classes="control-section"):
        with gr.Row():
             with gr.Column(scale=3):
                  url_input = gr.Textbox(
                      label="Website URL",
                      placeholder="e.g., https://demoblaze.com",
                      info="Enter the full public URL of the website to analyze."
                  )
             with gr.Column(scale=1):
                  num_cases_input = gr.Slider(
                      minimum=1, maximum=10, value=3, step=1, # Default to 3
                      label="Number of Test Cases",
                      info="How many test cases should the AI generate?"
                  )
        # Use elem_id for more specific CSS targeting if needed
        start_button = gr.Button("✨ Analyze Website and Generate Tests ✨", variant="primary", elem_id="generate-button")


    # --- Status / Logs ---
    with gr.Accordion("📊 Status & Logs", open=True): # Open by default
         status_output = gr.Textbox(
             label="Processing Log",
             lines=12,
             interactive=False,
             show_copy_button=True
         )

    # --- Results Section ---
    with gr.Column(elem_classes="results-section"):
        gr.Markdown("## Results")
        with gr.Tabs():
            with gr.TabItem("📄 Extracted UI Elements"):
                elements_output = gr.Code(
                    label="elements.json (Preview - scroll horizontally if needed)",
                    language="json",
                    interactive=False,
                    elem_classes="json-output-code" # Apply class for CSS targeting
                )
                download_elements = gr.File(label="Download elements.json", scale=0) # Make button smaller

            with gr.TabItem("✅ Generated Test Cases"):
                test_cases_output = gr.DataFrame(
                    label="Test Cases (Steps column supports multi-line)",
                    interactive=False,
                    wrap=True, # Allow text wrapping generally
                    elem_classes="test-cases-df" # Apply class for CSS targeting
                 )
                download_test_cases = gr.File(label="Download test_cases.xlsx", scale=0)

            with gr.TabItem("🐍 Generated Selenium Scripts"):
                scripts_output = gr.DataFrame(
                    label="Selenium Scripts (Code column preserves formatting & scrolls)",
                    interactive=False,
                    wrap=False, # Disable wrapping for code column
                    elem_classes="scripts-df" # Apply class for CSS targeting
                )
                download_scripts = gr.File(label="Download test_scripts.xlsx", scale=0)

    # --- Footer ---
    with gr.Row():
         gr.HTML("""
            <div class="app-footer">
                AI Test Generator Prototype | Using OpenAI Compatible API 
            </div>
         """)


    # --- Event Handling (Ensure outputs match the yielded tuple order) ---
    start_button.click(
        fn=process_website,
        inputs=[url_input, num_cases_input],
        outputs=[
            elements_output,        # 1st element in yielded tuple
            test_cases_output,      # 2nd
            scripts_output,         # 3rd
            download_elements,      # 4th
            download_test_cases,    # 5th
            download_scripts,       # 6th
            status_output           # 7th
        ]
    )

    # --- Examples ---
    gr.Examples(
        examples=[
            ["https://demoblaze.com", 5],
            ["http://the-internet.herokuapp.com/login", 4],
            ["https://www.wikipedia.org/", 3]
        ],
        inputs=[url_input, num_cases_input],
        label="Example Websites",
        elem_id="examples-container" # Optional ID for styling
    )

# --- Launch the Application ---
if __name__ == "__main__":
    print("Starting Gradio app with enhanced UI and corrected dynamic updates...")
    demo.launch(debug=True) # debug=True helps see errors

