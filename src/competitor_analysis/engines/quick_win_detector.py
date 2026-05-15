"""
Quick Win Detector for Competitor Analysis
Identifies easy fixes with high impact
"""

from typing import Dict, Any, List
from src.config.logger_config import setup_logger


class QuickWinDetector:
    """Detector for identifying quick wins - easy fixes with high impact"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def detect_quick_wins(
        self,
        user_data: Dict[str, Any],
        comparison: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Detect quick wins - easy fixes that provide high impact
        Returns list of actionable quick wins
        """
        quick_wins = []
        
        # Check for missing meta descriptions
        meta_win = self._check_meta_descriptions(user_data, comparison)
        if meta_win:
            quick_wins.append(meta_win)
        
        # Check for missing title optimization
        title_win = self._check_title_optimization(user_data, comparison)
        if title_win:
            quick_wins.append(title_win)
        
        # Check for image optimization
        image_win = self._check_image_optimization(user_data)
        if image_win:
            quick_wins.append(image_win)
        
        # Check for HTTPS
        https_win = self._check_https(user_data, comparison)
        if https_win:
            quick_wins.append(https_win)
        
        # Check for robots.txt
        robots_win = self._check_robots_txt(user_data)
        if robots_win:
            quick_wins.append(robots_win)
        
        # Check for Open Graph tags
        og_win = self._check_open_graph(user_data)
        if og_win:
            quick_wins.append(og_win)
        
        # Sort by impact (high to low), then by effort (easy to hard)
        quick_wins.sort(key=lambda x: (
            0 if x["impact"] == "high" else 1 if x["impact"] == "medium" else 2,
            0 if x["effort_level"] == "easy" else 1 if x["effort_level"] == "medium" else 2
        ))
        
        return quick_wins[:5]  # Return top 5 quick wins
    
    def _check_meta_descriptions(
        self, 
        user_data: Dict[str, Any], 
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for missing meta descriptions"""
        url_results = user_data.get("url_results", [])
        if not url_results:
            return None
        
        # Check first page (homepage)
        homepage = url_results[0] if url_results else {}
        meta_check = homepage.get("meta_description_length_check", {})
        
        if meta_check.get("status") != "PASS":
            return {
                "issue": "Add a meta description to your homepage",
                "why_it_matters": "This is the text people see in Google search results. A good description can increase clicks by 20-30%.",
                "effort": "5 minutes",
                "effort_level": "easy",
                "impact": "high",
                "how_to_fix": "Add this HTML to your homepage <head> section: <meta name='description' content='Your compelling description here'>",
                "expected_result": "More people will click on your site when they see it in Google results"
            }
        return None
    
    def _check_title_optimization(
        self, 
        user_data: Dict[str, Any], 
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for title optimization issues"""
        url_results = user_data.get("url_results", [])
        if not url_results:
            return None
        
        homepage = url_results[0] if url_results else {}
        title_check = homepage.get("title_length_check", {})
        title = homepage.get("title", "")
        
        if title_check.get("status") != "PASS" or len(title) < 30 or len(title) > 60:
            issue = "too short" if len(title) < 30 else "too long" if len(title) > 60 else "needs optimization"
            
            return {
                "issue": f"Optimize your homepage title - it's {issue}",
                "why_it_matters": "Page titles appear as the clickable headline in Google. Poor titles hurt your click-through rates.",
                "effort": "2 minutes",
                "effort_level": "easy",
                "impact": "high",
                "how_to_fix": f"Update your <title> tag to be 30-60 characters. Current: '{title}' ({len(title)} chars)",
                "expected_result": "Better visibility and more clicks from Google search results"
            }
        return None
    
    def _check_image_optimization(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for unoptimized images"""
        url_results = user_data.get("url_results", [])
        if not url_results:
            return None
        
        # Check for large HTML size indicating unoptimized images
        sizes = [r.get("html_size_bytes", 0) for r in url_results if r.get("html_size_bytes")]
        if sizes and max(sizes) > 1000000:  # > 1MB
            return {
                "issue": "Compress your images",
                "why_it_matters": "Large images are the #1 cause of slow websites. They dramatically increase page load time.",
                "effort": "15 minutes",
                "effort_level": "easy",
                "impact": "high",
                "how_to_fix": "Use free tools like TinyPNG.com or Squoosh.app to compress images before uploading. Aim for under 200KB per image.",
                "expected_result": "Your pages will load 30-50% faster"
            }
        return None
    
    def _check_https(
        self, 
        user_data: Dict[str, Any], 
        comparison: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for missing HTTPS"""
        base_checks = user_data.get("base_url_checks", {})
        https_check = base_checks.get("https_ssl_check", {})
        
        if https_check.get("status") != "PASS":
            return {
                "issue": "Enable HTTPS security on your website",
                "why_it_matters": "Without HTTPS, visitors see 'Not Secure' warnings. Google ranks secure sites higher.",
                "effort": "30 minutes",
                "effort_level": "medium",
                "impact": "high",
                "how_to_fix": "Contact your hosting provider and ask them to install a free SSL certificate (Let's Encrypt). Most hosts do this for free.",
                "expected_result": "Remove security warnings and improve Google rankings"
            }
        return None
    
    def _check_robots_txt(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for missing robots.txt"""
        base_checks = user_data.get("base_url_checks", {})
        robots_check = base_checks.get("robots_txt_check", {})
        
        if robots_check.get("status") != "PASS":
            return {
                "issue": "Add a robots.txt file",
                "why_it_matters": "This file tells Google which pages to crawl. Without it, Google may miss important pages.",
                "effort": "10 minutes",
                "effort_level": "easy",
                "impact": "medium",
                "how_to_fix": "Create a file named 'robots.txt' in your website root folder with: User-agent: *\nAllow: /",
                "expected_result": "Google can properly crawl and index your website"
            }
        return None
    
    def _check_open_graph(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for missing Open Graph tags"""
        url_results = user_data.get("url_results", [])
        if not url_results:
            return None
        
        homepage = url_results[0] if url_results else {}
        og_check = homepage.get("open_graph_check", {})
        
        if og_check.get("status") != "PASS":
            return {
                "issue": "Add social media preview tags",
                "why_it_matters": "When people share your site on Facebook/Twitter, these tags control how it looks. Without them, shares look unprofessional.",
                "effort": "20 minutes",
                "effort_level": "easy",
                "impact": "medium",
                "how_to_fix": "Add Open Graph meta tags to your homepage: <meta property='og:title' content='Your Title'> and <meta property='og:image' content='your-image-url.jpg'>",
                "expected_result": "Your site looks professional when shared on social media"
            }
        return None
