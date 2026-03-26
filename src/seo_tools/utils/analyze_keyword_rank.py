import asyncio
import time
import json
import requests
from typing import List, Dict
from playwright.async_api import async_playwright
from src.config.logger_config import setup_logger
from src.config.settings import settings
from src.seo_tools.schemas.analyze_keyword_rank import AnalyzeKeywordRankResult


logger = setup_logger(__name__)

class KeywordRankChecker:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.results = []
    

    async def search_google_cse(self, keyword: str, max_results: int = 100) -> List[Dict]:
        """Search using Google Custom Search Engine API - most reliable method"""
        try:
            api_url = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                'key': settings.google_cloud_api_key_3,
                'cx': settings.google_cloud_cse,
                'q': keyword,
                'num': min(max_results, 10),
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
    
    async def check_keyword_rank(self, keyword: str, target_domain: str = None, max_results: int = 100) -> Dict:
        """Check the ranking position of a keyword for a specific domain"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                search_results = await self.search_google_cse(keyword, max_results)

                target_position = None
                if target_domain:
                    clean_target_domain = target_domain.lower().replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/')
                    
                    for result in search_results:
                        result_url = result['url'].lower()
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
    
    async def run(self, keywords: List[str], target_domain: str = None, max_results: int = 100) -> List[Dict]:
        """Check ranking positions for multiple keywords"""
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                for keyword in keywords:
                    logger.info(f"Checking keyword: {keyword}")
                    result = await self.check_keyword_rank(keyword, target_domain, max_results)
                    self.results.append(result)
                    
                    await asyncio.sleep(2)
                    
            finally:
                await browser.close()
        validated_results = [AnalyzeKeywordRankResult(**res) for res in self.results]

        return validated_results
    
    def save_results(self, results: List[Dict], filename: str = None) -> str:
        """Save results to JSON file"""
        if filename is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"keyword_rank_results_{filename}.json"
        
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
            
            print("-" * 40)