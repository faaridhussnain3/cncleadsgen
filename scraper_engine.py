import time
import os
import sys
import re
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

TARGET_COUNT = 20000
LINKS_FILE = "links.md"
URLS_TO_SCRAPE_FILE = "urls_to_scrape.md"
LOGS_DIR = "logs"
NUM_WORKERS = 4

EXCLUDE_DOMAINS = [
    'google.', 'gstatic.', 'ggpht.', 'youtube.', 'facebook.', 'linkedin.',
    'instagram.', 'twitter.', 'yelp.', 'yellowpages.', 'mapquest.', 'wikipedia.',
    'amazon.', 'ebay.', 'mfgbase.', 'iqsdirectory.', 'thomasnet.', 'rfqusa.',
    'wixsite.', 'getjobber.', 'job5156.', 'zhaopin.', '51job.', 'liepin.',
    'bosszhipin.', 'baidu.', 'reddit.', 'github.', 'pinterest.'
]

def setup_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-infobars')
    options.add_argument('--window-size=1280,800')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Increase page load timeout to prevent "Read timed out"
    options.page_load_strategy = 'eager'
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(60) # Fail fast on stalled pages instead of 120s hang
    return driver

def load_existing_links():
    links = set()
    for fpath in [LINKS_FILE, URLS_TO_SCRAPE_FILE]:
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                for line in f:
                    clean = line.strip().rstrip('.,;:/"\'')
                    if clean.startswith('http'):
                        links.add(clean)
    return links

def append_to_links(links):
    if not links:
        return
    for fpath in [LINKS_FILE, URLS_TO_SCRAPE_FILE]:
        prefix = ""
        if os.path.exists(fpath):
            with open(fpath, 'r', encoding='utf-8') as f:
                content = f.read()
                if content and not content.endswith('\n'):
                    prefix = "\n"

        with open(fpath, 'a', encoding='utf-8') as f:
            f.write(prefix)
            for link in links:
                f.write(f"{link}\n")

def is_valid_company_website(url):
    if not url or not url.startswith('http'):
        return False
    domain = urllib.parse.urlparse(url).netloc.lower()
    for ex in EXCLUDE_DOMAINS:
        if ex in domain:
            return False
    return True

def load_queries_from_md(md_path):
    pending_queries = []
    if os.path.exists(md_path):
        with open(md_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith('- ') and not stripped.endswith('[DONE]'):
                    q = stripped[2:].strip()
                    pending_queries.append(q)
    return pending_queries

def mark_query_as_done(md_path, target_query):
    if not os.path.exists(md_path):
        return
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- '):
            q_text = stripped[2:].replace(' [DONE]', '').strip()
            if q_text == target_query:
                updated.append(f"- {q_text} [DONE]\n")
            else:
                updated.append(line)
        else:
            updated.append(line)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.writelines(updated)

def append_md_log(log_path, query, status, extracted_urls, error_msg=None):
    os.makedirs(LOGS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ensure log header exists
    if not os.path.exists(log_path):
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"# 📜 Execution Log - {os.path.basename(log_path)}\n\n")

    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"### 🔍 `[{timestamp}]` {query}\n")
        f.write(f"- **Status:** `{status}`\n")
        if status == "SUCCESS":
            f.write(f"- **Extracted New URLs ({len(extracted_urls)}):**\n")
            for u in extracted_urls:
                f.write(f"  - [{u}]({u})\n")
        elif status == "ZERO_NEW":
            f.write("- **Extracted New URLs:** 0 (All results were already saved or filtered)\n")
        elif status == "ERROR":
            f.write(f"- **Error Details:** `{error_msg}`\n")
        f.write("\n---\n\n")

def scrape_single_query(query, existing_links_set):
    encoded_search = urllib.parse.quote(query)
    maps_url = f"https://www.google.com/maps/search/{encoded_search}"

    driver = None
    extracted = []
    error = None
    try:
        driver = setup_driver()
        driver.get(maps_url)
        time.sleep(2.0)

        try:
            scroll_panel = driver.find_element(By.XPATH, '//div[contains(@aria-label, "Results for")]')
            for _ in range(2):
                driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scroll_panel)
                time.sleep(0.8)
        except Exception:
            pass

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/url?q=' in href:
                actual_url = href.split('/url?q=')[1].split('&')[0]
                actual_url = urllib.parse.unquote(actual_url).rstrip('.,;:/"\'')
                if is_valid_company_website(actual_url) and actual_url not in existing_links_set:
                    extracted.append(actual_url)
            elif is_valid_company_website(href) and href not in existing_links_set:
                extracted.append(href.rstrip('.,;:/"\''))

    except Exception as e:
        error = str(e)
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    return list(set(extracted)), error

def run_category_engine(category_name, query_md_file, log_md_file):
    existing_links = load_existing_links()
    pending_queries = load_queries_from_md(query_md_file)

    print(f"🏭 Starting Category Scraper: {category_name}")
    print(f"📄 Query File: '{query_md_file}' | Pending Queries to Run: {len(pending_queries)}")
    print(f"📜 Log File: '{log_md_file}'")
    print(f"📊 Current Unique Links in links.md: {len(existing_links)} / Goal: {TARGET_COUNT}\n")

    if not pending_queries:
        print(f"🎉 All queries in '{query_md_file}' are already marked [DONE]!")
        return

    new_total = 0

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(scrape_single_query, q, existing_links): q for q in pending_queries}

        for future in as_completed(futures):
            q = futures[future]
            try:
                extracted_urls, error = future.result()

                if error:
                    print(f"⚠️ [{category_name}] Error on '{q}': {error}")
                    append_md_log(log_md_file, q, "ERROR", [], error_msg=error)
                else:
                    new_urls = [u for u in extracted_urls if u not in existing_links]

                    # Mark query as DONE in MD file
                    mark_query_as_done(query_md_file, q)

                    if new_urls:
                        print(f"✨ [{category_name}] '{q}' -> Found {len(new_urls)} NEW websites!")
                        for u in new_urls:
                            existing_links.add(u)
                            new_total += 1
                        append_to_links(new_urls)
                        append_md_log(log_md_file, q, "SUCCESS", new_urls)
                    else:
                        print(f"ℹ️ [{category_name}] '{q}' -> Done (0 new URLs).")
                        append_md_log(log_md_file, q, "ZERO_NEW", [])

                print(f"📈 [{category_name}] Total Links in links.md: {len(existing_links)}")

            except Exception as e:
                print(f"❌ Error executing task for '{q}': {e}")

    print(f"\n🎉 [{category_name}] Run finished! Added {new_total} new company websites to links.md.")
