"""Build dashboard payload for competitor analysis from two site audit dicts."""

from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Set
from urllib.parse import urlparse

_STOP = {
    "that",
    "this",
    "with",
    "from",
    "your",
    "have",
    "will",
    "been",
    "were",
    "they",
    "their",
    "what",
    "when",
    "where",
    "which",
    "while",
    "about",
    "into",
    "more",
    "some",
    "than",
    "then",
    "very",
    "just",
    "also",
    "only",
    "here",
    "such",
    "make",
    "like",
    "each",
    "other",
}


def _check_status(val: Any) -> Optional[str]:
    if val is None:
        return None
    if isinstance(val, dict):
        return str(val.get("status", "")).upper() or None
    return None


def _infer_page_type(url: str) -> str:
    try:
        path = (urlparse(url).path or "/").lower()
    except Exception:
        return "other"
    if path in ("", "/"):
        return "home"
    if any(x in path for x in ("/dp/", "/gp/product", "/product/", "/products/", "/p/")):
        return "product"
    if any(x in path for x in ("/blog", "/news", "/articles/", "/post/")):
        return "blog"
    if path.endswith((".txt", ".md", ".xml", ".json")):
        return "other"
    return "page"


def _tokens(text: str) -> Set[str]:
    if not text:
        return set()
    return {w for w in re.findall(r"\b[a-z0-9]{4,}\b", text.lower()) if w not in _STOP}


def _page_keywords(row: Dict[str, Any]) -> List[str]:
    parts = [
        row.get("title") or "",
        row.get("meta_description") or "",
        row.get("h1") or "",
        row.get("meta_keywords") or "",
    ]
    bag: Set[str] = set()
    for p in parts:
        bag |= _tokens(p)
    out = sorted(bag)
    return out[:24]


def _classify_intent(keyword: str) -> str:
    k = keyword.lower()
    if re.search(r"\b(how|what|why|when|guide|tutorial|learn|tips|ideas|meaning)\b", k):
        return "informational"
    if re.search(r"\b(login|signin|signup|account|contact|careers|map|directory)\b", k):
        return "navigational"
    if re.search(r"\b(buy|price|pricing|shop|cart|checkout|coupon|deal|order|discount)\b", k):
        return "transactional"
    if re.search(r"\b(best|review|reviews|vs|versus|top|alternative|compare)\b", k):
        return "commercial"
    if len(k) >= 8:
        return "informational"
    return "informational"


def _https_ok(base: Dict[str, Any]) -> bool:
    return _check_status(base.get("https_ssl_check")) == "PASS"


def _sample_title(url_results: List[Dict[str, Any]]) -> str:
    for r in url_results:
        t = (r.get("title") or "").strip()
        if t:
            return t[:120]
    return ""


def _sample_meta(url_results: List[Dict[str, Any]]) -> str:
    for r in url_results:
        m = (r.get("meta_description") or "").strip()
        if m:
            return m[:160]
    return ""


def _mobile_pass_rate(url_results: List[Dict[str, Any]]) -> Optional[float]:
    if not url_results:
        return None
    ok = 0
    for r in url_results:
        if _check_status(r.get("mobile_responsiveness")) == "PASS":
            ok += 1
    return round(100.0 * ok / len(url_results), 1)


def _count_fail_checks(url_results: List[Dict[str, Any]]) -> int:
    keys = [
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
    n = 0
    for r in url_results:
        if not isinstance(r, dict):
            continue
        for k in keys:
            if _check_status(r.get(k)) == "FAIL":
                n += 1
    return n


def _winner_numeric(
    user_val: Optional[float], comp_val: Optional[float], lower_is_better: bool = False
) -> Optional[str]:
    if user_val is None or comp_val is None:
        return None
    if user_val == comp_val:
        return "tie"
    if lower_is_better:
        return "user" if user_val < comp_val else "competitor"
    return "user" if user_val > comp_val else "competitor"


def _winner_bool_tie_ok(u: bool, c: bool) -> Optional[str]:
    if u == c:
        return "tie"
    return "user" if u and not c else "competitor"


def _content_gaps(
    user_results: List[Dict[str, Any]], comp_results: List[Dict[str, Any]], max_gaps: int = 12
) -> List[Dict[str, Any]]:
    user_corpus: Set[str] = set()
    for r in user_results:
        if not isinstance(r, dict):
            continue
        user_corpus |= _tokens(
            f"{r.get('title', '')} {r.get('meta_description', '')} {r.get('h1', '')}"
        )
    gaps: List[Dict[str, Any]] = []
    seen_topics: Set[str] = set()
    for r in comp_results:
        title = (r.get("title") or "").strip()
        if not title or len(title) < 8:
            continue
        rt = _tokens(title)
        if not rt:
            continue
        overlap = len(rt & user_corpus)
        if overlap >= max(2, int(0.35 * len(rt))):
            continue
        topic_key = title.lower()[:80]
        if topic_key in seen_topics:
            continue
        seen_topics.add(topic_key)
        gaps.append(
            {
                "topic": title[:200],
                "example_competitor_urls": [str(r.get("url", ""))],
            }
        )
        if len(gaps) >= max_gaps:
            break
    return gaps


def _keywords_by_intent(all_keywords: Iterable[str]) -> Dict[str, List[str]]:
    buckets = {
        "informational": [],
        "navigational": [],
        "transactional": [],
        "commercial": [],
    }
    seen: Set[str] = set()
    for kw in all_keywords:
        k = kw.strip()
        if not k or len(k) < 4 or k.lower() in seen:
            continue
        seen.add(k.lower())
        intent = _classify_intent(k)
        buckets[intent].append(k)
    for k in buckets:
        buckets[k] = sorted(set(buckets[k]))[:40]
    return buckets


_FAIL_SUGGESTION: Dict[str, str] = {
    "title_length_check": "Adjust title tag length (roughly 30–60 characters) and make it descriptive.",
    "title_keyword_presence": "Include a clear primary topic in the title tag.",
    "meta_description_length_check": "Write a meta description around 120–160 characters.",
    "meta_description_keyword_presence": "Reflect the page topic in the meta description.",
    "h1_check": "Use exactly one descriptive H1 per page.",
    "image_alt_check": "Add meaningful alt text to important images.",
    "canonical_check": "Add or fix canonical tags on pages with duplicate or parameterized URLs.",
    "noindex_check": "Remove accidental noindex if the page should rank.",
    "open_graph_check": "Add Open Graph tags for better social previews.",
    "schema_validation": "Fix or add valid JSON-LD structured data.",
    "html_size_check": "Reduce HTML payload size where possible.",
    "response_time_check": "Improve server response or caching to speed up TTFB.",
    "js_minification_check": "Minify or defer non-critical JavaScript.",
    "css_minification_check": "Minify CSS and remove unused styles where possible.",
    "mobile_responsiveness": "Fix viewport and layout so the page passes mobile checks.",
}


def _suggestions_from_failures(url_results: List[Dict[str, Any]], limit: int = 10) -> List[str]:
    keys = list(_FAIL_SUGGESTION.keys())
    out: List[str] = []
    seen: Set[str] = set()
    for r in url_results:
        if not isinstance(r, dict):
            continue
        page = str(r.get("url", ""))[:96]
        for key in keys:
            if _check_status(r.get(key)) != "FAIL":
                continue
            hint = _FAIL_SUGGESTION.get(key, f"Review {key.replace('_', ' ')}")
            line = f"{hint} ({page})" if page else hint
            if line in seen:
                continue
            seen.add(line)
            out.append(line)
            if len(out) >= limit:
                return out
    return out


def _recommendations(
    user_score: int,
    comp_score: int,
    user_fails: int,
    user_mobile_rate: Optional[float],
) -> List[Dict[str, Any]]:
    recs: List[Dict[str, Any]] = []
    if user_score < comp_score:
        recs.append(
            {
                "priority": "high",
                "category": "seo",
                "title": "Close the SEO score gap",
                "details": (
                    "Your overall score is lower than the competitor. Start by fixing FAIL checks, "
                    "then convert WARNING checks to PASS across titles/meta, canonicals, schema, "
                    "and mobile responsiveness."
                ),
            }
        )
    if user_fails >= 8:
        recs.append(
            {
                "priority": "high",
                "category": "technical",
                "title": "Fix failing technical/on-page checks",
                "details": (
                    f"Detected {user_fails} failing checks. Prioritize noindex, missing H1, "
                    "missing alt text, invalid schema, and poor mobile responsiveness on key pages."
                ),
            }
        )
    elif user_fails >= 1:
        recs.append(
            {
                "priority": "medium",
                "category": "technical",
                "title": "Tighten on-page technical SEO",
                "details": (
                    f"There are {user_fails} failing checks across analyzed pages. "
                    "Address FAIL items first, then warnings."
                ),
            }
        )
    if user_mobile_rate is not None and user_mobile_rate < 70:
        recs.append(
            {
                "priority": "medium",
                "category": "ux",
                "title": "Improve mobile experience",
                "details": (
                    "Many pages are failing mobile responsiveness checks. Ensure a correct viewport tag "
                    "and fix layout issues that break on small screens."
                ),
            }
        )
    if not recs:
        recs.append(
            {
                "priority": "low",
                "category": "seo",
                "title": "Keep monitoring",
                "details": "No major gaps detected versus the competitor on the analyzed sample. Re-run with a higher max_pages or FULL_CRAWL for deeper coverage.",
            }
        )
    return recs


def build_competitor_analysis_payload(
    user_site: Dict[str, Any],
    competitor_site: Dict[str, Any],
    errors: Dict[str, str],
) -> Dict[str, Any]:
    user_results: List[Dict[str, Any]] = list(user_site.get("url_results") or [])
    comp_results: List[Dict[str, Any]] = list(competitor_site.get("url_results") or [])

    user_pages: List[Dict[str, Any]] = []
    for r in user_results:
        if not isinstance(r, dict):
            continue
        url = str(r.get("url", ""))
        user_pages.append(
            {
                "url": url,
                "page_type": _infer_page_type(url),
                "title": (r.get("title") or "")[:500],
                "meta_description": (r.get("meta_description") or "")[:500],
                "keywords": _page_keywords(r),
            }
        )

    competitor_pages: List[Dict[str, Any]] = []
    for r in comp_results:
        if not isinstance(r, dict):
            continue
        url = str(r.get("url", ""))
        competitor_pages.append(
            {
                "url": url,
                "page_type": _infer_page_type(url),
                "title": (r.get("title") or "")[:500],
                "meta_description": (r.get("meta_description") or "")[:500],
                "keywords": _page_keywords(r),
            }
        )

    all_kw: List[str] = []
    for p in user_pages + competitor_pages:
        all_kw.extend(p.get("keywords") or [])

    user_score = int(user_site.get("score") or 0)
    comp_score = int(competitor_site.get("score") or 0)
    user_base = user_site.get("base_url_checks") or {}
    comp_base = competitor_site.get("base_url_checks") or {}

    u_https = _https_ok(user_base)
    c_https = _https_ok(comp_base)

    u_avg = user_site.get("avg_response_time_ms")
    c_avg = competitor_site.get("avg_response_time_ms")
    u_mob = _mobile_pass_rate(user_results)
    c_mob = _mobile_pass_rate(comp_results)

    user_fails = _count_fail_checks(user_results)

    comparison: List[Dict[str, Any]] = [
        {
            "feature": "SEO Score",
            "user": user_score,
            "competitor": comp_score,
            "winner": _winner_numeric(float(user_score), float(comp_score)),
        },
        {
            "feature": "HTTPS",
            "user": u_https,
            "competitor": c_https,
            "winner": _winner_bool_tie_ok(u_https, c_https),
        },
        {
            "feature": "Site Title (sample)",
            "user": _sample_title(user_results) or None,
            "competitor": _sample_title(comp_results) or None,
            "winner": None,
        },
        {
            "feature": "Meta Description (sample)",
            "user": _sample_meta(user_results) or None,
            "competitor": _sample_meta(comp_results) or None,
            "winner": None,
        },
        {
            "feature": "Pages Analyzed",
            "user": len(user_pages),
            "competitor": len(competitor_pages),
            "winner": _winner_numeric(float(len(user_pages)), float(len(competitor_pages))),
        },
        {
            "feature": "Avg Response Time (ms)",
            "user": round(u_avg, 1) if isinstance(u_avg, (int, float)) else None,
            "competitor": round(c_avg, 1) if isinstance(c_avg, (int, float)) else None,
            "winner": _winner_numeric(
                float(u_avg) if isinstance(u_avg, (int, float)) else None,
                float(c_avg) if isinstance(c_avg, (int, float)) else None,
                lower_is_better=True,
            ),
        },
        {
            "feature": "Mobile PASS Rate",
            "user": u_mob,
            "competitor": c_mob,
            "winner": _winner_numeric(u_mob, c_mob) if u_mob is not None or c_mob is not None else None,
        },
    ]

    payload: Dict[str, Any] = {
        "user_pages": user_pages,
        "competitor_pages": competitor_pages,
        "content_gaps": _content_gaps(user_results, comp_results),
        "keywords_by_intent": _keywords_by_intent(all_kw),
        "user_seo_score": user_score,
        "competitor_seo_score": comp_score,
        "comparison": comparison,
        "recommendations": _recommendations(user_score, comp_score, user_fails, u_mob),
        "user_site": user_site,
        "competitor_site": competitor_site,
        "suggestions": _suggestions_from_failures(user_results),
        "errors": errors or {},
    }
    return payload
