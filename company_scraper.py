import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
import sys
import os
from datetime import datetime

# Common keywords for CNC machining
INDUSTRIES = ['automotive', 'aerospace', 'medical', 'healthcare', 'defense', 'electronics', 'semiconductor', 'oil and gas', 'energy', 'marine', 'telecommunications', 'robotics']
MATERIALS = ['aluminum', 'steel', 'stainless steel', 'titanium', 'brass', 'copper', 'plastic', 'composites', 'acrylic', 'nylon', 'polycarbonate', 'delrin', 'carbon steel']
PARTS = ['enclosures', 'brackets', 'gears', 'shafts', 'housings', 'panels', 'heatsinks', 'fittings', 'valves', 'flanges', 'fasteners', 'prototypes']

def get_page_soup(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_emails(text):
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return list(set(re.findall(email_pattern, text)))

def extract_certs(text):
    cert_pattern = r'(ISO\s*\d{4}(?:\s*:\s*\d{4})?|AS9100[A-Z]?|ITAR|NIST\s*800-171|NADCAP)'
    return list(set(re.findall(cert_pattern, text, re.IGNORECASE)))

def extract_keywords(text, keyword_list):
    found = []
    text_lower = text.lower()
    for kw in keyword_list:
        if kw.lower() in text_lower:
            found.append(kw)
    return found

def clean_text(soup):
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.extract()
    text = soup.get_text(separator='\n')
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return '\n'.join(chunk for chunk in chunks if chunk)

def get_internal_links(soup, base_url):
    links = {}
    for a in soup.find_all('a', href=True):
        href = a['href']
        text = a.get_text(strip=True).lower()
        full_url = urllib.parse.urljoin(base_url, href)
        if urllib.parse.urlparse(full_url).netloc == urllib.parse.urlparse(base_url).netloc:
            if 'contact' in text or 'contact' in href.lower():
                links['Contact'] = full_url
            elif 'about' in text or 'about' in href.lower():
                links['About'] = full_url
    return links

def scrape_company(base_url):
    if not base_url.startswith('http'):
        base_url = 'https://' + base_url
    
    print(f"Scraping {base_url}...")
    
    data = {
        'url': base_url,
        'emails': set(),
        'certs': set(),
        'industries': set(),
        'materials': set(),
        'parts': set(),
        'pages_content': {}
    }

    # Scrape Home Page
    soup_home = get_page_soup(base_url)
    if not soup_home:
        print("Could not fetch home page. Exiting.")
        return data

    text_home = clean_text(soup_home)
    data['pages_content']['Home'] = text_home
    
    # Find links to About and Contact
    links = get_internal_links(soup_home, base_url)
    print(f"Found pages: {list(links.keys())}")

    # Scrape About and Contact Pages
    for page_name, url in links.items():
        print(f"Scraping {page_name} page ({url})...")
        soup = get_page_soup(url)
        if soup:
            data['pages_content'][page_name] = clean_text(soup)

    # Process all text
    all_text = " ".join(data['pages_content'].values())
    
    data['emails'].update(extract_emails(all_text))
    data['certs'].update(extract_certs(all_text))
    data['industries'].update(extract_keywords(all_text, INDUSTRIES))
    data['materials'].update(extract_keywords(all_text, MATERIALS))
    data['parts'].update(extract_keywords(all_text, PARTS))

    return data

def save_to_markdown(data):
    domain = urllib.parse.urlparse(data['url']).netloc.replace('www.', '')
    filename = f"{domain}_scraped_data.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Company Data: {domain}\n\n")
        f.write(f"**URL:** {data['url']}\n")
        f.write(f"**Date Scraped:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Extracted Information\n\n")
        
        f.write("### Emails Found\n")
        if data['emails']:
            for email in data['emails']:
                f.write(f"- {email}\n")
        else:
            f.write("- None found\n")
        f.write("\n")
        
        f.write("### Certifications Found\n")
        if data['certs']:
            for cert in data['certs']:
                f.write(f"- {cert.upper()}\n")
        else:
            f.write("- None found\n")
        f.write("\n")

        f.write("### Industries Served\n")
        if data['industries']:
            for ind in data['industries']:
                f.write(f"- {ind.title()}\n")
        else:
            f.write("- None found\n")
        f.write("\n")

        f.write("### Materials Worked With\n")
        if data['materials']:
            for mat in data['materials']:
                f.write(f"- {mat.title()}\n")
        else:
            f.write("- None found\n")
        f.write("\n")

        f.write("### Parts Manufactured\n")
        if data['parts']:
            for part in data['parts']:
                f.write(f"- {part.title()}\n")
        else:
            f.write("- None found\n")
        f.write("\n")

        f.write("## Raw Page Content (for further refinement)\n\n")
        for page_name, content in data['pages_content'].items():
            f.write(f"### {page_name} Page\n")
            f.write("```text\n")
            # Truncate if too long, or save it all. We will save it all but trim empty lines
            formatted_content = '\n'.join([line for line in content.splitlines() if line.strip()])
            f.write(formatted_content)
            f.write("\n```\n\n")
            
    print(f"\nSaved data to {filename}")

if __name__ == "__main__":
    urls = []
    
    # If a URL is passed via command line, just use that
    if len(sys.argv) > 1:
        urls.append(sys.argv[1])
    else:
        # Otherwise, read from urls_to_scrape.md
        urls_file = "urls_to_scrape.md"
        if os.path.exists(urls_file):
            print(f"Reading URLs from {urls_file}...")
            with open(urls_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('http'):
                        urls.append(line)
        else:
            print(f"Could not find {urls_file}.")
            urls.append(input("Enter company website URL: "))

    if not urls:
        print("No valid URLs found to scrape.")
    else:
        for url in urls:
            if url.strip():
                print(f"--- Processing: {url} ---")
                scraped_data = scrape_company(url.strip())
                save_to_markdown(scraped_data)
        print("\nAll done!")
