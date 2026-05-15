"""
Suggestion Engine for Competitor Analysis
Generates business-friendly (Level 1) improvement suggestions
"""

from typing import Dict, Any, List
from src.config.logger_config import setup_logger


class SuggestionEngine:
    """Engine for generating business-friendly improvement suggestions"""
    
    def __init__(self):
        self.logger = setup_logger(__name__)
    
    def generate_suggestions(
        self,
        comparison: Dict[str, Any],
        user_score: int,
        competitor_score: int
    ) -> List[Dict[str, Any]]:
        """
        Generate prioritized suggestions based on comparison
        Returns Level 1 (business-friendly) suggestions
        """
        suggestions = []
        
        # Check performance issues
        perf_suggestions = self._generate_performance_suggestions(comparison)
        suggestions.extend(perf_suggestions)
        
        # Check SEO issues
        seo_suggestions = self._generate_seo_suggestions(comparison)
        suggestions.extend(seo_suggestions)
        
        # Check technical issues
        tech_suggestions = self._generate_technical_suggestions(comparison)
        suggestions.extend(tech_suggestions)
        
        # Sort by priority score (highest first)
        suggestions.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return suggestions
    
    def _generate_performance_suggestions(self, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions for performance issues"""
        suggestions = []
        perf = comparison.get("performance", {})
        
        # Check load time
        load_time = perf.get("load_time", {})
        if load_time.get("winner") == "competitor":
            user_val = load_time.get("user_value", "Unknown")
            comp_val = load_time.get("competitor_value", "Unknown")
            
            suggestions.append({
                "category": "performance",
                "priority": "critical",
                "priority_score": 95,
                "issue": "Your website loads too slowly",
                "your_metric": f"{user_val} average load time",
                "competitor_metric": f"{comp_val} average load time",
                "what_this_means": "Visitors leave slow websites. Google ranks them lower too. 40% of visitors leave if a site takes more than 3 seconds to load.",
                "what_you_should_do": [
                    "Contact your web developer about speed optimization",
                    "Ask your hosting provider about faster server options",
                    "Consider using a CDN service like CloudFlare",
                    "Compress images before uploading them"
                ],
                "expected_benefit": "Faster sites keep more visitors and rank higher. You could see 20-30% more traffic.",
                "timeline": "Complete within 2 weeks for best results"
            })
        
        # Check page size
        page_size = perf.get("page_size", {})
        if page_size.get("winner") == "competitor":
            user_val = page_size.get("user_value", "Unknown")
            comp_val = page_size.get("competitor_value", "Unknown")
            
            suggestions.append({
                "category": "performance",
                "priority": "high",
                "priority_score": 80,
                "issue": "Your pages are larger than they should be",
                "your_metric": f"{user_val} average page size",
                "competitor_metric": f"{comp_val} average page size",
                "what_this_means": "Large pages take longer to load, especially on mobile devices with slower connections.",
                "what_you_should_do": [
                    "Compress images using tools like TinyPNG or ImageOptim",
                    "Remove unnecessary plugins and scripts",
                    "Enable compression on your web server",
                    "Use lazy loading for images below the fold"
                ],
                "expected_benefit": "Smaller pages load faster, improving user experience and search rankings.",
                "timeline": "Complete within 1-2 weeks"
            })
        
        return suggestions
    
    def _generate_seo_suggestions(self, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions for SEO issues"""
        suggestions = []
        seo = comparison.get("seo", {})
        
        # Check meta descriptions
        meta_desc = seo.get("meta_description_coverage", {})
        if meta_desc.get("winner") == "competitor":
            user_val = meta_desc.get("user_value", "0%")
            comp_val = meta_desc.get("competitor_value", "100%")
            
            # Extract percentage
            try:
                user_pct = int(user_val.replace("%", ""))
            except:
                user_pct = 0
            
            if user_pct < 80:
                suggestions.append({
                    "category": "seo",
                    "priority": "high",
                    "priority_score": 88,
                    "issue": "Missing meta descriptions on your pages",
                    "your_metric": f"{user_val} of pages have descriptions",
                    "competitor_metric": f"{comp_val} of pages have descriptions",
                    "what_this_means": "Meta descriptions are the text people see in Google search results. Without them, Google shows random text from your page, which may not encourage clicks.",
                    "what_you_should_do": [
                        "Write unique descriptions for each important page",
                        "Keep them between 120-160 characters long",
                        "Include relevant keywords naturally",
                        "Make them compelling to encourage clicks"
                    ],
                    "expected_benefit": "Better descriptions lead to more clicks from Google search results, increasing your traffic.",
                    "timeline": "Complete within 1 week"
                })
        
        # Check title optimization
        title_opt = seo.get("title_optimization", {})
        if title_opt.get("winner") == "competitor":
            user_val = title_opt.get("user_value", "0%")
            comp_val = title_opt.get("competitor_value", "100%")
            
            suggestions.append({
                "category": "seo",
                "priority": "high",
                "priority_score": 85,
                "issue": "Your page titles need improvement",
                "your_metric": f"{user_val} of titles are optimized",
                "competitor_metric": f"{comp_val} of titles are optimized",
                "what_this_means": "Page titles appear as the clickable headline in Google search results. Poor titles hurt your click-through rates.",
                "what_you_should_do": [
                    "Keep titles between 30-60 characters",
                    "Include your main keyword near the beginning",
                    "Make each title unique and descriptive",
                    "Add power words like 'Best', 'Guide', 'Ultimate' to increase clicks"
                ],
                "expected_benefit": "Better titles lead to higher click-through rates from search results.",
                "timeline": "Complete within 1 week"
            })
        
        # Check heading structure
        headings = seo.get("heading_structure", {})
        if headings.get("winner") == "competitor":
            suggestions.append({
                "category": "seo",
                "priority": "medium",
                "priority_score": 70,
                "issue": "Your heading structure needs work",
                "your_metric": "Inconsistent heading usage",
                "competitor_metric": "Well-structured headings",
                "what_this_means": "Headings help Google understand your content structure and help visitors scan your pages.",
                "what_you_should_do": [
                    "Use only one H1 tag per page (main title)",
                    "Use H2 tags for main sections",
                    "Use H3 tags for subsections",
                    "Include relevant keywords in headings naturally"
                ],
                "expected_benefit": "Better structure helps both Google and visitors understand your content.",
                "timeline": "Complete within 2 weeks"
            })
        
        return suggestions
    
    def _generate_technical_suggestions(self, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggestions for technical issues"""
        suggestions = []
        tech = comparison.get("technical", {})
        
        # Check HTTPS
        https = tech.get("https_security", {})
        if https.get("winner") == "competitor":
            suggestions.append({
                "category": "technical",
                "priority": "critical",
                "priority_score": 98,
                "issue": "Your website is not secure (missing HTTPS)",
                "your_metric": "HTTPS not enabled",
                "competitor_metric": "HTTPS enabled",
                "what_this_means": "Without HTTPS, visitors see 'Not Secure' warnings. Google penalizes non-secure sites in search rankings.",
                "what_you_should_do": [
                    "Install an SSL certificate (many hosts offer free Let's Encrypt)",
                    "Update all internal links to use https://",
                    "Set up redirects from http:// to https://",
                    "Update your Google Search Console property"
                ],
                "expected_benefit": "Security is a ranking factor. HTTPS builds trust and improves search rankings.",
                "timeline": "Complete immediately - this is critical"
            })
        
        # Check mobile friendliness
        mobile = tech.get("mobile_friendly", {})
        if mobile.get("winner") == "competitor":
            user_val = mobile.get("user_value", "0%")
            comp_val = mobile.get("competitor_value", "100%")
            
            suggestions.append({
                "category": "technical",
                "priority": "high",
                "priority_score": 90,
                "issue": "Your mobile experience needs improvement",
                "your_metric": f"{user_val} mobile-friendly score",
                "competitor_metric": f"{comp_val} mobile-friendly score",
                "what_this_means": "Over 60% of web traffic comes from mobile devices. Poor mobile experience loses customers.",
                "what_you_should_do": [
                    "Test your site on real mobile devices",
                    "Ensure buttons are large enough to tap easily",
                    "Make text readable without zooming",
                    "Consider a responsive design if you don't have one"
                ],
                "expected_benefit": "Better mobile experience means more mobile visitors convert to customers.",
                "timeline": "Complete within 2-3 weeks"
            })
        
        return suggestions
    
    def generate_strengths(self, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate list of strengths (areas where user wins)"""
        strengths = []
        
        perf = comparison.get("performance", {})
        seo = comparison.get("seo", {})
        tech = comparison.get("technical", {})
        
        # Performance strengths
        if perf.get("load_time", {}).get("winner") == "user":
            strengths.append({
                "category": "performance",
                "metric": "Page Load Speed",
                "your_value": perf["load_time"]["user_value"],
                "competitor_value": perf["load_time"]["competitor_value"],
                "advantage": "Faster loading",
                "what_this_means": "Your website loads faster than your competitor, providing a better user experience.",
                "business_impact": "Fast-loading sites keep more visitors and rank higher in Google.",
                "keep_doing": "Continue monitoring your page speed and optimize images and scripts."
            })
        
        if perf.get("page_size", {}).get("winner") == "user":
            strengths.append({
                "category": "performance",
                "metric": "Page Size",
                "your_value": perf["page_size"]["user_value"],
                "competitor_value": perf["page_size"]["competitor_value"],
                "advantage": "Smaller pages",
                "what_this_means": "Your pages are smaller and more efficient than your competitor's.",
                "business_impact": "Smaller pages load faster and use less data, especially important for mobile users.",
                "keep_doing": "Continue optimizing images and removing unnecessary elements."
            })
        
        # SEO strengths
        if seo.get("meta_description_coverage", {}).get("winner") == "user":
            strengths.append({
                "category": "seo",
                "metric": "Meta Description Coverage",
                "your_value": seo["meta_description_coverage"]["user_value"],
                "competitor_value": seo["meta_description_coverage"]["competitor_value"],
                "advantage": "Better coverage",
                "what_this_means": "More of your pages have proper meta descriptions compared to your competitor.",
                "business_impact": "Better meta descriptions lead to higher click-through rates from search results.",
                "keep_doing": "Maintain complete meta description coverage across all important pages."
            })
        
        if seo.get("title_optimization", {}).get("winner") == "user":
            strengths.append({
                "category": "seo",
                "metric": "Title Optimization",
                "your_value": seo["title_optimization"]["user_value"],
                "competitor_value": seo["title_optimization"]["competitor_value"],
                "advantage": "Better titles",
                "what_this_means": "Your page titles are better optimized for search engines.",
                "business_impact": "Optimized titles improve your visibility and click-through rates in Google.",
                "keep_doing": "Continue writing compelling, keyword-rich titles."
            })
        
        # Technical strengths
        if tech.get("https_security", {}).get("winner") == "user":
            strengths.append({
                "category": "technical",
                "metric": "HTTPS Security",
                "your_value": "Enabled",
                "competitor_value": "Not Enabled",
                "advantage": "More secure",
                "what_this_means": "Your website is secure while your competitor's is not.",
                "business_impact": "Security builds trust with visitors and is a Google ranking factor.",
                "keep_doing": "Maintain your SSL certificate and keep it renewed."
            })
        
        if tech.get("mobile_friendly", {}).get("winner") == "user":
            strengths.append({
                "category": "technical",
                "metric": "Mobile Experience",
                "your_value": tech["mobile_friendly"]["user_value"],
                "competitor_value": tech["mobile_friendly"]["competitor_value"],
                "advantage": "Better mobile",
                "what_this_means": "Your website works better on mobile devices than your competitor's.",
                "business_impact": "With 60%+ mobile traffic, you're capturing mobile customers better.",
                "keep_doing": "Continue testing on real mobile devices and optimize mobile experience."
            })
        
        return strengths
    
    def generate_weaknesses(self, comparison: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate list of weaknesses (areas where user loses)"""
        weaknesses = []
        
        perf = comparison.get("performance", {})
        seo = comparison.get("seo", {})
        tech = comparison.get("technical", {})
        
        # Performance weaknesses
        if perf.get("load_time", {}).get("winner") == "competitor":
            weaknesses.append({
                "category": "performance",
                "metric": "Page Load Speed",
                "your_value": perf["load_time"]["user_value"],
                "competitor_value": perf["load_time"]["competitor_value"],
                "gap": "Slower",
                "what_this_means": "Your website loads slower than your competitor, potentially losing visitors.",
                "business_impact": "Slow sites have higher bounce rates and lower search rankings.",
                "improvement_priority": "Critical - fix this first"
            })
        
        # SEO weaknesses
        if seo.get("meta_description_coverage", {}).get("winner") == "competitor":
            user_val = seo["meta_description_coverage"]["user_value"]
            try:
                user_pct = int(user_val.replace("%", ""))
            except:
                user_pct = 0
            
            if user_pct < 80:
                weaknesses.append({
                    "category": "seo",
                    "metric": "Meta Description Coverage",
                    "your_value": user_val,
                    "competitor_value": seo["meta_description_coverage"]["competitor_value"],
                    "gap": "Lower coverage",
                    "what_this_means": "Many of your pages lack meta descriptions that appear in Google results.",
                    "business_impact": "Missing descriptions reduce click-through rates from search results.",
                    "improvement_priority": "High - easy fix with big impact"
                })
        
        # Technical weaknesses
        if tech.get("https_security", {}).get("winner") == "competitor":
            weaknesses.append({
                "category": "technical",
                "metric": "HTTPS Security",
                "your_value": "Not Enabled",
                "competitor_value": "Enabled",
                "gap": "Not secure",
                "what_this_means": "Your website shows 'Not Secure' warnings to visitors.",
                "business_impact": "Security warnings scare visitors away and hurt Google rankings.",
                "improvement_priority": "Critical - fix immediately"
            })
        
        return weaknesses
