from __future__ import annotations

from typing import Any, Dict, List, Optional


def calculate_seo_score(base_checks: dict, url_results: Optional[List[dict]] = None) -> int:
    """
    Calculate SEO score matching frontend logic:
    PASS = 100%, WARNING = 50%, FAIL = 0%
    """
    if not base_checks:
        return 0

    total_checks = 0
    passed_checks = 0
    warning_checks = 0
    failed_checks = 0

    base_check_keys = [
        "www_redirect_check",
        "robots_txt_check",
        "https_ssl_check",
        "directory_listing_check",
        "expires_headers_check",
        "caching_advice",
    ]

    # Base URL checks
    for key in base_check_keys:
        check = base_checks.get(key)
        if not check:
            continue

        total_checks += 1
        if isinstance(check, dict):
            status = check.get("status", "")
            if status == "PASS":
                passed_checks += 1
            elif status == "WARNING":
                warning_checks += 1
            elif status == "FAIL":
                failed_checks += 1
        elif check is True:
            passed_checks += 1
        elif check is False:
            failed_checks += 1

    # Per-URL checks
    if url_results:
        url_check_keys = [
            "title_length_check",
            "title_keyword_presence",
            "meta_description_length_check",
            "meta_description_keyword_presence",
            "h1_check",
            "image_alt_check",
            "canonical_check",
            "noindex_check",
            "open_graph_check",
            "schema_validation",
            "html_size_check",
            "response_time_check",
            "js_minification_check",
            "css_minification_check",
            "mobile_responsiveness",
        ]

        for result in url_results:
            if not isinstance(result, dict):
                continue

            for key in url_check_keys:
                check = result.get(key)
                if not check:
                    continue

                total_checks += 1
                if isinstance(check, dict):
                    status = check.get("status", "")
                    if status == "PASS":
                        passed_checks += 1
                    elif status == "WARNING":
                        warning_checks += 1
                    elif status == "FAIL":
                        failed_checks += 1
                elif check is True:
                    passed_checks += 1
                elif check is False:
                    failed_checks += 1

    if total_checks == 0:
        return 0

    # Calculate score: PASS = 100%, WARNING = 50%, FAIL = 0%
    # Match frontend formula: Math.round(((passed * 100 + warning * 50) / total))
    return round((passed_checks * 100 + warning_checks * 50) / total_checks)

