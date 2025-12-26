import requests
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Set a custom user agent so we don't get blocked immediately
HEADERS = {
    'User-Agent': 'PulseDocumentationBot/1.0 (Educational Project; +http://localhost:8501)'
}

def is_valid_link(url, base_domain):
    """
    Checks if we should follow this link. 
    We only want internal links to keep the scope manageable.
    """
    try:
        parsed = urlparse(url)
        # Check if it's the same domain and not an anchor link (starts with #)
        return bool(parsed.netloc) and (parsed.netloc == base_domain) and '#' not in url
    except:
        return False

def crawl_website(start_url, max_limit=3):
    """
    Simple BFS crawler to grab documentation pages.
    """
    visited_urls = set()
    queue = [start_url]
    collected_data = []
    
    # Grab the domain so we don't drift off to other sites (like Twitter/Facebook links)
    base_domain = urlparse(start_url).netloc
    
    print(f"--> Starting crawl on {base_domain}...")

    while queue and len(visited_urls) < max_limit:
        current_url = queue.pop(0)
        
        if current_url in visited_urls:
            continue
            
        try:
            # Add a small delay to be polite to the server
            time.sleep(0.5) 
            
            resp = requests.get(current_url, headers=HEADERS, timeout=5)
            if resp.status_code != 200:
                print(f"Skipping {current_url} - Status {resp.status_code}")
                continue
                
            # Parse HTML
            doc_soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Heuristic: Find the main content.
            # Most docs use <main>, <article>, or a specific div. 
            # Fallback to body if we can't find specific tags.
            content_node = doc_soup.find('main') or doc_soup.find('article') or doc_soup.find('body')
            
            if content_node:
                text_content = content_node.get_text(separator=' ', strip=True)
                
                # Filter out empty pages or pages with just nav links
                if len(text_content) > 200:
                    collected_data.append(f"SOURCE: {current_url}\nTEXT: {text_content[:10000]}") # limit size
                    visited_urls.add(current_url)
                    print(f"   [+] Scraped: {current_url}")
            
            # Find next links to process
            for tag in doc_soup.find_all('a', href=True):
                absolute_link = urljoin(current_url, tag['href'])
                if is_valid_link(absolute_link, base_domain) and absolute_link not in visited_urls:
                    queue.append(absolute_link)
            
        except Exception as e:
            # Just print the error and keep going, don't crash the whole crawler
            print(f"!!! Error parsing {current_url}: {e}")
            
    return collected_data