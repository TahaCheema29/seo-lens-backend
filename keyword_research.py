import requests

# 🔑 Replace these with your credentials
API_KEY = "AIzaSyDCaC6114aro5xd4HrRON-vJi1MX4fZv_k"
CX = "95ca36ed8cab64023"  # CSE ID from Google Custom Search

def get_keyword_rank(keyword: str, domain: str, max_pages: int = 10):
    """
    Returns the search rank (1-100) and URL of a domain for a given keyword using Google Custom Search API.
    """
    start = 1  # Google results start index (1-based)
    
    for page in range(max_pages):  # 10 pages * 10 results = top 100
        # API request URL
        url = (
            f"https://www.googleapis.com/customsearch/v1?"
            f"q={keyword}&key={API_KEY}&cx={CX}&start={start}"
        )

        response = requests.get(url)
        if response.status_code != 200:
            print("❌ API request failed:", response.text)
            break

        data = response.json()
        items = data.get("items", [])

        for idx, item in enumerate(items):
            link = item.get("link", "")
            if domain.lower() in link.lower():
                # Found domain → return rank
                rank = start + idx
                return rank, link

        # If there are no more results, stop early
        if "nextPage" not in data.get("queries", {}):
            break

        start += 10  # Move to next page (10 results per page)

    return None, None  # Not found in top 100


if __name__ == "__main__":
    # Example usage
    keyword = "best coffee shop in Lahore"
    domain = "https://loafology.com/"

    rank, url = get_keyword_rank(keyword, domain)

    if rank:
        print(f"✅ '{domain}' ranks #{rank} for '{keyword}'")
        print(f"🔗 {url}")
    else:
        print(f"❌ '{domain}' not found in top 100 results for '{keyword}'")
