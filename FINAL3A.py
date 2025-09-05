# import time
# import requests
# import pandas as pd
# from bs4 import BeautifulSoup
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.service import Service
# from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
# from webdriver_manager.chrome import ChromeDriverManager
# import os

# # ================== CLEANUP FUNCTIONS ==================
# def clean_value(val: str) -> str:
#     if not val:
#         return "N/A"
#     s = val.replace("\xa0", " ").strip()
#     return "N/A" if s == "" or s.upper() == "N/A" else s

# def normalize_height(val: str) -> str:
#     if not val:
#         return "N/A"
#     return val.replace("â²", "'").replace("â³", '"').strip() or "N/A"

# def parse_table(table) -> str:
#     if not table:
#         return "N/A"
#     rows = []
#     for tr in table.find_all("tr"):
#         cells = [clean_value(td.get_text(" ", strip=True)) for td in tr.find_all(["th", "td"])]
#         if len(cells) >= 2:
#             rows.append(f"{cells[0]}: {', '.join(cells[1:])}")
#     return ", ".join(rows) if rows else "N/A"

# # ================== SCRAPE SINGLE PROFILE ==================
# def scrape_profile(url: str) -> dict:
#     data = {}
#     try:
#         r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
#         r.raise_for_status()
#         soup = BeautifulSoup(r.text, "html.parser")

#         seen_tables = set()

#         # ---- Scrape normal fields ----
#         for field in soup.select("div.field"):
#             name_el = field.select_one(".name") or field.select_one("span.name, div.name")
#             value_el = field.select_one(".value") or field.select_one("span.value, div.value")
#             if not name_el:
#                 continue
#             key = clean_value(name_el.get_text(strip=True).rstrip(":"))
#             value = clean_value(value_el.get_text(" ", strip=True) if value_el else "N/A")
#             data[key] = value

#         # ---- Normalize Height field ----
#         if "Height" in data:
#             data["Height"] = normalize_height(data["Height"])

#         # ---- Scrape tables (skip duplicates and 'Table') ----
#         for table in soup.find_all("table"):
#             table_label_el = table.find_previous("div", class_="name")
#             table_name = clean_value(table_label_el.get_text(strip=True)) if table_label_el else "Table"
#             if table_name in seen_tables or table_name == "Table":
#                 continue  # skip duplicates and unwanted tables
#             seen_tables.add(table_name)
#             data[table_name] = parse_table(table)

#         data["URL"] = url

#     except Exception as e:
#         data = {"URL": url, "Error": str(e)}

#     return data

# # ================== SAVE DATA PAGE BY PAGE ==================
# def save_to_excel(data_list, output_file):
#     df_new = pd.DataFrame(data_list)
#     if os.path.exists(output_file):
#         df_old = pd.read_excel(output_file)
#         df_all = pd.concat([df_old, df_new], ignore_index=True)
#     else:
#         df_all = df_new
#     df_all.to_excel(output_file, index=False)
#     print(f"Data saved to {output_file}. Total records: {len(df_all)}")

# # ================== MAIN PROCESS ==================
# def scrape_all_pages(base_url, output_file):
#     options = webdriver.ChromeOptions()
#     options.add_argument('--disable-gpu')
#     options.add_argument('--no-sandbox')
#     options.add_argument('--window-size=1920,1080')
#     # options.add_argument('--headless')

#     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
#     wait = WebDriverWait(driver, 20)

#     page_number = 1
#     try:
#         driver.get(base_url)

#         while True:
#             print(f"\n=== Processing Page {page_number} ===")
#             page_data = []

#             # Step 1: Collect profile links on this page (skip ads)
#             for attempt in range(3):
#                 try:
#                     wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.gallery-listing table tr td a")))
#                     links = driver.find_elements(By.CSS_SELECTOR, "div.gallery-listing table tr td a")
#                     page_links = [link.get_attribute("href") for link in links if link.get_attribute("href")]
#                     # Filter out advertisement links
#                     page_links = [link for link in page_links if "mugshots.com" in link and "ad" not in link.lower()]
#                     page_links = list(dict.fromkeys(page_links))  # remove duplicates
#                     print(f"Found {len(page_links)} profile links on page {page_number}.")
#                     break
#                 except StaleElementReferenceException:
#                     print("Stale element, retrying...")
#                     time.sleep(1)
#             else:
#                 print("Failed to fetch links after retries. Skipping page.")
#                 continue

#             # Step 2: Scrape profiles on this page
#             for i, url in enumerate(page_links, 1):
#                 record = scrape_profile(url)
#                 page_data.append(record)
#                 print(f"Scraped {i}/{len(page_links)} on page {page_number}")
#                 time.sleep(0.3)

#             # Step 3: Save data after each page
#             save_to_excel(page_data, output_file)

#             # Step 4: Go to next page
#             try:
#                 next_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.pagination a.next.page")))
#                 driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
#                 time.sleep(1)
#                 driver.execute_script("arguments[0].click();", next_button)
#                 page_number += 1
#                 time.sleep(2)
#             except (NoSuchElementException, TimeoutException):
#                 print("No more pages. Scraping finished.")
#                 break

#     finally:
#         driver.quit()


# # ================== RUN SCRIPT ==================
# if __name__ == "__main__":
#     base_url = "https://mugshots.com/US-States/California/Riverside-County-CA/?name_prefix=X&noimg=1"
#     output_file = "Riverside_Mugshots_x.xlsx"
#     scrape_all_pages(base_url, output_file)


import time
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
import os

# ================== CLEANUP FUNCTIONS ==================
def clean_value(val: str) -> str:
    if not val:
        return "N/A"
    s = val.replace("\xa0", " ").strip()
    return "N/A" if s == "" or s.upper() == "N/A" else s

def normalize_height(val: str) -> str:
    if not val:
        return "N/A"
    return val.replace("â²", "'").replace("â³", '"').strip() or "N/A"

def parse_table(table) -> str:
    """Parse table into key: value pairs and remove duplicate-style rows"""
    if not table:
        return "N/A"
    rows = []
    for tr in table.find_all("tr"):
        cells = [clean_value(td.get_text(" ", strip=True)) for td in tr.find_all(["th", "td"])]
        # Only keep rows that have key:value format (i.e., first column as key, rest as values)
        if len(cells) >= 2:
            rows.append(f"{cells[0]}: {', '.join(cells[1:])}")
    return ", ".join(rows) if rows else "N/A"

# ================== SCRAPE SINGLE PROFILE ==================
def scrape_profile(url: str) -> dict:
    data = {}
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        seen_tables = set()

        # ---- Scrape normal fields ----
        for field in soup.select("div.field"):
            name_el = field.select_one(".name") or field.select_one("span.name, div.name")
            value_el = field.select_one(".value") or field.select_one("span.value, div.value")
            if not name_el:
                continue
            key = clean_value(name_el.get_text(strip=True).rstrip(":"))
            value = clean_value(value_el.get_text(" ", strip=True) if value_el else "N/A")
            data[key] = value

        # ---- Normalize Height field ----
        if "Height" in data:
            data["Height"] = normalize_height(data["Height"])

        # ---- Scrape tables (skip duplicates and 'Table') ----
        for table in soup.find_all("table"):
            table_label_el = table.find_previous("div", class_="name")
            table_name = clean_value(table_label_el.get_text(strip=True)) if table_label_el else "Table"
            if table_name in seen_tables or table_name == "Table":
                continue
            seen_tables.add(table_name)
            data[table_name] = parse_table(table)

        data["URL"] = url

    except Exception as e:
        data = {"URL": url, "Error": str(e)}

    return data

# ================== SAVE DATA PAGE BY PAGE ==================
def save_to_excel(data_list, output_file):
    df_new = pd.DataFrame(data_list)
    if os.path.exists(output_file):
        df_old = pd.read_excel(output_file)
        df_all = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df_all = df_new
    df_all.to_excel(output_file, index=False)
    print(f"Data saved to {output_file}. Total records: {len(df_all)}")

# ================== MAIN PROCESS ==================
def scrape_all_pages(base_url, output_file):
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--window-size=1920,1080')
    # options.add_argument('--headless')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    wait = WebDriverWait(driver, 20)

    page_number = 1
    try:
        driver.get(base_url)

        while True:
            print(f"\n=== Processing Page {page_number} ===")
            page_data = []

            # Step 1: Collect profile links on this page (skip ads)
            try:
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.gallery-listing table tr td a")))
                time.sleep(2)  # ensure all 120 links load
                links = driver.find_elements(By.CSS_SELECTOR, "div.gallery-listing table tr td a")
                page_links = [link.get_attribute("href") for link in links if link.get_attribute("href")]
                page_links = [link for link in page_links if "mugshots.com" in link and "ad" not in link.lower()]
                page_links = list(dict.fromkeys(page_links))
                print(f"Found {len(page_links)} profile links on page {page_number}.")
            except StaleElementReferenceException:
                print("Stale element, retrying page...")
                continue

            # Step 2: Scrape profiles on this page
            for i, url in enumerate(page_links, 1):
                record = scrape_profile(url)
                page_data.append(record)
                print(f"Scraped {i}/{len(page_links)} on page {page_number}")
                time.sleep(0.3)

            # Step 3: Save data after each page
            save_to_excel(page_data, output_file)

            # Step 4: Go to next page
            try:
                next_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.pagination a.next.page")))
                driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", next_button)
                page_number += 1
                time.sleep(2)
            except (NoSuchElementException, TimeoutException):
                print("No more pages. Scraping finished.")
                break

    finally:
        driver.quit()

# ================== RUN SCRIPT ==================
if __name__ == "__main__":
    base_url = "https://mugshots.com/US-States/California/Riverside-County-CA/?name_prefix=X&noimg=1"
    output_file = "Riverside_Mugshots_x2.xlsx"
    scrape_all_pages(base_url, output_file)
