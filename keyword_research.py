import asyncio
import time
import json
from typing import List, Dict, Optional, Set
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from logger_config import setup_logger
from urllib.parse import quote_plus
import re

logger = setup_logger(__name__)

class KeywordResearch:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.results = []
    
    async def get_related_searches(self, page, keyword: str) -> List[str]:
        """Get related search terms from Google's 'Searches related to' section"""
        try:
            # Construct Google search URL
            search_url = f"https://www.google.com/search?q={quote_plus(keyword)}"
            
            logger.info(f"Getting related searches for: {keyword}")
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Get page content
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            related_searches = []
            
            # Find "Searches related to" section
            related_section = soup.find('div', {'aria-label': 'Searches related to'})
            if related_section:
                related_links = related_section.find_all('a')
                for link in related_links:
                    related_text = link.get_text().strip()
                    if related_text and related_text != keyword:
                        related_searches.append(related_text)
            
            # Alternative method - look for related searches in different containers
            if not related_searches:
                related_divs = soup.find_all('div', class_='brs_col')
                for div in related_divs:
                    links = div.find_all('a')
                    for link in links:
                        related_text = link.get_text().strip()
                        if related_text and related_text != keyword:
                            related_searches.append(related_text)
            
            return list(set(related_searches))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error getting related searches for '{keyword}': {e}")
            return []
    
    async def get_people_also_ask(self, page, keyword: str) -> List[Dict]:
        """Get 'People also ask' questions from Google search results"""
        try:
            # Construct Google search URL
            search_url = f"https://www.google.com/search?q={quote_plus(keyword)}"
            
            logger.info(f"Getting People Also Ask for: {keyword}")
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)
            
            # Get page content
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            paa_questions = []
            
            # Find People Also Ask section
            paa_section = soup.find('div', {'aria-label': 'People also ask'})
            if paa_section:
                questions = paa_section.find_all('div', class_='related-question-pair')
                for question_div in questions:
                    question_element = question_div.find('div', class_='match-mod-horizontal-padding')
                    if question_element:
                        question_text = question_element.get_text().strip()
                        if question_text:
                            paa_questions.append({
                                'question': question_text,
                                'keyword': keyword
                            })
            
            # Alternative method - look for questions in different containers
            if not paa_questions:
                question_divs = soup.find_all('div', class_='g')
                for div in question_divs:
                    # Look for question patterns
                    question_elements = div.find_all('span', string=re.compile(r'\?'))
                    for element in question_elements:
                        question_text = element.get_text().strip()
                        if question_text and '?' in question_text:
                            paa_questions.append({
                                'question': question_text,
                                'keyword': keyword
                            })
            
            return paa_questions
            
        except Exception as e:
            logger.error(f"Error getting People Also Ask for '{keyword}': {e}")
            return []
    
    async def get_autocomplete_suggestions(self, page, keyword: str) -> List[str]:
        """Get Google autocomplete suggestions for a keyword"""
        try:
            # Use Google's autocomplete API endpoint
            autocomplete_url = f"https://www.google.com/complete/search?client=chrome&q={quote_plus(keyword)}"
            
            logger.info(f"Getting autocomplete suggestions for: {keyword}")
            await page.goto(autocomplete_url, timeout=30000)
            
            # Get the response content
            content = await page.content()
            
            # Parse JSON response
            suggestions = []
            try:
                # The response is usually wrapped in some HTML, extract JSON
                json_match = re.search(r'\[(.*?)\]', content, re.DOTALL)
                if json_match:
                    json_str = '[' + json_match.group(1) + ']'
                    data = json.loads(json_str)
                    if len(data) > 1:
                        suggestions = data[1]  # Second element contains the suggestions
            except (json.JSONDecodeError, IndexError):
                logger.warning(f"Could not parse autocomplete response for '{keyword}'")
            
            return suggestions[:10]  # Limit to 10 suggestions
            
        except Exception as e:
            logger.error(f"Error getting autocomplete suggestions for '{keyword}': {e}")
            return []
    
    async def get_long_tail_keywords(self, page, keyword: str) -> List[str]:
        """Get long-tail keyword variations"""
        try:
            # Search for the keyword and look for long-tail variations in snippets
            search_url = f"https://www.google.com/search?q={quote_plus(keyword)}"
            
            logger.info(f"Getting long-tail keywords for: {keyword}")
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)
            
            html = await page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            long_tail_keywords = []
            
            # Extract text from snippets that might contain long-tail variations
            snippets = soup.find_all('span', class_='VuuXrf')
            for snippet in snippets:
                snippet_text = snippet.get_text().lower()
                # Look for phrases that contain the original keyword
                if keyword.lower() in snippet_text:
                    # Extract potential long-tail variations
                    words = snippet_text.split()
                    for i, word in enumerate(words):
                        if keyword.lower() in word:
                            # Get surrounding words to form long-tail phrases
                            start = max(0, i - 2)
                            end = min(len(words), i + 3)
                            phrase = ' '.join(words[start:end])
                            if len(phrase.split()) >= 3:  # Long-tail should be at least 3 words
                                long_tail_keywords.append(phrase)
            
            return list(set(long_tail_keywords))[:10]  # Remove duplicates and limit to 10
            
        except Exception as e:
            logger.error(f"Error getting long-tail keywords for '{keyword}': {e}")
            return []
    
    async def research_keyword(self, keyword: str) -> Dict:
        """Perform comprehensive keyword research for a single keyword"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
            try:
                # Set user agent to avoid detection
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                })
                
                # Get all types of related keywords
                related_searches = await self.get_related_searches(page, keyword)
                paa_questions = await self.get_people_also_ask(page, keyword)
                autocomplete_suggestions = await self.get_autocomplete_suggestions(page, keyword)
                long_tail_keywords = await self.get_long_tail_keywords(page, keyword)
                
                result = {
                    'primary_keyword': keyword,
                    'related_searches': related_searches[:10],  # Limit to 10
                    'people_also_ask': paa_questions[:10],  # Limit to 10
                    'autocomplete_suggestions': autocomplete_suggestions[:10],  # Limit to 10
                    'long_tail_keywords': long_tail_keywords[:10],  # Limit to 10
                    'total_related_terms': len(related_searches) + len(paa_questions) + len(autocomplete_suggestions) + len(long_tail_keywords),
                    'timestamp': time.time(),
                    'date': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                logger.info(f"Keyword research completed for '{keyword}' - Found {result['total_related_terms']} related terms")
                return result
                
            finally:
                await browser.close()
    
    async def research_multiple_keywords(self, keywords: List[str]) -> List[Dict]:
        """Perform keyword research for multiple keywords"""
        results = []
        
        for keyword in keywords:
            logger.info(f"Researching keyword: {keyword}")
            result = await self.research_keyword(keyword)
            results.append(result)
            
            # Add delay between searches to avoid rate limiting
            await asyncio.sleep(3)
        
        return results
    
    def save_results(self, results: List[Dict], filename: str = None) -> str:
        """Save results to JSON file"""
        if filename is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"keyword_research_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {filename}")
        return filename
    
    def print_summary(self, results: List[Dict]):
        """Print a summary of keyword research results"""
        print("\n" + "="*60)
        print("KEYWORD RESEARCH SUMMARY")
        print("="*60)
        
        for result in results:
            keyword = result['primary_keyword']
            related = result['related_searches']
            paa = result['people_also_ask']
            autocomplete = result['autocomplete_suggestions']
            long_tail = result['long_tail_keywords']
            
            print(f"\nPrimary Keyword: {keyword}")
            print(f"Total Related Terms Found: {result['total_related_terms']}")
            
            if related:
                print(f"\nRelated Searches ({len(related)}):")
                for i, term in enumerate(related[:5], 1):
                    print(f"  {i}. {term}")
                if len(related) > 5:
                    print(f"  ... and {len(related) - 5} more")
            
            if paa:
                print(f"\nPeople Also Ask ({len(paa)}):")
                for i, qa in enumerate(paa[:3], 1):
                    print(f"  {i}. {qa['question']}")
                if len(paa) > 3:
                    print(f"  ... and {len(paa) - 3} more")
            
            if autocomplete:
                print(f"\nAutocomplete Suggestions ({len(autocomplete)}):")
                for i, term in enumerate(autocomplete[:5], 1):
                    print(f"  {i}. {term}")
                if len(autocomplete) > 5:
                    print(f"  ... and {len(autocomplete) - 5} more")
            
            if long_tail:
                print(f"\nLong-tail Keywords ({len(long_tail)}):")
                for i, term in enumerate(long_tail[:3], 1):
                    print(f"  {i}. {term}")
                if len(long_tail) > 3:
                    print(f"  ... and {len(long_tail) - 3} more")
            
            print("-" * 40)


async def main():
    """Example usage of the KeywordResearch"""
    researcher = KeywordResearch(headless=True)
    
    # Example keywords to research
    keywords = [
        "python web scraping",
        "SEO tools",
        "content marketing"
    ]
    
    print("Starting keyword research...")
    
    # Research multiple keywords
    results = await researcher.research_multiple_keywords(keywords)
    
    # Print summary
    researcher.print_summary(results)
    
    # Save results
    filename = researcher.save_results(results)
    print(f"\nDetailed results saved to: {filename}")


if __name__ == "__main__":
    asyncio.run(main())
