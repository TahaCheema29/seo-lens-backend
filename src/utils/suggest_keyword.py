import asyncio
import time
import json
import requests
from typing import List, Dict, Optional, Set
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from src.config.logger_config import setup_logger
from urllib.parse import quote_plus
import re
from src.config.settings import settings
from src.schemas.suggest_keywords import SuggestKeywordResult

logger = setup_logger(__name__)

class KeywordResearch:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.results = []
    
    async def search_google_cse(self, keyword: str, max_results: int = 10) -> List[Dict]:
        """Search using Google Custom Search Engine API - most reliable method"""
        try:
            # Google Custom Search API endpoint
            api_url = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                'key': settings.google_cloud_api_key_3,
                'cx': settings.google_cloud_cse,
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

                if "items" in data:
                    for idx, item in enumerate(data["items"], 1):
                        try:
                            results.append(
                                {
                                    "position": idx,
                                    "title": item.get("title", "No title"),
                                    "url": item.get("link", "No URL"),
                                    "snippet": item.get("snippet", "No snippet"),
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Error parsing CSE result {idx}: {e}")
                            continue

                logger.info(f"Google CSE API found {len(results)} results")
                return results
            else:
                logger.error(
                    f"Google CSE API request failed with status {response.status_code}: {response.text}"
                )
                return []

        except Exception as e:
            logger.error(f"Google CSE API search failed for '{keyword}': {e}")
            return []

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
            soup = BeautifulSoup(html, "html.parser")

            related_searches = []

            # Method 1: Find "Searches related to" section with various selectors
            related_selectors = [
                'div[aria-label="Searches related to"]',
                "div.brs_col",
                "div[data-ved]",
                "div.g[data-ved]",
            ]

            for selector in related_selectors:
                related_sections = soup.select(selector)
                for section in related_sections:
                    links = section.find_all("a")
                    for link in links:
                        related_text = link.get_text().strip()
                        if (
                            related_text
                            and related_text != keyword
                            and len(related_text) > 2
                            and len(related_text.split()) <= 5
                        ):  # Reasonable length
                            related_searches.append(related_text)

            # Method 2: Extract from search result titles and snippets
            if not related_searches:
                search_results = soup.find_all("div", class_="g")
                for result in search_results:
                    # Extract from titles
                    title_elem = result.find("h3")
                    if title_elem:
                        title_text = title_elem.get_text().strip()
                        words = title_text.split()
                        for word in words:
                            if (
                                len(word) > 3
                                and word.lower() not in keyword.lower()
                                and word.lower()
                                not in [
                                    "the",
                                    "and",
                                    "for",
                                    "with",
                                    "from",
                                    "this",
                                    "that",
                                ]
                            ):
                                related_searches.append(word)

                    # Extract from snippets
                    snippet_elem = result.find("span", class_="VuuXrf")
                    if snippet_elem:
                        snippet_text = snippet_elem.get_text().strip()
                        words = snippet_text.split()
                        for word in words:
                            if (
                                len(word) > 3
                                and word.lower() not in keyword.lower()
                                and word.lower()
                                not in [
                                    "the",
                                    "and",
                                    "for",
                                    "with",
                                    "from",
                                    "this",
                                    "that",
                                ]
                            ):
                                related_searches.append(word)

            # Method 3: Generate common related terms
            if not related_searches:
                common_related = [
                    "strategy",
                    "tips",
                    "tools",
                    "examples",
                    "benefits",
                    "guide",
                    "tutorial",
                    "best practices",
                    "techniques",
                    "methods",
                ]
                for term in common_related:
                    related_searches.append(f"{keyword} {term}")
                    related_searches.append(f"{term} {keyword}")

            # Clean and deduplicate
            cleaned_searches = []
            seen = set()
            for term in related_searches:
                term = term.strip().lower()
                if (
                    term
                    and term not in seen
                    and term != keyword.lower()
                    and len(term) > 2
                ):
                    cleaned_searches.append(term)
                    seen.add(term)

            logger.info(f"Found {len(cleaned_searches)} related searches")
            return cleaned_searches[:10]

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
            await page.wait_for_timeout(3000)  # Wait longer for dynamic content

            # Get page content
            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            paa_questions = []

            # Method 1: Look for People Also Ask section with various selectors
            paa_selectors = [
                'div[aria-label="People also ask"]',
                "div[data-initq]",
                "div.g[data-initq]",
                'div[jsname="Cpkphb"]',
            ]

            for selector in paa_selectors:
                paa_sections = soup.select(selector)
                for section in paa_sections:
                    questions = section.find_all(
                        ["div", "span"], string=re.compile(r"\?")
                    )
                    for question in questions:
                        question_text = question.get_text().strip()
                        if (
                            question_text
                            and "?" in question_text
                            and len(question_text) > 10
                        ):
                            paa_questions.append(
                                {"question": question_text, "keyword": keyword}
                            )

            # Method 2: Look for questions in search results
            if not paa_questions:
                question_divs = soup.find_all("div", class_="g")
                for div in question_divs:
                    # Look for question patterns in various elements
                    question_elements = div.find_all(
                        ["span", "div", "h3"], string=re.compile(r"\?")
                    )
                    for element in question_elements:
                        question_text = element.get_text().strip()
                        if (
                            question_text
                            and "?" in question_text
                            and len(question_text) > 10
                            and keyword.lower() in question_text.lower()
                        ):
                            paa_questions.append(
                                {"question": question_text, "keyword": keyword}
                            )

            # Method 3: Generate some common questions based on the keyword
            if not paa_questions:
                common_questions = [
                    f"What is {keyword}?",
                    f"How does {keyword} work?",
                    f"Why is {keyword} important?",
                    f"Best practices for {keyword}",
                    f"How to improve {keyword}?",
                ]
                for question in common_questions:
                    paa_questions.append({"question": question, "keyword": keyword})

            # Remove duplicates and limit
            unique_questions = []
            seen = set()
            for q in paa_questions:
                if q["question"] not in seen:
                    unique_questions.append(q)
                    seen.add(q["question"])

            logger.info(f"Found {len(unique_questions)} People Also Ask questions")
            return unique_questions[:10]

        except Exception as e:
            logger.error(f"Error getting People Also Ask for '{keyword}': {e}")
            return []

    async def get_autocomplete_suggestions(self, page, keyword: str) -> List[str]:
        """Get Google autocomplete suggestions for a keyword"""
        try:
            logger.info(f"Getting autocomplete suggestions for: {keyword}")

            # Method 1: Try to simulate typing in Google search box
            search_url = "https://www.google.com"
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)

            # Find the search box and type the keyword
            search_box = page.locator('input[name="q"]')
            if await search_box.count() > 0:
                await search_box.fill(keyword)
                await page.wait_for_timeout(1000)  # Wait for suggestions to appear

                # Look for autocomplete suggestions
                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                suggestions = []

                # Look for autocomplete suggestions in various containers
                autocomplete_selectors = [
                    'div[role="presentation"]',
                    'div[jsname="aajZCb"]',
                    'div[class*="aajZCb"]',
                    'div[class*="erkvQe"]',
                    'ul[role="listbox"] li',
                    "div[data-ved] span",
                ]

                for selector in autocomplete_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text().strip()
                        if (
                            text
                            and text != keyword
                            and keyword.lower() in text.lower()
                            and len(text) > len(keyword)
                            and len(text.split()) <= 5
                        ):
                            suggestions.append(text)

                if suggestions:
                    suggestions = list(set(suggestions))[:10]
                    logger.info(
                        f"Found {len(suggestions)} autocomplete suggestions via typing simulation"
                    )
                    return suggestions

            # Method 2: Extract from search results if typing simulation fails
            search_url = f"https://www.google.com/search?q={quote_plus(keyword)}"
            await page.goto(search_url, timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(2000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            suggestions = []

            # Extract from search result titles and snippets
            search_results = soup.find_all("div", class_="g")
            for result in search_results:
                # Extract from titles
                title_elem = result.find("h3")
                if title_elem:
                    title_text = title_elem.get_text().strip()
                    words = title_text.split()
                    for i, word in enumerate(words):
                        if keyword.lower() in word.lower():
                            # Get surrounding words to form suggestions
                            start = max(0, i - 1)
                            end = min(len(words), i + 2)
                            phrase = " ".join(words[start:end])
                            if len(phrase.split()) <= 4 and phrase != keyword:
                                suggestions.append(phrase)

                # Extract from snippets
                snippet_elem = result.find("span", class_="VuuXrf")
                if snippet_elem:
                    snippet_text = snippet_elem.get_text().strip()
                    words = snippet_text.split()
                    for i, word in enumerate(words):
                        if keyword.lower() in word.lower():
                            start = max(0, i - 1)
                            end = min(len(words), i + 2)
                            phrase = " ".join(words[start:end])
                            if len(phrase.split()) <= 4 and phrase != keyword:
                                suggestions.append(phrase)

            # Method 3: Generate common autocomplete suggestions
            if not suggestions:
                common_suggestions = [
                    f"{keyword} strategy",
                    f"{keyword} tips",
                    f"{keyword} examples",
                    f"{keyword} tools",
                    f"{keyword} guide",
                    f"{keyword} best practices",
                    f"{keyword} benefits",
                    f"{keyword} tutorial",
                    f"{keyword} ideas",
                    f"{keyword} 2024",
                    f"{keyword} 2025",
                ]
                suggestions = common_suggestions

            # Clean and deduplicate
            cleaned_suggestions = []
            seen = set()
            for suggestion in suggestions:
                suggestion = suggestion.strip().lower()
                if (
                    suggestion
                    and suggestion not in seen
                    and suggestion != keyword.lower()
                    and len(suggestion) > len(keyword)
                    and len(suggestion.split()) <= 5
                ):
                    cleaned_suggestions.append(suggestion)
                    seen.add(suggestion)

            logger.info(f"Found {len(cleaned_suggestions)} autocomplete suggestions")
            return cleaned_suggestions[:10]

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
            soup = BeautifulSoup(html, "html.parser")

            long_tail_keywords = []

            # Method 1: Extract from snippets with various selectors
            snippet_selectors = [
                "span.VuuXrf",
                "span.st",
                "div.VwiC3b",
                "span[data-ved]",
                "div[data-ved]",
            ]

            for selector in snippet_selectors:
                snippets = soup.select(selector)
                for snippet in snippets:
                    snippet_text = snippet.get_text().strip()
                    if snippet_text and keyword.lower() in snippet_text.lower():
                        # Extract potential long-tail variations
                        words = snippet_text.split()
                        for i, word in enumerate(words):
                            if keyword.lower() in word.lower():
                                # Get surrounding words to form long-tail phrases
                                start = max(0, i - 2)
                                end = min(len(words), i + 3)
                                phrase = " ".join(words[start:end])
                                if (
                                    len(phrase.split()) >= 3
                                ):  # Long-tail should be at least 3 words
                                    long_tail_keywords.append(phrase)

            # Method 2: Extract from titles
            titles = soup.find_all(["h3", "h2", "h1"])
            for title in titles:
                title_text = title.get_text().strip()
                if title_text and keyword.lower() in title_text.lower():
                    words = title_text.split()
                    for i, word in enumerate(words):
                        if keyword.lower() in word.lower():
                            start = max(0, i - 1)
                            end = min(len(words), i + 2)
                            phrase = " ".join(words[start:end])
                            if len(phrase.split()) >= 2:
                                long_tail_keywords.append(phrase)

            # Method 3: Generate common long-tail variations
            if not long_tail_keywords:
                common_modifiers = [
                    "how to",
                    "what is",
                    "best",
                    "guide",
                    "tutorial",
                    "tips",
                    "strategies",
                    "tools",
                    "examples",
                    "benefits",
                    "advantages",
                    "disadvantages",
                    "vs",
                    "comparison",
                    "review",
                    "2024",
                    "2025",
                    "free",
                    "paid",
                    "online",
                ]

                for modifier in common_modifiers:
                    long_tail_keywords.append(f"{modifier} {keyword}")
                    long_tail_keywords.append(f"{keyword} {modifier}")

            # Clean and deduplicate
            cleaned_keywords = []
            for phrase in long_tail_keywords:
                phrase = phrase.strip().lower()
                if (
                    len(phrase.split()) >= 2
                    and len(phrase) > len(keyword)
                    and phrase not in cleaned_keywords
                ):
                    cleaned_keywords.append(phrase)

            logger.info(f"Found {len(cleaned_keywords)} long-tail keywords")
            return cleaned_keywords[:10]

        except Exception as e:
            logger.error(f"Error getting long-tail keywords for '{keyword}': {e}")
            return []

    async def research_keyword(self, keyword: str) -> Dict:
        """Perform comprehensive keyword research with maximum parallelism"""
        
        # Create tasks for all operations
        tasks = [
            self.search_google_cse(keyword, 10),
            self._get_related_searches_with_browser(keyword),
            self._get_people_also_ask_with_browser(keyword),
            self._get_autocomplete_with_browser(keyword),
            self._get_long_tail_with_browser(keyword)
        ]
        
        # Execute all tasks in parallel
        search_results, web_related_searches, paa_questions, autocomplete_suggestions, long_tail_keywords = await asyncio.gather(*tasks)
        
        # Process results (same as before)
        related_searches = []
        if search_results:
            for result in search_results:
                title = result.get("title", "").lower()
                snippet = result.get("snippet", "").lower()
                words = (title + " " + snippet).split()
                for word in words:
                    if (len(word) > 3 and word not in keyword.lower() and 
                        word not in ["the", "and", "for", "with", "from", "this", "that", "are", "was", "were"]):
                        related_searches.append(word)
            related_searches = list(set(related_searches))[:10]

        # Combine results
        all_related_searches = list(set(related_searches + web_related_searches))[:10]

        result = {
            "primary_keyword": keyword,
            "search_results": search_results,
            "related_searches": all_related_searches,
            "people_also_ask": paa_questions[:10],
            "autocomplete_suggestions": autocomplete_suggestions[:10],
            "long_tail_keywords": long_tail_keywords[:10],
            "total_related_terms": len(all_related_searches) + len(paa_questions) + 
                                len(autocomplete_suggestions) + len(long_tail_keywords),
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        logger.info(f"Keyword research completed for '{keyword}' - Found {result['total_related_terms']} related terms")
        return result
    

    async def _get_related_searches_with_browser(self, keyword: str) -> List[str]:
        """Wrapper to create browser instance for related searches"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            try:
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                })
                return await self.get_related_searches(page, keyword)
            finally:
                await browser.close()

    async def _get_people_also_ask_with_browser(self, keyword: str) -> List[Dict]:
        """Wrapper to create browser instance for people also ask"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            try:
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                })
                return await self.get_people_also_ask(page, keyword)
            finally:
                await browser.close()

    async def _get_autocomplete_with_browser(self, keyword: str) -> List[str]:
        """Wrapper to create browser instance for autocomplete"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            try:
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                })
                return await self.get_autocomplete_suggestions(page, keyword)
            finally:
                await browser.close()

    async def _get_long_tail_with_browser(self, keyword: str) -> List[str]:
        """Wrapper to create browser instance for long tail keywords"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            try:
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                })
                return await self.get_long_tail_keywords(page, keyword)
            finally:
                await browser.close()

    async def run(self, keywords: List[str]) -> List[Dict]:
        """Perform keyword research for multiple keywords"""

        start_time = time.time()

        for keyword in keywords:
            logger.info(f"Researching keyword: {keyword}")
            result = await self.research_keyword(keyword)
            self.results.append(result)

            await asyncio.sleep(3)

        validated_results = [SuggestKeywordResult(**res) for res in self.results]

        total_time = time.time() - start_time
        total_minutes = total_time / 60

        logger.info(f"Total time seconds {total_time}")
        logger.info(f"Total time minutes {total_minutes}")

        return validated_results

    def save_results(self, results: List[Dict], filename: str = None) -> str:
        """Save results to JSON file"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"keyword_research_results_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to: {filename}")
        return filename

    def print_summary(self, results: List[Dict]):
        """Print a summary of keyword research results"""
        print("\n" + "=" * 60)
        print("KEYWORD RESEARCH SUMMARY")
        print("=" * 60)

        for result in results:
            keyword = result["primary_keyword"]
            related = result["related_searches"]
            paa = result["people_also_ask"]
            autocomplete = result["autocomplete_suggestions"]
            long_tail = result["long_tail_keywords"]
            search_results = result.get("search_results", [])

            print(f"\nPrimary Keyword: {keyword}")
            print(f"Total Related Terms Found: {result['total_related_terms']}")
            print(f"Search Results Found: {len(search_results)}")

            if search_results:
                print(f"\nTop Search Results ({len(search_results)}):")
                for i, res in enumerate(search_results[:3], 1):
                    print(f"  {i}. {res['title']} - {res['url']}")
                if len(search_results) > 3:
                    print(f"  ... and {len(search_results) - 3} more")

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