from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


def _safe_str_status(status_value: Any) -> Optional[str]:
    if status_value is None:
        return None
    if isinstance(status_value, str):
        return status_value.strip()
    return str(status_value).strip()


def compute_seo_base_url_checks_metrics(base_url_checks: Optional[Dict[str, Any]]) -> Dict[str, int]:
    """
    Compute:
    - criticalIssues: number of FAIL checks
    - warnings: number of WARNING checks
    - passedChecks: number of PASS checks
    - score: percentage based on passed checks out of all checks (PASS+WARNING+FAIL)
    """
    if not base_url_checks:
        return {
            "criticalIssues": 0,
            "warnings": 0,
            "passedChecks": 0,
            "score": 0,
        }

    critical = 0
    warnings = 0
    passed = 0

    for value in base_url_checks.values():
        if not isinstance(value, dict):
            continue
        status_value = _safe_str_status(value.get("status"))
        if status_value == "FAIL":
            critical += 1
        elif status_value == "WARNING":
            warnings += 1
        elif status_value == "PASS":
            passed += 1

    total = critical + warnings + passed
    score = int(round((passed / total) * 100)) if total > 0 else 0

    return {
        "criticalIssues": critical,
        "warnings": warnings,
        "passedChecks": passed,
        "score": score,
    }


def infer_result_status(model_status: Any, fallback: str = "completed") -> str:
    """Normalize status; fallback to `fallback` when not present."""
    normalized = _safe_str_status(model_status)
    if normalized in {"completed", "processing", "failed"}:
        return normalized
    # When status isn't in the model yet, treat existing rows as completed by default.
    return fallback


def compute_keyword_suggestion_metrics(
    related_searches: Optional[List[Any]],
    long_tail_keywords: Optional[List[Any]],
    search_results: Optional[List[Any]],
) -> Dict[str, int]:
    related_searches = related_searches or []
    long_tail_keywords = long_tail_keywords or []
    search_results = search_results or []

    return {
        "relatedKeywordsCount": len(related_searches),
        "longTailKeywordsCount": len(long_tail_keywords),
        "searchResultsCount": len(search_results),
    }


def compute_keyword_rank_metrics(
    target_url: str,
    target_position: Optional[int],
    search_results: Optional[List[Dict[str, Any]]],
) -> Dict[str, Any]:
    parsed = urlparse(target_url or "")
    domain = parsed.netloc or target_url or ""

    search_results = search_results or []
    positions: List[int] = []
    top10 = 0

    for item in search_results:
        if not isinstance(item, dict):
            continue
        pos = item.get("position")
        if isinstance(pos, int):
            positions.append(pos)
        elif pos is not None:
            try:
                positions.append(int(pos))
            except Exception:
                pass

    for pos in positions:
        if pos <= 10:
            top10 += 1

    avg_position = mean(positions) if positions else None
    not_ranking = 1 if target_position is None else 0

    return {
        "domain": domain,
        "top10Count": top10,
        "notRankingCount": not_ranking,
        "avgPosition": avg_position,
    }

