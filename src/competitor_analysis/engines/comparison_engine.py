"""
Enhanced Comparison Engine for Competitor Analysis
Calculates comprehensive scores and compares metrics between user and competitor websites
Uses simple pass/fail scoring for consistency with SEO Analyzer
"""

from typing import Dict, Any, Optional, List
from statistics import mean, median
from src.config.logger_config import setup_logger


class ComparisonEngine:
    """Engine for comparing SEO metrics between two websites"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def calculate_overall_score(self, seo_data: Dict[str, Any]) -> int:
        """Calculate overall SEO score (0-100) from SEO analysis data"""
        return self._calculate_simple_score(seo_data)
    
    def _calculate_simple_score(self, seo_data: Dict[str, Any]) -> int:
        """Calculate simple pass/fail score"""
        base_url_checks = seo_data.get("base_url_checks", {})
        url_results = seo_data.get("url_results", [])
        
        total_checks = 0
        passed_checks = 0
        warning_checks = 0
        
        # Count base URL checks
        base_checks = [
            base_url_checks.get("www_redirect_check"),
            base_url_checks.get("robots_txt_check"),
            base_url_checks.get("https_ssl_check"),
            base_url_checks.get("directory_listing_check"),
            base_url_checks.get("expires_headers_check"),
            base_url_checks.get("caching_advice"),
        ]
        
        for check in base_checks:
            if check:
                status = check.get("status", "")
                total_checks += 1
                if status == "PASS":
                    passed_checks += 1
                elif status == "WARNING":
                    warning_checks += 1
        
        # Count URL result checks
        for result in url_results:
            if not isinstance(result, dict):
                continue
            checks = [
                result.get("title_length_check"),
                result.get("title_keyword_presence"),
                result.get("meta_description_length_check"),
                result.get("meta_description_keyword_presence"),
                result.get("h1_check"),
                result.get("image_alt_check"),
                result.get("canonical_check"),
                result.get("noindex_check"),
                result.get("open_graph_check"),
                result.get("schema_validation"),
                result.get("html_size_check"),
                result.get("response_time_check"),
                result.get("js_minification_check"),
                result.get("css_minification_check"),
                result.get("mobile_responsiveness"),
            ]
            
            for check in checks:
                if check:
                    status = check.get("status", "")
                    total_checks += 1
                    if status == "PASS":
                        passed_checks += 1
                    elif status == "WARNING":
                        warning_checks += 1
        
        # Calculate score: PASS = 100%, WARNING = 50%, FAIL = 0%
        if total_checks > 0:
            score = round(((passed_checks * 100 + warning_checks * 50) / total_checks))
        else:
            score = 0
        
        return score
    
    def compare_metrics(
        self, 
        user_data: Dict[str, Any], 
        competitor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare all metrics between user and competitor"""
        return {
            "performance": self._compare_performance(user_data, competitor_data),
            "seo": self._compare_seo(user_data, competitor_data),
            "technical": self._compare_technical(user_data, competitor_data),
            "content": self._compare_content(user_data, competitor_data),
            "links": self._compare_links(user_data, competitor_data),
            "social": self._compare_social(user_data, competitor_data),
        }
    
    def _compare_performance(
        self, 
        user_data: Dict[str, Any], 
        competitor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare performance metrics with detailed analysis"""
        user_results = user_data.get("url_results", [])
        comp_results = competitor_data.get("url_results", [])
        
        # Response times
        user_response_times = [r.get("response_time_ms", 0) for r in user_results if r.get("response_time_ms")]
        comp_response_times = [r.get("response_time_ms", 0) for r in comp_results if r.get("response_time_ms")]
        
        user_avg_response = mean(user_response_times) if user_response_times else 0
        comp_avg_response = mean(comp_response_times) if comp_response_times else 0
        user_median_response = median(user_response_times) if user_response_times else 0
        comp_median_response = median(comp_response_times) if comp_response_times else 0
        
        # Page sizes
        user_sizes = [r.get("html_size_bytes", 0) for r in user_results if r.get("html_size_bytes")]
        comp_sizes = [r.get("html_size_bytes", 0) for r in comp_results if r.get("html_size_bytes")]
        
        user_avg_size = mean(user_sizes) if user_sizes else 0
        comp_avg_size = mean(comp_sizes) if comp_sizes else 0
        
        # Total requests
        user_requests = [r.get("total_requests", 0) for r in user_results if r.get("total_requests")]
        comp_requests = [r.get("total_requests", 0) for r in comp_results if r.get("total_requests")]
        
        user_avg_requests = mean(user_requests) if user_requests else 0
        comp_avg_requests = mean(comp_requests) if comp_requests else 0
        
        return {
            "category_score": {
                "user": int(self._calculate_simple_score(user_data)),
                "competitor": int(self._calculate_simple_score(competitor_data))
            },
            "load_time": {
                "user_value": f"{user_avg_response/1000:.1f}s",
                "competitor_value": f"{comp_avg_response/1000:.1f}s",
                "winner": "user" if user_avg_response < comp_avg_response else "competitor" if comp_avg_response < user_avg_response else "tie",
                "gap": f"{abs(user_avg_response - comp_avg_response)/1000:.1f}s"
            },
            "page_size": {
                "user_value": f"{user_avg_size/1024:.0f}KB",
                "competitor_value": f"{comp_avg_size/1024:.0f}KB",
                "winner": "user" if user_avg_size < comp_avg_size else "competitor" if comp_avg_size < user_avg_size else "tie",
            },
            "requests_count": {
                "user_value": f"{user_avg_requests:.0f}",
                "competitor_value": f"{comp_avg_requests:.0f}",
                "winner": "user" if user_avg_requests < comp_avg_requests else "competitor" if comp_avg_requests < user_avg_requests else "tie",
            },
            "server_response_time": {
                "user_value": f"{user_median_response/1000:.2f}s",
                "competitor_value": f"{comp_median_response/1000:.2f}s",
                "winner": "user" if user_median_response < comp_median_response else "competitor" if comp_median_response < user_median_response else "tie",
            }
        }
    
    def _compare_seo(
        self, 
        user_data: Dict[str, Any], 
        competitor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare SEO metrics with detailed analysis"""
        user_results = user_data.get("url_results", [])
        comp_results = competitor_data.get("url_results", [])
        
        total_user = len(user_results)
        total_comp = len(comp_results)
        
        # Meta description coverage
        user_meta_pass = sum(1 for r in user_results if r.get("meta_description_length_check", {}).get("status") == "PASS")
        comp_meta_pass = sum(1 for r in comp_results if r.get("meta_description_length_check", {}).get("status") == "PASS")
        
        user_meta_coverage = (user_meta_pass / total_user * 100) if total_user > 0 else 0
        comp_meta_coverage = (comp_meta_pass / total_comp * 100) if total_comp > 0 else 0
        
        # Title optimization
        user_title_pass = sum(1 for r in user_results if r.get("title_length_check", {}).get("status") == "PASS")
        comp_title_pass = sum(1 for r in comp_results if r.get("title_length_check", {}).get("status") == "PASS")
        
        user_title_coverage = (user_title_pass / total_user * 100) if total_user > 0 else 0
        comp_title_coverage = (comp_title_pass / total_comp * 100) if total_comp > 0 else 0
        
        # H1 structure
        user_h1_pass = sum(1 for r in user_results if r.get("h1_check", {}).get("status") == "PASS")
        comp_h1_pass = sum(1 for r in comp_results if r.get("h1_check", {}).get("status") == "PASS")
        
        user_h1_coverage = (user_h1_pass / total_user * 100) if total_user > 0 else 0
        comp_h1_coverage = (comp_h1_pass / total_comp * 100) if total_comp > 0 else 0
        
        # Image alt tags
        user_alt_pass = sum(1 for r in user_results if r.get("image_alt_check", {}).get("status") == "PASS")
        comp_alt_pass = sum(1 for r in comp_results if r.get("image_alt_check", {}).get("status") == "PASS")
        
        user_alt_coverage = (user_alt_pass / total_user * 100) if total_user > 0 else 0
        comp_alt_coverage = (comp_alt_pass / total_comp * 100) if total_comp > 0 else 0
        
        # Canonical tags
        user_canonical_pass = sum(1 for r in user_results if r.get("canonical_check", {}).get("status") == "PASS")
        comp_canonical_pass = sum(1 for r in comp_results if r.get("canonical_check", {}).get("status") == "PASS")
        
        user_canonical_coverage = (user_canonical_pass / total_user * 100) if total_user > 0 else 0
        comp_canonical_coverage = (comp_canonical_pass / total_comp * 100) if total_comp > 0 else 0
        
        # Schema markup
        user_schema_pass = sum(1 for r in user_results if r.get("schema_validation", {}).get("status") == "PASS")
        comp_schema_pass = sum(1 for r in comp_results if r.get("schema_validation", {}).get("status") == "PASS")
        
        user_schema_coverage = (user_schema_pass / total_user * 100) if total_user > 0 else 0
        comp_schema_coverage = (comp_schema_pass / total_comp * 100) if total_comp > 0 else 0
        
        # Open Graph
        user_og_pass = sum(1 for r in user_results if r.get("open_graph_check", {}).get("status") == "PASS")
        comp_og_pass = sum(1 for r in comp_results if r.get("open_graph_check", {}).get("status") == "PASS")
        
        user_og_coverage = (user_og_pass / total_user * 100) if total_user > 0 else 0
        comp_og_coverage = (comp_og_pass / total_comp * 100) if total_comp > 0 else 0
        
        # Internal and external links
        user_internal = sum(r.get("internal_links_count", 0) for r in user_results) / total_user if total_user > 0 else 0
        comp_internal = sum(r.get("internal_links_count", 0) for r in comp_results) / total_comp if total_comp > 0 else 0
        
        user_external = sum(r.get("external_links_count", 0) for r in user_results) / total_user if total_user > 0 else 0
        comp_external = sum(r.get("external_links_count", 0) for r in comp_results) / total_comp if total_comp > 0 else 0
        
        return {
            "category_score": {
                "user": int(self._calculate_simple_score(user_data)),
                "competitor": int(self._calculate_simple_score(competitor_data))
            },
            "title_optimization": {
                "user_value": f"{user_title_coverage:.0f}%",
                "competitor_value": f"{comp_title_coverage:.0f}%",
                "winner": "user" if user_title_coverage > comp_title_coverage else "competitor" if comp_title_coverage > user_title_coverage else "tie",
            },
            "meta_description_coverage": {
                "user_value": f"{user_meta_coverage:.0f}%",
                "competitor_value": f"{comp_meta_coverage:.0f}%",
                "winner": "user" if user_meta_coverage > comp_meta_coverage else "competitor" if comp_meta_coverage > user_meta_coverage else "tie",
            },
            "heading_structure": {
                "user_value": f"{user_h1_coverage:.0f}%",
                "competitor_value": f"{comp_h1_coverage:.0f}%",
                "winner": "user" if user_h1_coverage > comp_h1_coverage else "competitor" if comp_h1_coverage > user_h1_coverage else "tie",
            },
            "image_alt_coverage": {
                "user_value": f"{user_alt_coverage:.0f}%",
                "competitor_value": f"{comp_alt_coverage:.0f}%",
                "winner": "user" if user_alt_coverage > comp_alt_coverage else "competitor" if comp_alt_coverage > user_alt_coverage else "tie",
            },
            "canonical_tags": {
                "user_value": f"{user_canonical_coverage:.0f}%",
                "competitor_value": f"{comp_canonical_coverage:.0f}%",
                "winner": "user" if user_canonical_coverage > comp_canonical_coverage else "competitor" if comp_canonical_coverage > user_canonical_coverage else "tie",
            },
            "schema_markup": {
                "user_value": f"{user_schema_coverage:.0f}%",
                "competitor_value": f"{comp_schema_coverage:.0f}%",
                "winner": "user" if user_schema_coverage > comp_schema_coverage else "competitor" if comp_schema_coverage > user_schema_coverage else "tie",
            },
            "open_graph_tags": {
                "user_value": f"{user_og_coverage:.0f}%",
                "competitor_value": f"{comp_og_coverage:.0f}%",
                "winner": "user" if user_og_coverage > comp_og_coverage else "competitor" if comp_og_coverage > user_og_coverage else "tie",
            },
            "internal_links": {
                "user_value": f"{user_internal:.0f}",
                "competitor_value": f"{comp_internal:.0f}",
                "winner": "user" if user_internal > comp_internal else "competitor" if comp_internal > user_internal else "tie",
            },
            "external_links": {
                "user_value": f"{user_external:.0f}",
                "competitor_value": f"{comp_external:.0f}",
                "winner": "user" if user_external > comp_external else "competitor" if comp_external > user_external else "tie",
            },
        }
    
    def _compare_technical(
        self, 
        user_data: Dict[str, Any], 
        competitor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare technical metrics with detailed analysis"""
        user_base = user_data.get("base_url_checks", {})
        comp_base = competitor_data.get("base_url_checks", {})
        
        user_results = user_data.get("url_results", [])
        comp_results = competitor_data.get("url_results", [])
        
        total_user = len(user_results)
        total_comp = len(comp_results)
        
        # HTTPS
        user_https = user_base.get("https_ssl_check", {}).get("status") == "PASS"
        comp_https = comp_base.get("https_ssl_check", {}).get("status") == "PASS"
        
        # Mobile friendly
        user_mobile = sum(1 for r in user_results if r.get("mobile_responsiveness", {}).get("status") == "PASS")
        comp_mobile = sum(1 for r in comp_results if r.get("mobile_responsiveness", {}).get("status") == "PASS")
        
        user_mobile_pct = (user_mobile / total_user * 100) if total_user > 0 else 0
        comp_mobile_pct = (comp_mobile / total_comp * 100) if total_comp > 0 else 0
        
        # Robots.txt
        user_robots = user_base.get("robots_txt_check", {}).get("status") == "PASS"
        comp_robots = comp_base.get("robots_txt_check", {}).get("status") == "PASS"
        
        # WWW redirect
        user_www = user_base.get("www_redirect_check", {}).get("status") == "PASS"
        comp_www = comp_base.get("www_redirect_check", {}).get("status") == "PASS"
        
        # Directory listing
        user_dir = user_base.get("directory_listing_check", {}).get("status") == "PASS"
        comp_dir = comp_base.get("directory_listing_check", {}).get("status") == "PASS"
        
        return {
            "category_score": {
                "user": int(self._calculate_simple_score(user_data)),
                "competitor": int(self._calculate_simple_score(competitor_data))
            },
            "https_security": {
                "user_value": "Enabled" if user_https else "Not Enabled",
                "competitor_value": "Enabled" if comp_https else "Not Enabled",
                "winner": "tie" if user_https == comp_https else ("user" if user_https else "competitor"),
            },
            "mobile_friendly": {
                "user_value": f"{user_mobile_pct:.0f}%",
                "competitor_value": f"{comp_mobile_pct:.0f}%",
                "winner": "user" if user_mobile_pct > comp_mobile_pct else "competitor" if comp_mobile_pct > user_mobile_pct else "tie",
            },
            "robots_txt": {
                "user_value": "Present" if user_robots else "Missing",
                "competitor_value": "Present" if comp_robots else "Missing",
                "winner": "tie" if user_robots == comp_robots else ("user" if user_robots else "competitor"),
            },
            "www_redirect": {
                "user_value": "Proper" if user_www else "Issues",
                "competitor_value": "Proper" if comp_www else "Issues",
                "winner": "tie" if user_www == comp_www else ("user" if user_www else "competitor"),
            },
            "directory_listing": {
                "user_value": "Disabled" if user_dir else "Enabled",
                "competitor_value": "Disabled" if comp_dir else "Enabled",
                "winner": "tie" if user_dir == comp_dir else ("user" if user_dir else "competitor"),
            },
        }
    
    def _compare_content(
        self, 
        user_data: Dict[str, Any], 
        competitor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare content metrics"""
        user_results = user_data.get("url_results", [])
        comp_results = competitor_data.get("url_results", [])
        
        total_user = len(user_results)
        total_comp = len(comp_results)
        
        # Calculate average word count from HTML size as proxy
        user_avg_size = mean([r.get("html_size_bytes", 0) for r in user_results]) if user_results else 0
        comp_avg_size = mean([r.get("html_size_bytes", 0) for r in comp_results]) if comp_results else 0
        
        # Images per page
        user_images = [r.get("image_requests", 0) for r in user_results if r.get("image_requests")]
        comp_images = [r.get("image_requests", 0) for r in comp_results if r.get("image_requests")]
        
        user_avg_images = mean(user_images) if user_images else 0
        comp_avg_images = mean(comp_images) if comp_images else 0
        
        return {
            "category_score": {
                "user": int(self._calculate_simple_score(user_data)),
                "competitor": int(self._calculate_simple_score(competitor_data))
            },
            "avg_word_count": {
                "user_value": f"{user_avg_size/100:.0f}",
                "competitor_value": f"{comp_avg_size/100:.0f}",
                "winner": "user" if user_avg_size > comp_avg_size else "competitor" if comp_avg_size > user_avg_size else "tie",
            },
            "images_per_page": {
                "user_value": f"{user_avg_images:.0f}",
                "competitor_value": f"{comp_avg_images:.0f}",
                "winner": "user" if user_avg_images > comp_avg_images else "competitor" if comp_avg_images > user_avg_images else "tie",
            },
        }
    
    def _compare_links(
        self, 
        user_data: Dict[str, Any], 
        competitor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare link metrics"""
        user_results = user_data.get("url_results", [])
        comp_results = competitor_data.get("url_results", [])
        
        # Total internal links
        user_internal_total = sum(r.get("internal_links_count", 0) for r in user_results)
        comp_internal_total = sum(r.get("internal_links_count", 0) for r in comp_results)
        
        # Total external links
        user_external_total = sum(r.get("external_links_count", 0) for r in user_results)
        comp_external_total = sum(r.get("external_links_count", 0) for r in comp_results)
        
        # Average per page
        total_user = len(user_results)
        total_comp = len(comp_results)
        
        user_avg_internal = user_internal_total / total_user if total_user > 0 else 0
        comp_avg_internal = comp_internal_total / total_comp if total_comp > 0 else 0
        
        user_avg_external = user_external_total / total_user if total_user > 0 else 0
        comp_avg_external = comp_external_total / total_comp if total_comp > 0 else 0
        
        return {
            "category_score": {
                "user": int(self._calculate_simple_score(user_data)),
                "competitor": int(self._calculate_simple_score(competitor_data))
            },
            "total_internal_links": {
                "user_value": f"{user_internal_total}",
                "competitor_value": f"{comp_internal_total}",
                "winner": "user" if user_internal_total > comp_internal_total else "competitor" if comp_internal_total > user_internal_total else "tie",
            },
            "total_external_links": {
                "user_value": f"{user_external_total}",
                "competitor_value": f"{comp_external_total}",
                "winner": "user" if user_external_total > comp_external_total else "competitor" if comp_external_total > user_external_total else "tie",
            },
            "avg_internal_links_per_page": {
                "user_value": f"{user_avg_internal:.1f}",
                "competitor_value": f"{comp_avg_internal:.1f}",
                "winner": "user" if user_avg_internal > comp_avg_internal else "competitor" if comp_avg_internal > user_avg_internal else "tie",
            },
            "avg_external_links_per_page": {
                "user_value": f"{user_avg_external:.1f}",
                "competitor_value": f"{comp_avg_external:.1f}",
                "winner": "user" if user_avg_external > comp_avg_external else "competitor" if comp_avg_external > user_avg_external else "tie",
            },
        }
    
    def _compare_social(
        self, 
        user_data: Dict[str, Any], 
        competitor_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare social media metrics"""
        user_results = user_data.get("url_results", [])
        comp_results = competitor_data.get("url_results", [])
        
        total_user = len(user_results)
        total_comp = len(comp_results)
        
        # Open Graph coverage
        user_og = sum(1 for r in user_results if r.get("open_graph_check", {}).get("status") == "PASS")
        comp_og = sum(1 for r in comp_results if r.get("open_graph_check", {}).get("status") == "PASS")
        
        user_og_pct = (user_og / total_user * 100) if total_user > 0 else 0
        comp_og_pct = (comp_og / total_comp * 100) if total_comp > 0 else 0
        
        return {
            "category_score": {
                "user": int(self._calculate_simple_score(user_data)),
                "competitor": int(self._calculate_simple_score(competitor_data))
            },
            "facebook_open_graph": {
                "user_value": f"{user_og_pct:.0f}%",
                "competitor_value": f"{comp_og_pct:.0f}%",
                "winner": "user" if user_og_pct > comp_og_pct else "competitor" if comp_og_pct > user_og_pct else "tie",
            },
        }
    
    def determine_winner(self, user_score: int, competitor_score: int) -> str:
        """Determine the winner based on scores"""
        if user_score > competitor_score:
            return "user"
        elif competitor_score > user_score:
            return "competitor"
        return "tie"
    
    def generate_summary(self, user_score: int, competitor_score: int, comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive human-readable summary"""
        gap = abs(user_score - competitor_score)
        winner = self.determine_winner(user_score, competitor_score)
        
        # Generate key takeaways
        takeaways = self._generate_takeaways(comparison, winner)
        
        # Determine competitive position
        if winner == "user":
            if gap >= 20:
                position = "Market Leader"
            elif gap >= 10:
                position = "Strong Performer"
            else:
                position = "Competitive Edge"
        elif winner == "competitor":
            if gap >= 20:
                position = "Significant Gap"
            elif gap >= 10:
                position = "Needs Improvement"
            else:
                position = "Close Competition"
        else:
            position = "Tied"
        
        if winner == "user":
            headline = f"You're ahead by {gap} points!"
            key_insight = "Your website has stronger SEO foundations than your competitor."
            encouragement = "Keep up the good work and continue optimizing!"
        elif winner == "competitor":
            headline = f"You're {gap} points behind your competitor"
            key_insight = self._generate_weakness_insight(comparison)
            encouragement = self._generate_strength_encouragement(comparison)
        else:
            headline = "You're tied with your competitor"
            key_insight = "Both websites have similar SEO strength."
            encouragement = "Small improvements can give you the edge!"
        
        return {
            "headline": headline,
            "key_insight": key_insight,
            "encouragement": encouragement,
            "key_takeaways": takeaways,
            "competitive_position": position,
        }
    
    def _generate_takeaways(self, comparison: Dict[str, Any], winner: str) -> List[str]:
        """Generate key takeaways from the comparison"""
        takeaways = []
        
        perf = comparison.get("performance", {})
        seo = comparison.get("seo", {})
        tech = comparison.get("technical", {})
        content = comparison.get("content", {})
        
        # Performance takeaways
        if perf.get("load_time", {}).get("winner") == "user":
            takeaways.append("Your pages load faster than your competitor's")
        elif perf.get("load_time", {}).get("winner") == "competitor":
            takeaways.append("Your competitor's pages load faster - prioritize speed optimization")
        
        # SEO takeaways
        user_meta = seo.get("meta_description_coverage", {}).get("user_value", "0%")
        comp_meta = seo.get("meta_description_coverage", {}).get("competitor_value", "0%")
        if user_meta == "0%" and comp_meta != "0%":
            takeaways.append("Your competitor uses meta descriptions - you should add them")
        
        # Technical takeaways
        if tech.get("https_security", {}).get("winner") == "user":
            takeaways.append("You have HTTPS enabled - good security foundation")
        elif tech.get("https_security", {}).get("winner") == "competitor":
            takeaways.append("Your competitor has HTTPS - you need SSL certificate")
        
        return takeaways[:3]  # Return top 3 takeaways
    
    def _generate_weakness_insight(self, comparison: Dict[str, Any]) -> str:
        """Generate insight about main weaknesses"""
        weaknesses = []
        
        perf = comparison.get("performance", {})
        seo = comparison.get("seo", {})
        tech = comparison.get("technical", {})
        
        if perf.get("load_time", {}).get("winner") == "competitor":
            weaknesses.append("page speed")
        if seo.get("meta_description_coverage", {}).get("winner") == "competitor":
            weaknesses.append("meta descriptions")
        if tech.get("mobile_friendly", {}).get("winner") == "competitor":
            weaknesses.append("mobile experience")
        if seo.get("schema_markup", {}).get("winner") == "competitor":
            weaknesses.append("structured data")
        
        if weaknesses:
            return f"Focus on improving: {', '.join(weaknesses[:2])}."
        return "Focus on overall SEO optimization to catch up."
    
    def _generate_strength_encouragement(self, comparison: Dict[str, Any]) -> str:
        """Generate encouragement based on strengths"""
        strengths = []
        
        perf = comparison.get("performance", {})
        seo = comparison.get("seo", {})
        tech = comparison.get("technical", {})
        
        if perf.get("load_time", {}).get("winner") == "user":
            strengths.append("page speed")
        if seo.get("title_optimization", {}).get("winner") == "user":
            strengths.append("title optimization")
        if tech.get("mobile_friendly", {}).get("winner") == "user":
            strengths.append("mobile experience")
        if seo.get("schema_markup", {}).get("winner") == "user":
            strengths.append("structured data")
        
        if strengths:
            return f"Good news: you're winning on {strengths[0]}!"
        return "With focused effort, you can catch up quickly."
    
    def generate_page_breakdown(
        self, 
        user_data: Dict[str, Any], 
        competitor_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate page-by-page comparison"""
        user_results = user_data.get("url_results", [])
        comp_results = competitor_data.get("url_results", [])
        
        page_comparisons = []
        
        # Compare up to 5 pages
        for i, user_page in enumerate(user_results[:5]):
            user_score = self._calculate_page_score(user_page)
            
            # Find matching competitor page or use first
            comp_page = comp_results[i] if i < len(comp_results) else (comp_results[0] if comp_results else None)
            comp_score = self._calculate_page_score(comp_page) if comp_page else 0
            
            winner = "user" if user_score > comp_score else "competitor" if comp_score > user_score else "tie"
            
            page_comparisons.append({
                "url": user_page.get("url", "Unknown"),
                "user_score": user_score,
                "competitor_score": comp_score,
                "winner": winner,
                "key_differences": self._get_page_differences(user_page, comp_page),
                "recommendations": self._get_page_recommendations(user_page, comp_page)
            })
        
        return page_comparisons
    
    def _calculate_page_score(self, page: Dict[str, Any]) -> int:
        """Calculate score for a single page"""
        checks = [
            page.get("title_length_check"),
            page.get("meta_description_length_check"),
            page.get("h1_check"),
            page.get("image_alt_check"),
            page.get("canonical_check"),
            page.get("open_graph_check"),
            page.get("mobile_responsiveness"),
        ]
        
        total = 0
        passed = 0
        
        for check in checks:
            if check:
                total += 1
                if check.get("status") == "PASS":
                    passed += 1
        
        return round((passed / total * 100)) if total > 0 else 0
    
    def _get_page_differences(self, user_page: Dict[str, Any], comp_page: Optional[Dict[str, Any]]) -> List[str]:
        """Get key differences between pages"""
        differences = []
        
        if not comp_page:
            differences.append("No comparable competitor page")
            return differences
        
        # Compare response time
        user_time = user_page.get("response_time_ms", 0)
        comp_time = comp_page.get("response_time_ms", 0)
        if user_time and comp_time:
            if user_time < comp_time:
                differences.append(f"Loads faster by {((comp_time - user_time) / 1000):.1f}s")
            elif comp_time < user_time:
                differences.append(f"Loads slower by {((user_time - comp_time) / 1000):.1f}s")
        
        return differences
    
    def _get_page_recommendations(self, user_page: Dict[str, Any], comp_page: Optional[Dict[str, Any]]) -> List[str]:
        """Get recommendations for a page"""
        recommendations = []
        
        if user_page.get("title_length_check", {}).get("status") != "PASS":
            recommendations.append("Optimize title length")
        
        if user_page.get("meta_description_length_check", {}).get("status") != "PASS":
            recommendations.append("Add or improve meta description")
        
        if user_page.get("h1_check", {}).get("status") != "PASS":
            recommendations.append("Fix H1 tag structure")
        
        if user_page.get("image_alt_check", {}).get("status") != "PASS":
            recommendations.append("Add alt text to images")
        
        return recommendations[:3]
    
    def generate_action_priority_matrix(
        self, 
        comparison: Dict[str, Any], 
        user_score: int, 
        competitor_score: int
    ) -> List[Dict[str, Any]]:
        """Generate prioritized action items with effort/impact matrix"""
        actions = []
        
        perf = comparison.get("performance", {})
        seo = comparison.get("seo", {})
        tech = comparison.get("technical", {})
        
        # High impact, easy effort actions
        if seo.get("meta_description_coverage", {}).get("winner") == "competitor":
            actions.append({
                "action": "Add meta descriptions",
                "category": "SEO",
                "impact": "high",
                "effort": "easy",
                "priority": 1,
                "description": "Add compelling meta descriptions to all pages",
                "steps": ["Write unique descriptions", "Keep under 160 characters", "Include target keywords"]
            })
        
        if seo.get("title_optimization", {}).get("winner") == "competitor":
            actions.append({
                "action": "Optimize page titles",
                "category": "SEO",
                "impact": "high",
                "effort": "easy",
                "priority": 2,
                "description": "Improve title tags for better click-through rates",
                "steps": ["Keep titles 50-60 characters", "Include primary keyword", "Make them compelling"]
            })
        
        if seo.get("image_alt_coverage", {}).get("winner") == "competitor":
            actions.append({
                "action": "Add image alt text",
                "category": "SEO",
                "impact": "medium",
                "effort": "easy",
                "priority": 3,
                "description": "Describe all images for accessibility and SEO",
                "steps": ["Audit all images", "Write descriptive alt text", "Include keywords naturally"]
            })
        
        if perf.get("load_time", {}).get("winner") == "competitor":
            actions.append({
                "action": "Improve page speed",
                "category": "Performance",
                "impact": "high",
                "effort": "medium",
                "priority": 4,
                "description": "Optimize loading times for better user experience",
                "steps": ["Compress images", "Minify CSS/JS", "Enable caching"]
            })
        
        if not tech.get("https_security", {}).get("winner") == "user":
            actions.append({
                "action": "Enable HTTPS",
                "category": "Technical",
                "impact": "high",
                "effort": "easy",
                "priority": 5,
                "description": "Secure your site with SSL certificate",
                "steps": ["Get SSL certificate", "Configure server", "Update internal links"]
            })
        
        # Sort by priority
        return sorted(actions, key=lambda x: x["priority"])
