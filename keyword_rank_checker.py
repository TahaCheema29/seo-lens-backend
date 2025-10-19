import asyncio
import time
import json
import requests
from typing import List, Dict, Optional
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from logger_config import setup_logger
from urllib.parse import quote_plus
import re
from config import GOOGLE_API_KEY, GOOGLE_CSE_ID

logger = setup_logger(__name__)

class KeywordRankChecker:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.results = []
    

    async def search_google_cse(self, keyword: str, max_results: int = 100) -> List[Dict]:
        """Search using Google Custom Search Engine API - most reliable method"""
        try:
            # Google Custom Search API endpoint
            api_url = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                'key': GOOGLE_API_KEY,
                'cx': GOOGLE_CSE_ID,
                'q': keyword,
                'num': min(max_results, 10),  # Google CSE API limits to 10 results per request
                'safe': 'off',
                'fields': 'items(title,link,snippet)'
            }
            
            logger.info(f"Searching Google CSE API for: {keyword}")
            response = requests.get(api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                if 'items' in data:
                    for idx, item in enumerate(data['items'], 1):
                        try:
                            results.append({
                                'position': idx,
                                'title': item.get('title', 'No title'),
                                'url': item.get('link', 'No URL'),
                                'snippet': item.get('snippet', 'No snippet')
                            })
                        except Exception as e:
                            logger.warning(f"Error parsing CSE result {idx}: {e}")
                            continue
                
                logger.info(f"Google CSE API found {len(results)} results")
                return results
            else:
                logger.error(f"Google CSE API request failed with status {response.status_code}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Google CSE API search failed for '{keyword}': {e}")
            return []

    async def search_startpage(self, keyword: str, max_results: int = 100) -> List[Dict]:
        """Search using Startpage.com - privacy-focused search that's less protected"""
        try:
            search_url = f"https://www.startpage.com/sp/search?query={quote_plus(keyword)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
            }
            
            logger.info(f"Searching Startpage for: {keyword}")
            response = requests.get(search_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Startpage result selectors
                search_results = soup.find_all('div', class_='w-gl__result')
                
                for idx, result in enumerate(search_results, 1):
                    try:
                        # Extract title
                        title_element = result.find('h3') or result.find('a', class_='w-gl__result-title')
                        title = title_element.get_text().strip() if title_element else "No title"
                        
                        # Extract URL
                        link_element = result.find('a', class_='w-gl__result-title') or result.find('a', href=True)
                        url = link_element.get('href') if link_element else "No URL"
                        
                        # Clean URL if it's a Startpage redirect
                        if url.startswith('/sp/click'):
                            # Extract real URL from Startpage redirect
                            onclick = link_element.get('onclick', '') if link_element else ''
                            if 'url=' in onclick:
                                url = onclick.split('url=')[1].split('&')[0]
                        
                        # Extract snippet
                        snippet_element = result.find('p', class_='w-gl__description') or result.find('div', class_='w-gl__description')
                        snippet = snippet_element.get_text().strip() if snippet_element else "No snippet"
                        
                        if url and url.startswith('http'):
                            results.append({
                                'position': idx,
                                'title': title,
                                'url': url,
                                'snippet': snippet
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error parsing Startpage result {idx}: {e}")
                        continue
                
                logger.info(f"Startpage found {len(results)} results")
                return results
            else:
                logger.error(f"Startpage request failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Startpage search failed for '{keyword}': {e}")
            return []

    async def search_duckduckgo_improved(self, keyword: str, max_results: int = 100) -> List[Dict]:
        """Improved DuckDuckGo search with better parsing"""
        try:
            # Use DuckDuckGo instant answer API
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(keyword)}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            logger.info(f"Searching DuckDuckGo improved for: {keyword}")
            response = requests.get(search_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # DuckDuckGo result selectors - try multiple
                selectors = [
                    'div.result',
                    'div.web-result',
                    'div[data-result]',
                    '.result__body',
                    'div.result__snippet'
                ]
                
                search_results = []
                for selector in selectors:
                    search_results = soup.select(selector)
                    if search_results:
                        logger.info(f"DuckDuckGo found {len(search_results)} results using {selector}")
                        break
                
                # If no results found with selectors, look for any links
                if not search_results:
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        text = link.get_text().strip()
                        
                        # Skip DuckDuckGo internal links
                        if (href and href.startswith('http') and 
                            'duckduckgo.com' not in href and 
                            text and len(text) > 5):
                            
                            # Clean DuckDuckGo redirect URLs
                            if '/l/?uddg=' in href:
                                href = href.split('/l/?uddg=')[1]
                            elif '/l/?kh=-1&uddg=' in href:
                                href = href.split('/l/?kh=-1&uddg=')[1]
                            
                            search_results.append({
                                'title': text,
                                'url': href,
                                'snippet': 'No snippet'
                            })
                    
                    logger.info(f"DuckDuckGo fallback found {len(search_results)} results")
                
                # Convert to standard format
                for idx, result in enumerate(search_results, 1):
                    try:
                        if isinstance(result, dict):
                            title = result.get('title', 'No title')
                            url = result.get('url', '')
                            snippet = result.get('snippet', 'No snippet')
                        else:
                            title_element = result.find('a', class_='result__a') or result.find('h2') or result.find('a', href=True)
                            title = title_element.get_text().strip() if title_element else "No title"
                            
                            link_element = result.find('a', href=True) or title_element
                            url = link_element.get('href') if link_element else "No URL"
                            
                            snippet_element = result.find('a', class_='result__snippet') or result.find('div', class_='result__snippet')
                            snippet = snippet_element.get_text().strip() if snippet_element else "No snippet"
                        
                        if url and url.startswith('http'):
                            results.append({
                                'position': idx,
                                'title': title,
                                'url': url,
                                'snippet': snippet
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error parsing DuckDuckGo result {idx}: {e}")
                        continue
                
                logger.info(f"DuckDuckGo improved found {len(results)} results")
                return results
            else:
                logger.error(f"DuckDuckGo request failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"DuckDuckGo improved search failed for '{keyword}': {e}")
            return []

    async def search_bing(self, keyword: str, max_results: int = 100) -> List[Dict]:
        """Search using Bing Web Search API - real results"""
        try:
            # Bing Web Search API endpoint (free tier: 1000 queries/month)
            # You can get a free API key from: https://azure.microsoft.com/en-us/services/cognitive-services/bing-web-search-api/
            
            # For now, let's use a simple web scraping approach with better stealth
            search_url = f"https://www.bing.com/search?q={quote_plus(keyword)}&count={max_results}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            logger.info(f"Searching Bing for: {keyword}")
            response = requests.get(search_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Bing search result selectors
                search_results = soup.find_all('li', class_='b_algo')
                
                for idx, result in enumerate(search_results, 1):
                    try:
                        # Extract title
                        title_element = result.find('h2') or result.find('a')
                        title = title_element.get_text().strip() if title_element else "No title"
                        
                        # Extract URL
                        link_element = result.find('a', href=True)
                        url = link_element.get('href') if link_element else "No URL"
                        
                        # Extract snippet
                        snippet_element = result.find('p') or result.find('div', class_='b_caption')
                        snippet = snippet_element.get_text().strip() if snippet_element else "No snippet"
                        
                        if url and url.startswith('http'):
                            results.append({
                                'position': idx,
                                'title': title,
                                'url': url,
                                'snippet': snippet
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error parsing Bing result {idx}: {e}")
                        continue
                
                logger.info(f"Found {len(results)} results from Bing")
                return results
            else:
                logger.error(f"Bing request failed with status {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Bing search failed for '{keyword}': {e}")
            return []

    async def search_with_selenium(self, page, keyword: str, max_results: int = 100) -> List[Dict]:
        """Use Playwright with more realistic browser behavior"""
        try:
            # Set very realistic browser settings
            await page.set_viewport_size({"width": 1920, "height": 1080})
            
            # Set realistic headers
            await page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            })
            
            # Visit Google homepage first
            await page.goto("https://www.google.com", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Try to find and fill search box
            search_box = await page.query_selector('input[name="q"]')
            if search_box:
                await search_box.fill(keyword)
                await search_box.press("Enter")
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(3000)
                
                # Extract results
                html = await page.content()
                soup = BeautifulSoup(html, 'html.parser')
                results = []
                
                # Try multiple selectors for Google results
                selectors = ['div.g', '.tF2Cxc', '.yuRUbf', 'div[data-ved]']
                
                for selector in selectors:
                    search_results = soup.select(selector)
                    if search_results:
                        logger.info(f"Found {len(search_results)} results using selector: {selector}")
                        break
                
                for idx, result in enumerate(search_results, 1):
                    try:
                        title_element = result.find('h3') or result.find('h1')
                        title = title_element.get_text().strip() if title_element else "No title"
                        
                        link_element = result.find('a', href=True)
                        url = link_element.get('href') if link_element else "No URL"
                        
                        if url.startswith('/url?q='):
                            url = url.split('/url?q=')[1].split('&')[0]
                        
                        snippet_element = result.find('span', class_='VuuXrf') or result.find('div', class_='VwiC3b')
                        snippet = snippet_element.get_text().strip() if snippet_element else "No snippet"
                        
                        if url and url.startswith('http'):
                            results.append({
                                'position': idx,
                                'title': title,
                                'url': url,
                                'snippet': snippet
                            })
                            
                    except Exception as e:
                        logger.warning(f"Error parsing result {idx}: {e}")
                        continue
                
                logger.info(f"Found {len(results)} results from Google")
                return results
            else:
                logger.error("Could not find Google search box")
                return []
                
        except Exception as e:
            logger.error(f"Selenium search failed for '{keyword}': {e}")
            return []


    async def search_google(self, page, keyword: str, max_results: int = 100) -> List[Dict]:
        """Backup Google search method - simplified"""
        try:
            logger.info(f"Attempting Google search for: {keyword}")
            
            # Simple direct search
            search_url = f"https://www.google.com/search?q={quote_plus(keyword)}"
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # Check if we got CAPTCHA
            html = await page.content()
            if "captcha" in html.lower() or "unusual traffic" in html.lower():
                logger.warning("CAPTCHA detected on Google, skipping...")
                return []
            
            # Try to extract results
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            # Look for search results
            search_results = soup.find_all('div', class_='g')
            
            for idx, result in enumerate(search_results, 1):
                try:
                    title_element = result.find('h3')
                    title = title_element.get_text().strip() if title_element else "No title"
                    
                    link_element = result.find('a', href=True)
                    url = link_element.get('href') if link_element else "No URL"
                    
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    
                    snippet_element = result.find('span', class_='VuuXrf') or result.find('div', class_='VwiC3b')
                    snippet = snippet_element.get_text().strip() if snippet_element else "No snippet"
                    
                    if url and url.startswith('http'):
                        results.append({
                            'position': idx,
                            'title': title,
                            'url': url,
                            'snippet': snippet
                        })
                        
                except Exception as e:
                    logger.warning(f"Error parsing Google result {idx}: {e}")
                    continue
            
            logger.info(f"Google search found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Google search failed for '{keyword}': {e}")
            return []
    
    async def check_keyword_rank(self, keyword: str, target_domain: str = None, max_results: int = 100) -> Dict:
        """Check the ranking position of a keyword for a specific domain"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                # Set user agent to avoid detection
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # Use Google Custom Search Engine API (most reliable)
                search_results = await self.search_google_cse(keyword, max_results)
                
                # If CSE fails, try Startpage as fallback
                if not search_results:
                    logger.info("Google CSE API failed, trying Startpage...")
                    search_results = await self.search_startpage(keyword, max_results)
                
                # If that fails, try DuckDuckGo as last resort
                if not search_results:
                    logger.info("Startpage search failed, trying DuckDuckGo...")
                    search_results = await self.search_duckduckgo_improved(keyword, max_results)
                
                # Find target domain position if specified
                target_position = None
                if target_domain:
                    # Clean target domain for better matching
                    clean_target_domain = target_domain.lower().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
                    
                    for result in search_results:
                        result_url = result['url'].lower()
                        # Check multiple domain variations
                        if (clean_target_domain in result_url or 
                            result_url.endswith(clean_target_domain) or
                            f'.{clean_target_domain}' in result_url):
                            target_position = result['position']
                            logger.info(f"Found {target_domain} at position {target_position} for keyword '{keyword}'")
                            break
                
                result = {
                    'keyword': keyword,
                    'target_domain': target_domain,
                    'target_position': target_position,
                    'total_results': len(search_results),
                    'search_results': search_results,
                    'timestamp': time.time(),
                    'date': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                logger.info(f"Keyword '{keyword}' - Position: {target_position if target_position else 'Not found'}")
                return result
                
            finally:
                await browser.close()
    
    async def check_multiple_keywords(self, keywords: List[str], target_domain: str = None, max_results: int = 100) -> List[Dict]:
        """Check ranking positions for multiple keywords"""
        results = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                # Set user agent to avoid detection
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                for keyword in keywords:
                    logger.info(f"Checking keyword: {keyword}")
                    result = await self.check_keyword_rank(keyword, target_domain, max_results)
                    results.append(result)
                    
                    # Add delay between searches to avoid rate limiting
                    await asyncio.sleep(2)
                    
            finally:
                await browser.close()
        
        return results
    
    def save_results(self, results: List[Dict], filename: str = None) -> str:
        """Save results to JSON file"""
        if filename is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"keyword_rank_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {filename}")
        return filename
    
    def print_summary(self, results: List[Dict], show_debug: bool = False):
        """Print a summary of ranking results"""
        print("\n" + "="*60)
        print("KEYWORD RANKING SUMMARY")
        print("="*60)
        
        for result in results:
            keyword = result['keyword']
            position = result['target_position']
            domain = result['target_domain']
            search_results = result.get('search_results', [])
            
            print(f"\nKeyword: {keyword}")
            print(f"Domain: {domain}")
            print(f"Total results found: {len(search_results)}")
            
            if position:
                print(f"Position: #{position}")
                if position <= 10:
                    print("Status: ✅ First page!")
                elif position <= 20:
                    print("Status: 🟡 Second page")
                else:
                    print("Status: 🔴 Beyond second page")
            else:
                print("Position: Not found in top 100")
                print("Status: ❌ Not ranking")
                
                # Debug: Show first few results to help troubleshoot
                if show_debug and search_results:
                    print("\n🔍 DEBUG - First 5 search results:")
                    for i, res in enumerate(search_results[:5], 1):
                        print(f"  {i}. {res['title']} - {res['url']}")
            
            print("-" * 40)


async def main():
    """Example usage of the KeywordRankChecker"""
    checker = KeywordRankChecker(headless=True)
    
    # Example keywords and domain to check
    keywords = [
        "git tutorial",
        "version control"
    ]
    target_domain = "w3schools.com"  # Clean domain format
    
    print("Starting keyword rank checking...")
    
    # Check multiple keywords
    results = await checker.check_multiple_keywords(
        keywords=keywords,
        target_domain=target_domain,
        max_results=100
    )
    
    # Print summary with debug info
    checker.print_summary(results, show_debug=True)
    
    # Save results
    filename = checker.save_results(results)
    print(f"\nDetailed results saved to: {filename}")


if __name__ == "__main__":
    asyncio.run(main())
