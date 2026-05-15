"""
Shared SEO Scoring Utility
Provides consistent scoring across all SEO analysis features
"""

from typing import Dict, Any, List
from statistics import mean


class SEOScorer:
    """
    Standardized SEO scoring calculator
    Used by both Site Crawler and Competitor Analysis for consistency
    """
    
    @staticmethod
    def calculate_overall_score(seo_data: Dict[str, Any]) -> int:
        """
        Calculate overall SEO score (0-100) from SEO analysis data
        
        Weights:
        - Performance: 35%
        - SEO: 40%
        - Technical: 25%
        """
        try:
            performance_score = SEOScorer._calculate_performance_score(seo_data)
            seo_score = SEOScorer._calculate_seo_score(seo_data)
            technical_score = SEOScorer._calculate_technical_score(seo_data)
            
            # Weighted average
            total_score = (
                performance_score * 0.35 +  # Performance: 35%
                seo_score * 0.40 +          # SEO: 40%
                technical_score * 0.25      # Technical: 25%
            )
            
            return min(100, max(0, int(total_score)))
        except Exception as e:
            return 0
    
    @staticmethod
    def _calculate_performance_score(seo_data: Dict[str, Any]) -> float:
        """Calculate performance score (0-100)"""
        scores = []
        
        url_results = seo_data.get("url_results", [])
        if not url_results:
            return 50.0  # Default if no data
        
        # Response time score
        response_times = [
            r.get("response_time_ms", 0) 
            for r in url_results 
            if r.get("response_time_ms")
        ]
        if response_times:
            avg_response_time = mean(response_times)
            # Score: <0.5s=100, 0.5-1s=80, 1-2s=60, 2-3s=40, >3s=20
            if avg_response_time < 500:
                scores.append(100)
            elif avg_response_time < 1000:
                scores.append(80)
            elif avg_response_time < 2000:
                scores.append(60)
            elif avg_response_time < 3000:
                scores.append(40)
            else:
                scores.append(20)
        
        # Page size score
        html_sizes = [
            r.get("html_size_bytes", 0) 
            for r in url_results 
            if r.get("html_size_bytes")
        ]
        if html_sizes:
            avg_size = mean(html_sizes)
            # Score: <100KB=100, 100-500KB=80, 500KB-1MB=60, 1-2MB=40, >2MB=20
            if avg_size < 100000:
                scores.append(100)
            elif avg_size < 500000:
                scores.append(80)
            elif avg_size < 1000000:
                scores.append(60)
            elif avg_size < 2000000:
                scores.append(40)
            else:
                scores.append(20)
        
        # Minification score
        js_scores = [r.get("js_minification_check", {}).get("status") for r in url_results]
        css_scores = [r.get("css_minification_check", {}).get("status") for r in url_results]
        
        pass_count = js_scores.count("PASS") + css_scores.count("PASS")
        total_checks = len(js_scores) + len(css_scores)
        if total_checks > 0:
            minification_score = (pass_count / total_checks) * 100
            scores.append(minification_score)
        
        return mean(scores) if scores else 50.0
    
    @staticmethod
    def _calculate_seo_score(seo_data: Dict[str, Any]) -> float:
        """Calculate SEO score (0-100)"""
        scores = []
        
        url_results = seo_data.get("url_results", [])
        if not url_results:
            return 50.0
        
        total_pages = len(url_results)
        
        # Title optimization
        title_checks = [r.get("title_length_check", {}).get("status") for r in url_results]
        pass_count = title_checks.count("PASS")
        scores.append((pass_count / total_pages * 100) if total_pages > 0 else 0)
        
        # Meta description coverage
        meta_checks = [r.get("meta_description_length_check", {}).get("status") for r in url_results]
        pass_count = meta_checks.count("PASS")
        scores.append((pass_count / total_pages * 100) if total_pages > 0 else 0)
        
        # H1 structure
        h1_checks = [r.get("h1_check", {}).get("status") for r in url_results]
        pass_count = h1_checks.count("PASS")
        scores.append((pass_count / total_pages * 100) if total_pages > 0 else 0)
        
        # Image alt text
        images_with_alt = sum(
            1 for r in url_results 
            if r.get("image_alt_check", {}).get("status") == "PASS"
        )
        scores.append((images_with_alt / total_pages * 100) if total_pages > 0 else 0)
        
        # Canonical tags
        canonical_checks = [r.get("canonical_check", {}).get("status") for r in url_results]
        pass_count = canonical_checks.count("PASS")
        scores.append((pass_count / total_pages * 100) if total_pages > 0 else 0)
        
        # Schema markup
        schema_checks = [r.get("schema_validation", {}).get("status") for r in url_results]
        pass_count = schema_checks.count("PASS")
        scores.append((pass_count / total_pages * 100) if total_pages > 0 else 0)
        
        return mean(scores) if scores else 50.0
    
    @staticmethod
    def _calculate_technical_score(seo_data: Dict[str, Any]) -> float:
        """Calculate technical SEO score (0-100)"""
        scores = []
        
        base_checks = seo_data.get("base_url_checks", {})
        
        # HTTPS SSL
        https_check = base_checks.get("https_ssl_check", {})
        if https_check.get("status") == "PASS":
            scores.append(100)
        else:
            scores.append(0)
        
        # Mobile responsiveness
        url_results = seo_data.get("url_results", [])
        mobile_checks = [r.get("mobile_responsiveness", {}).get("status") for r in url_results]
        pass_count = mobile_checks.count("PASS")
        total = len(mobile_checks)
        scores.append((pass_count / total * 100) if total > 0 else 50)
        
        # Robots.txt
        robots_check = base_checks.get("robots_txt_check", {})
        if robots_check.get("status") == "PASS":
            scores.append(100)
        else:
            scores.append(50)
        
        return mean(scores) if scores else 50.0
    
    @staticmethod
    def calculate_simple_score(seo_data: Dict[str, Any]) -> int:
        """
        Calculate simple score based on base_url_checks only
        Used for backward compatibility with existing analyses
        """
        base_checks = seo_data.get("base_url_checks", {})
        if not base_checks:
            return 0
        
        # Count passed checks
        passed = 0
        total = 0
        
        for key, value in base_checks.items():
            if key == "base_url":
                continue
            total += 1
            if isinstance(value, dict) and value.get("status") == "PASS":
                passed += 1
            elif value == True:
                passed += 1
        
        return int((passed / total * 100)) if total > 0 else 0
