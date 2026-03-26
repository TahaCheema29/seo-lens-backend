# Remaining APIs to Implement

---

## Already Implemented ✅

| Module | Endpoints |
|--------|-----------|
| Authentication | `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, `PUT /auth/me`, `DELETE /auth/me` |
| Admin Auth | `POST /admin/auth/register`, `POST /admin/auth/login`, `POST /admin/auth/logout`, `GET /admin/auth/me`, `GET /admin/auth/admins` |
| Admin Users | `GET /admin/users`, `GET /admin/users/:id`, `PUT /admin/users/:id/activate`, `PUT /admin/users/:id/deactivate`, `PUT /admin/users/:id/role/:role`, `DELETE /admin/users/:id` |
| Keyword Rank | `POST /keyword-rank/analyze`, `GET /keyword-rank/results`, `GET /keyword-rank/results/:id`, `DELETE /keyword-rank/results/:id` |
| Keyword Suggestion | `POST /keyword-suggestion/analyze`, `GET /keyword-suggestion/results`, `GET /keyword-suggestion/results/:id`, `DELETE /keyword-suggestion/results/:id` |
| SEO Insight | `POST /seo-insight/analyze`, `GET /seo-insight/results`, `GET /seo-insight/results/:id`, `DELETE /seo-insight/results/:id` |

---

## Schema Updates Required ⚠️

### `GET /seo-insight/results`
Add computed fields:
- `score` - calculate from `base_url_checks`
- `criticalIssues` - count from `base_url_checks`
- `warnings` - count from `base_url_checks`
- `passedChecks` - count from `base_url_checks`
- `pageCount` - rename from `total_pages`
- `status` - add column to model (`completed`, `processing`, `failed`)

### `GET /keyword-suggestion/results`
Add computed fields:
- `relatedKeywordsCount` - `len(related_searches)`
- `longTailKeywordsCount` - `len(long_tail_keywords)`
- `searchResultsCount` - `len(search_results)`
- `status` - add column to model

### `GET /keyword-rank/results`
Add computed fields:
- `domain` - extract from `target_url`
- `top10Count` - count positions <= 10 from results
- `notRankingCount` - count keywords not found
- `avgPosition` - average position from results
- `status` - add column to model

---

## Remaining APIs to Implement ❌

### 1. Dashboard API (1 endpoint)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/overview` | Get dashboard KPIs and recent analyses |

**Response:**
```json
{
  "seoScore": 84,
  "keywordsTracked": 2847,
  "backlinks": 1234,
  "organicTraffic": "45.2K",
  "performanceChart": [...],
  "recentAnalyses": { "seo": [...], "keywords": [...], "rank": [...] }
}
```

---

### 2. SEO Insight Stats (1 endpoint)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/seo-insight/stats` | Get aggregated stats for dashboard cards |

**Response:**
```json
{
  "avgScore": 78,
  "totalCritical": 12,
  "totalWarnings": 45,
  "completedCount": 8,
  "processingCount": 2,
  "failedCount": 1
}
```

---

### 3. Keyword Suggestion Stats (1 endpoint)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/keyword-suggestion/stats` | Get aggregated stats for dashboard cards |

**Response:**
```json
{
  "totalKeywords": 1250,
  "completedCount": 10,
  "processingCount": 2,
  "avgRelatedKeywords": 45
}
```

---

### 4. Keyword Rank Stats (1 endpoint)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/keyword-rank/stats` | Get aggregated stats for dashboard cards |

**Response:**
```json
{
  "totalKeywords": 150,
  "top10Count": 25,
  "avgPosition": 12.5,
  "completedCount": 8,
  "processingCount": 1
}
```

---

## Summary

| Type | Count |
|------|-------|
| New Endpoints | 4 |
| Schema Updates | 3 |

---

## Implementation Priority

1. **Add `status` column** to `seo_insights`, `keyword_suggestions`, `keyword_ranks` tables
2. **Update response schemas** to include computed fields
3. **Implement `/dashboard/overview`** - aggregates data from all tables
4. **Implement `/seo-insight/stats`**
5. **Implement `/keyword-suggestion/stats`**
6. **Implement `/keyword-rank/stats`**