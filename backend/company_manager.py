# backend/company_manager.py
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import validators
import json
import re
import time

from backend.llm_client import generate_response
from backend.vector_store.vector_store import save_to_vector_index

USER_AGENT = "Mozilla/5.0 (compatible; CompanyBot/1.0; +https://example.com)"
CHUNK_SIZE = 700
CRAWL_DELAY = 1  # seconds between requests

# -----------------------------------------------------
# Fetch textual content from a single page
# -----------------------------------------------------
def fetch_page_text(url):
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
    except Exception as e:
        return "", f"Error fetching {url}: {str(e)}"

    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript", "svg", "header", "footer"]):
        tag.decompose()

    main = soup.find(["main", "article"])
    if main:
        text = main.get_text(separator="\n", strip=True)
    else:
        parts = [
            t.get_text(separator=" ", strip=True)
            for t in soup.find_all(["h1","h2","h3","p","div"])
            if len(t.get_text(strip=True)) > 10
        ]
        text = "\n".join(parts)
    return text, None

# -----------------------------------------------------
# Crawl all internal pages of the website
# -----------------------------------------------------
def crawl_website(base_url, max_pages=50):
    """Crawl website and fetch text from internal pages (limited to max_pages)."""
    visited = set()
    to_visit = [base_url]
    all_text = ""

    domain = urlparse(base_url).netloc

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)

        text, err = fetch_page_text(url)
        if err:
            print(f"⚠️ {err}")
            continue
        if text:
            all_text += "\n" + text

        # find internal links
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT})
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                href = a['href']
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)
                if parsed.netloc == domain and full_url not in visited and full_url not in to_visit:
                    to_visit.append(full_url)
        except Exception:
            continue

        time.sleep(CRAWL_DELAY)

    return all_text

# -----------------------------------------------------
# Extract company details using LLM
# -----------------------------------------------------
def extract_branding_from_text(text):
    limited_text = text[:4000] if len(text) > 4000 else text
    prompt = f"""
You are analyzing a company's website content. Extract key information and return ONLY a valid JSON object.
Extract the following info: company_name, tagline, tone, short_about, products (max 5), contact_email, contact_phone, address
Return ONLY JSON.
Website Content:
\"\"\" 
{limited_text}
\"\"\" 
"""
    try:
        summary = generate_response(prompt)
        json_match = re.search(r'\{[\s\S]*\}', summary)
        data = json.loads(json_match.group(0)) if json_match else {}
        for field in [
            "company_name","tagline","tone","short_about",
            "products","contact_email","contact_phone","address"
        ]:
            if field not in data:
                data[field] = "" if field != "products" else []
        return data
    except Exception as e:
        print(f"⚠️ LLM extraction failed: {e}")
        return {
            "company_name": "Unknown Company",
            "tagline": "",
            "tone": "professional and helpful",
            "short_about": "Company information could not be extracted.",
            "products": [],
            "contact_email": "",
            "contact_phone": "",
            "address": ""
        }

# -----------------------------------------------------
# Build full company profile
# -----------------------------------------------------
def build_company_profile(url, max_pages=50):
    print(f"🔍 Crawling website: {url}")
    text = crawl_website(url, max_pages=max_pages)

    if not text or len(text.strip()) < 40:
        return {"error": "No usable text found on website", "success": False}

    print(f"✅ Fetched {len(text)} characters from website")
    try:
        from langdetect import detect
        lang = detect(text)
    except Exception:
        lang = "en"
    print(f"🌐 Detected language: {lang}")

    print("🤖 Extracting company profile with LLM...")
    profile = extract_branding_from_text(text)
    profile["lang"] = lang
    profile["website"] = url
    profile["source_text_snippet"] = text[:500]
    profile["success"] = True

    # Split text into chunks
    chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    profile["chunks"] = chunks
    print(f"🧩 Total chunks created: {len(chunks)}")

    # Save website content to domain-specific vector index
    domain = urlparse(url).netloc.replace(".", "_")
    index_name = f"{domain}_index"
    try:
        save_to_vector_index(index_name, text)
        print(f"💾 Website content saved to vector index: {index_name}")
    except Exception as e:
        print(f"⚠️ Failed to save to vector index: {e}")

    print(f"✅ Profile created for: {profile.get('company_name','Unknown')}")
    return profile
