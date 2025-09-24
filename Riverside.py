import time
import os
import pdfplumber
import subprocess
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# ----------------------------
# 1. Setup Chrome download preferences
# ----------------------------
download_dir = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(download_dir):
    os.makedirs(download_dir)

chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "plugins.always_open_pdf_externally": True,
    "download.prompt_for_download": False,
    "pdfjs.disabled": True
})

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# ----------------------------
# 2. Open the page and fill login details
# ----------------------------
url = "https://epublic-access.riverside.courts.ca.gov/public-portal/?q=node/385/3473130"
driver.get(url)
time.sleep(3)

# Fill in email
email_input = driver.find_element(By.ID, "edit-name")
email_input.clear()
email_input.send_keys("lotrorimle@gufum.com")

# Fill in password
pass_input = driver.find_element(By.ID, "edit-pass")
pass_input.clear()
pass_input.send_keys("Riversideleodoku@30")

# ----------------------------
# 3. Wait for manual CAPTCHA solve and login
# ----------------------------
print("Please solve the CAPTCHA manually and click 'Log in' in the browser.")
print("Waiting 90 seconds for you to do this...")
time.sleep(60)  # Adjust if needed

# ----------------------------
# 4. Click on 'Print Case Report'
# ----------------------------
try:
    print_button = driver.find_element(By.ID, "casePrintLink")
    print_button.click()
    print("Clicked on 'Print Case Report' button.")
except Exception as e:
    print("Error: Could not find 'Print Case Report' button:", e)
    driver.quit()
    exit()

# ----------------------------
# 5. Wait for PDF download
# ----------------------------
print("Waiting 10 seconds for PDF to download...")
time.sleep(5)
driver.quit()

# ----------------------------
# 6. Find downloaded PDF
# ----------------------------
pdf_files = [f for f in os.listdir(download_dir) if f.lower().endswith(".pdf")]
if not pdf_files:
    print("No PDF downloaded!")
    exit()

pdf_path = os.path.join(download_dir, pdf_files[0])
print(f"PDF downloaded: {pdf_path}")

# ----------------------------
# 7. Open PDF in default viewer
# ----------------------------
print("Opening PDF in default viewer...")
if platform.system() == "Windows":
    os.startfile(pdf_path)
elif platform.system() == "Darwin":  # macOS
    subprocess.call(["open", pdf_path])
else:  # Linux
    subprocess.call(["xdg-open", pdf_path])

# ----------------------------
# 8. Extract data dynamically under multiple start keywords
# ----------------------------
start_keywords = ["OTHER CASES", "CONCURRENT CASE", "CONSECUTIVE CASE",
                  "TRAIL CASE", "OTHER CASE", "CASE"]  # CASE = exact word
end_keyword = "REGISTER OF ACTIONS"

capturing = False
current_headers = []
current_cases = []

with pdfplumber.open(pdf_path) as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if not text:
            continue
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            # Start capturing if line contains any start keyword
            if any((kw == "CASE" and line == "CASE") or (kw != "CASE" and kw.lower() in line.lower())
                   for kw in start_keywords):
                capturing = True
                current_headers = []
                current_cases = []
                continue

            # Stop capturing when REGISTER OF ACTIONS found → print last block
            if capturing and end_keyword.lower() in line.lower():
                if current_headers and current_cases:
                    print("\n" + ", ".join(current_headers))
                    for case_line in current_cases:
                        print(", ".join(case_line.split()))
                capturing = False
                continue

            if capturing:
                # Detect new header row (e.g., Case Number, Expires, etc.)
                if line.lower().startswith("case number"):
                    # Print previous block if data exists
                    if current_headers and current_cases:
                        print("\n" + ", ".join(current_headers))
                        for case_line in current_cases:
                            print(", ".join(case_line.split()))
                        current_cases = []

                    # Set new headers for next block
                    current_headers = [h.strip() for h in line.split()]
                    continue

                # Every line after headers until next header/end → case row
                if current_headers and line:
                    current_cases.append(line)

# Print leftover data if REGISTER OF ACTIONS not found
if current_headers and current_cases:
    print("\n" + ", ".join(current_headers))
    for case_line in current_cases:
        print(", ".join(case_line.split()))
