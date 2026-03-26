# SEO Lens API Specification

## Overview

This document outlines all REST API endpoints required for the SEO Lens platform, including the User Dashboard, Admin Dashboard, and Public Website tools.

**Base URL**: `https://api.seolens.com/v1`

**Authentication**: All endpoints except public website tools require JWT Bearer token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

---

## Table of Contents

1. [Authentication APIs](#1-authentication-apis)
2. [User Dashboard APIs](#2-user-dashboard-apis)
3. [Admin Dashboard APIs](#3-admin-dashboard-apis)
4. [Public Website APIs](#4-public-website-apis)
5. [Common Response Patterns](#5-common-response-patterns)

---

## 1. Authentication APIs

### 1.1 User Registration
```
POST /auth/register
```

**Request Body:**
```json
{
  "email": "string",
  "password": "string",
  "name": "string"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "createdAt": "2024-01-16T10:00:00Z"
    },
    "token": "jwt_access_token",
    "refreshToken": "jwt_refresh_token"
  }
}
```

### 1.2 User Login
```
POST /auth/login
```

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "user"
    },
    "token": "jwt_access_token",
    "refreshToken": "jwt_refresh_token"
  }
}
```

### 1.3 Logout
```
POST /auth/logout
```

**Response (200):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

### 1.4 Refresh Token
```
POST /auth/refresh
```

**Request Body:**
```json
{
  "refreshToken": "jwt_refresh_token"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "token": "new_jwt_access_token",
    "refreshToken": "new_jwt_refresh_token"
  }
}
```

### 1.5 Forgot Password
```
POST /auth/forgot-password
```

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Password reset email sent"
}
```

### 1.6 Reset Password
```
POST /auth/reset-password
```

**Request Body:**
```json
{
  "token": "reset_token",
  "newPassword": "string"
}
```

### 1.7 Verify Email
```
POST /auth/verify-email
```

**Request Body:**
```json
{
  "token": "verification_token"
}
```

### 1.8 Get Current User
```
GET /auth/me
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "user",
      "company": "Acme Corp",
      "website": "https://acme.com",
      "plan": "professional",
      "status": "active"
    }
  }
}
```

---

## 2. User Dashboard APIs

### 2.1 Dashboard Overview

#### Get Dashboard Overview
```
GET /dashboard/overview
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "seoScore": 84,
    "keywordsTracked": 2847,
    "backlinks": 8432,
    "organicTraffic": "45.2K",
    "trends": {
      "seoScoreChange": 5.2,
      "trafficChange": 12.5,
      "backlinksChange": 8.3
    },
    "performanceChart": [
      { "label": "Mon", "value": 65, "color": "#3b82f6" },
      { "label": "Tue", "value": 78, "color": "#10b981" },
      { "label": "Wed", "value": 82, "color": "#f59e0b" }
    ],
    "planUsage": {
      "sites": { "used": 12, "limit": 50, "percentage": 24 },
      "keywords": { "used": 2847, "limit": 10000, "percentage": 28 },
      "reports": { "used": 127, "limit": 500, "percentage": 25 }
    },
    "recentReports": [
      {
        "id": "1",
        "name": "Monthly SEO Audit",
        "createdAt": "2024-01-15",
        "status": "completed"
      }
    ],
    "seoInsights": [
      {
        "id": "1",
        "type": "issue",
        "title": "Missing Meta Descriptions",
        "severity": "warning"
      }
    ],
    "topKeywords": [
      {
        "id": "1",
        "keyword": "seo optimization tools",
        "volume": 12400,
        "difficulty": 45,
        "trend": "up"
      }
    ],
    "rankOverview": [
      {
        "id": "1",
        "keyword": "seo optimization tools",
        "currentRank": 4,
        "previousRank": 6,
        "url": "https://example.com/seo-tools"
      }
    ]
  }
}
```

#### Run New Audit
```
POST /audits/run
```

**Request Body:**
```json
{
  "targetUrl": "https://example.com",
  "crawlMode": "sitemap" | "full",
  "depth": 3
}
```

**Response (202):**
```json
{
  "success": true,
  "data": {
    "auditId": "uuid",
    "status": "processing",
    "estimatedTime": 300,
    "message": "Audit started successfully"
  }
}
```

---

### 2.2 SEO Insights Module

#### Get All Insights
```
GET /insights
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | Filter by type: `issue`, `opportunity`, `success` |
| severity | string | Filter by severity: `critical`, `warning`, `info` |
| page | number | Page number |
| limit | number | Items per page |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "insights": [
      {
        "id": "1",
        "type": "issue",
        "title": "Missing Meta Descriptions",
        "description": "23 pages are missing meta descriptions",
        "severity": "warning",
        "metric": "Pages Affected",
        "metricValue": "23",
        "pageUrl": "https://example.com/page",
        "createdAt": "2024-01-16T10:00:00Z"
      }
    ],
    "counts": {
      "critical": 2,
      "warning": 8,
      "info": 15,
      "totalIssues": 25,
      "totalOpportunities": 10,
      "totalSuccess": 5
    },
    "seoScore": 84,
    "scoreChange": 12
  }
}
```

#### Get Insights Trends
```
GET /insights/trends
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | number | 7 | Number of days |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "scoreTrend": [
      { "date": "2024-01-10", "score": 72 },
      { "date": "2024-01-11", "score": 75 },
      { "date": "2024-01-12", "score": 78 },
      { "date": "2024-01-13", "score": 82 },
      { "date": "2024-01-14", "score": 84 }
    ],
    "issuesTrend": [
      { "date": "2024-01-10", "count": 15 },
      { "date": "2024-01-11", "count": 12 },
      { "date": "2024-01-12", "count": 10 },
      { "date": "2024-01-13", "count": 8 },
      { "date": "2024-01-14", "count": 5 }
    ]
  }
}
```

#### Get Issue Categories
```
GET /insights/categories
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "categories": [
      { "name": "Meta Tags", "count": 23, "percentage": 45, "color": "#8b5cf6" },
      { "name": "Page Speed", "count": 12, "percentage": 25, "color": "#f59e0b" },
      { "name": "Broken Links", "count": 8, "percentage": 15, "color": "#ef4444" },
      { "name": "Mobile Optimization", "count": 5, "percentage": 10, "color": "#3b82f6" }
    ]
  }
}
```

#### Export Insights Report
```
POST /insights/export
```

**Request Body:**
```json
{
  "format": "pdf" | "csv",
  "filters": {
    "type": "issue",
    "severity": "critical"
  }
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "downloadUrl": "https://api.seolens.com/v1/insights/export/uuid",
    "expiresAt": "2024-01-16T12:00:00Z"
  }
}
```

#### Run Full Site Audit
```
POST /audits/full
```

**Request Body:**
```json
{
  "deepScan": true,
  "checkMobile": true,
  "checkPerformance": true
}
```

**Response (202):**
```json
{
  "success": true,
  "data": {
    "auditId": "uuid",
    "status": "processing",
    "estimatedTime": 600
  }
}
```

---

### 2.3 Keyword Analyzer Module

#### Get Keywords
```
GET /keywords
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search term |
| competition | string | Filter: `low`, `medium`, `high` |
| trend | string | Filter: `up`, `stable`, `down` |
| page | number | Page number |
| limit | number | Items per page (default: 20) |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "keywords": [
      {
        "id": "1",
        "keyword": "seo optimization tools",
        "volume": 12400,
        "difficulty": 45,
        "cpc": 2.50,
        "competition": "medium",
        "trend": "up",
        "suggestions": ["best seo tools", "seo optimization software"],
        "createdAt": "2024-01-16T10:00:00Z"
      }
    ],
    "stats": {
      "totalCount": 2847,
      "avgDifficulty": 42,
      "totalVolume": 1250000,
      "lowCompetitionCount": 45,
      "risingKeywords": 23
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 2847,
      "pages": 143
    }
  }
}
```

#### Get Keyword Trends
```
GET /keywords/trends
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "volumeTrend": [
      { "label": "Jan", "value": 12000, "color": "#3b82f6" },
      { "label": "Feb", "value": 15000, "color": "#8b5cf6" },
      { "label": "Mar", "value": 18000, "color": "#ec4899" }
    ],
    "distribution": [
      { "label": "Low", "value": 45, "color": "#10b981" },
      { "label": "Medium", "value": 35, "color": "#f59e0b" },
      { "label": "High", "value": 20, "color": "#ef4444" }
    ]
  }
}
```

#### Research Keywords
```
POST /keywords/research
```

**Request Body:**
```json
{
  "keyword": "seo tools",
  "location": "US",
  "language": "en"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "keyword": "best seo tools",
        "volume": 5400,
        "difficulty": 38,
        "cpc": 3.20,
        "competition": "medium"
      }
    ],
    "relatedKeywords": [
      "seo optimization tools",
      "free seo tools",
      "google seo tools"
    ],
    "questions": [
      "what are the best seo tools",
      "how to use seo tools"
    ]
  }
}
```

#### Add Keywords
```
POST /keywords
```

**Request Body:**
```json
{
  "keywords": ["seo tools", "keyword research"],
  "tags": ["priority", "main"]
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "added": 2,
    "duplicates": 0,
    "failed": 0,
    "keywords": [
      {
        "id": "uuid",
        "keyword": "seo tools",
        "status": "tracking"
      }
    ]
  }
}
```

#### Delete Keyword
```
DELETE /keywords/:id
```

**Response (200):**
```json
{
  "success": true,
  "message": "Keyword deleted successfully"
}
```

#### Export Keywords
```
GET /keywords/export
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | `csv`, `xlsx`, `pdf` |

**Response:** File download

---

### 2.4 Rank Tracker Module

#### Get Rankings
```
GET /rankings
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search term |
| dateRange | string | `7d`, `30d`, `90d` |
| page | number | Page number |
| limit | number | Items per page |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "rankings": [
      {
        "id": "1",
        "keyword": "seo optimization tools",
        "currentRank": 4,
        "previousRank": 6,
        "url": "https://example.com/seo-tools",
        "searchVolume": 12400,
        "lastUpdated": "2024-01-16",
        "change": 2
      }
    ],
    "stats": {
      "trackedCount": 45,
      "top10Count": 12,
      "top3Count": 3,
      "improvedCount": 8,
      "declinedCount": 5,
      "unchangedCount": 32
    },
    "trendData": [
      { "date": "2024-01-10", "avgPosition": 14.2 },
      { "date": "2024-01-11", "avgPosition": 13.8 }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

#### Get Ranking Distribution
```
GET /rankings/distribution
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "distribution": [
      { "label": "#1-3", "value": 8, "color": "#10b981" },
      { "label": "#4-10", "value": 15, "color": "#3b82f6" },
      { "label": "#11-20", "value": 12, "color": "#f59e0b" },
      { "label": "#20+", "value": 10, "color": "#6b7280" }
    ]
  }
}
```

#### Add Ranking Keywords
```
POST /rankings/keywords
```

**Request Body:**
```json
{
  "keywords": ["seo tools"],
  "urls": ["https://example.com/seo-tools"],
  "location": "US",
  "language": "en"
}
```

#### Get Improvements
```
GET /rankings/improvements
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "improvements": [
      {
        "id": "1",
        "keyword": "seo optimization tools",
        "currentRank": 4,
        "previousRank": 8,
        "change": 4,
        "url": "https://example.com/seo-tools"
      }
    ]
  }
}
```

#### Get Declines
```
GET /rankings/declines
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "declines": [
      {
        "id": "2",
        "keyword": "keyword research",
        "currentRank": 18,
        "previousRank": 15,
        "change": -3,
        "url": "https://example.com/keyword-research"
      }
    ]
  }
}
```

#### Export Rankings
```
GET /rankings/export
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | `csv`, `pdf` |
| dateRange | string | `7d`, `30d`, `90d` |

---

### 2.5 Competitors Module

#### Get Competitors
```
GET /competitors
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| search | string | Search by domain |
| page | number | Page number |
| limit | number | Items per page |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "competitors": [
      {
        "id": "1",
        "domain": "competitor1.com",
        "domainAuthority": 68,
        "backlinks": 45200,
        "organicKeywords": 28500,
        "organicTraffic": 125000,
        "overlapScore": 78,
        "addedAt": "2024-01-16T10:00:00Z"
      }
    ],
    "stats": {
      "avgDA": 64,
      "totalBacklinks": 174600,
      "highOverlapCount": 2
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 4,
      "pages": 1
    }
  }
}
```

#### Get Competitor Distribution
```
GET /competitors/distribution
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "daDistribution": [
      { "label": "40-50", "value": 3, "color": "#10b981" },
      { "label": "50-60", "value": 5, "color": "#3b82f6" },
      { "label": "60-70", "value": 4, "color": "#f59e0b" },
      { "label": "70+", "value": 2, "color": "#8b5cf6" }
    ],
    "overlapDistribution": [
      { "label": "High", "value": 3, "color": "#ef4444" },
      { "label": "Medium", "value": 6, "color": "#f59e0b" },
      { "label": "Low", "value": 5, "color": "#10b981" }
    ]
  }
}
```

#### Add Competitor
```
POST /competitors
```

**Request Body:**
```json
{
  "domain": "competitor.com"
}
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "domain": "competitor.com",
    "domainAuthority": 65,
    "backlinks": 45000,
    "organicKeywords": 28000,
    "organicTraffic": 120000,
    "overlapScore": 75
  }
}
```

#### Delete Competitor
```
DELETE /competitors/:id
```

**Response (200):**
```json
{
  "success": true,
  "message": "Competitor removed successfully"
}
```

#### Get Top By Authority
```
GET /competitors/top-by-authority
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "competitors": [
      { "id": "2", "domain": "competitor2.com", "domainAuthority": 72 },
      { "id": "1", "domain": "competitor1.com", "domainAuthority": 68 },
      { "id": "4", "domain": "competitor4.com", "domainAuthority": 61 }
    ]
  }
}
```

#### Get Top By Backlinks
```
GET /competitors/top-by-backlinks
```

#### Get Top By Overlap
```
GET /competitors/top-by-overlap
```

#### Export Competitors
```
GET /competitors/export
```

---

### 2.6 Reports Module

#### Get Reports
```
GET /reports
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | Filter by type |
| status | string | Filter by status |
| page | number | Page number |
| limit | number | Items per page |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": "1",
        "name": "Monthly SEO Audit - January 2024",
        "type": "seo-audit",
        "status": "completed",
        "createdAt": "2024-01-15",
        "size": "2.4 MB",
        "downloadUrl": "https://api.seolens.com/v1/reports/1/download"
      }
    ],
    "counts": {
      "total": 45,
      "completed": 42,
      "processing": 2,
      "failed": 1
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

#### Get Report Distribution
```
GET /reports/distribution
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "byType": [
      { "label": "SEO Audit", "value": 15, "color": "#3b82f6" },
      { "label": "Keywords", "value": 12, "color": "#8b5cf6" },
      { "label": "Rank", "value": 10, "color": "#10b981" },
      { "label": "Comp", "value": 8, "color": "#f59e0b" }
    ],
    "byMonth": [
      { "label": "Jan", "value": 4, "color": "#3b82f6" },
      { "label": "Feb", "value": 6, "color": "#8b5cf6" },
      { "label": "Mar", "value": 8, "color": "#10b981" }
    ]
  }
}
```

#### Generate Report
```
POST /reports
```

**Request Body:**
```json
{
  "type": "seo-audit",
  "name": "Q1 SEO Report",
  "filters": {
    "dateRange": "90d",
    "sites": ["site1", "site2"]
  }
}
```

**Response (202):**
```json
{
  "success": true,
  "data": {
    "reportId": "uuid",
    "status": "processing",
    "estimatedTime": 120
  }
}
```

#### Get Report Details
```
GET /reports/:id
```

#### Download Report
```
GET /reports/:id/download
```

**Response:** File download (PDF, CSV, etc.)

#### Delete Report
```
DELETE /reports/:id
```

#### Get Scheduled Reports
```
GET /reports/scheduled
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "scheduled": [
      {
        "id": "1",
        "name": "Weekly SEO Summary",
        "schedule": "Every Monday at 9:00 AM",
        "type": "seo-audit",
        "status": "active"
      }
    ]
  }
}
```

#### Schedule Report
```
POST /reports/scheduled
```

**Request Body:**
```json
{
  "name": "Monthly Report",
  "type": "seo-audit",
  "schedule": "0 9 1 * *",
  "recipients": ["user@example.com"]
}
```

---

### 2.7 User Settings Module

#### Get User Profile
```
GET /user/profile
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "john.doe@example.com",
      "name": "John Doe",
      "company": "Acme Corp",
      "website": "https://acme.com",
      "avatarUrl": "https://api.seolens.com/avatars/uuid.jpg",
      "role": "user",
      "createdAt": "2023-08-15T10:00:00Z"
    }
  }
}
```

#### Update Profile
```
PUT /user/profile
```

**Request Body:**
```json
{
  "name": "John Doe",
  "company": "Acme Corp",
  "website": "https://acme.com"
}
```

#### Upload Avatar
```
POST /user/avatar
```

**Content-Type:** `multipart/form-data`

**Request Body:**
- `image`: File (JPG, PNG, GIF, max 2MB)

**Response (200):**
```json
{
  "success": true,
  "data": {
    "avatarUrl": "https://api.seolens.com/avatars/uuid.jpg"
  }
}
```

#### Get User Settings
```
GET /user/settings
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "notifications": {
      "email": true,
      "weeklyReport": true,
      "rankChanges": true,
      "newOpportunities": false
    },
    "preferences": {
      "timezone": "America/New_York",
      "currency": "USD",
      "language": "en"
    }
  }
}
```

#### Update Settings
```
PUT /user/settings
```

**Request Body:**
```json
{
  "notifications": {
    "email": true,
    "weeklyReport": true,
    "rankChanges": true,
    "newOpportunities": false
  },
  "preferences": {
    "timezone": "America/New_York",
    "currency": "USD",
    "language": "en"
  }
}
```

#### Get Subscription
```
GET /user/subscription
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "subscription": {
      "id": "sub_12345",
      "plan": "professional",
      "status": "active",
      "price": 99,
      "billingCycle": "monthly",
      "nextBillingDate": "2024-02-15",
      "features": [
        "Unlimited sites",
        "10,000 keywords",
        "Priority support",
        "API access",
        "White-label reports",
        "Team collaboration"
      ],
      "limits": {
        "sites": 50,
        "keywords": 10000,
        "reports": 500,
        "apiCalls": 100000
      },
      "usage": {
        "sites": 12,
        "keywords": 2847,
        "reports": 127,
        "apiCalls": 45230
      }
    }
  }
}
```

#### Get Available Plans
```
GET /plans
```

#### Upgrade Subscription
```
POST /subscriptions/upgrade
```

**Request Body:**
```json
{
  "planId": "professional",
  "billingCycle": "yearly"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "checkoutUrl": "https://checkout.stripe.com/...",
    "sessionId": "cs_..."
  }
}
```

#### Get Payment Methods
```
GET /user/payment-methods
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "methods": [
      {
        "id": "pm_123",
        "type": "card",
        "last4": "4242",
        "expMonth": 12,
        "expYear": 2025,
        "brand": "visa",
        "isDefault": true
      }
    ]
  }
}
```

#### Add Payment Method
```
POST /user/payment-methods
```

**Request Body:**
```json
{
  "token": "stripe_token"
}
```

#### Get Billing History
```
GET /user/billing-history
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "invoices": [
      {
        "id": "inv_123",
        "date": "2024-01-15",
        "amount": 99.00,
        "status": "paid",
        "description": "Professional Plan - Monthly",
        "downloadUrl": "https://api.seolens.com/v1/invoices/inv_123/download"
      }
    ]
  }
}
```

#### Change Password
```
PUT /user/password
```

**Request Body:**
```json
{
  "currentPassword": "string",
  "newPassword": "string"
}
```

#### Enable 2FA
```
POST /user/2fa/enable
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "qrCodeUrl": "data:image/png;base64,...",
    "backupCodes": ["code1", "code2", "..."]
  }
}
```

#### Delete Account
```
DELETE /user
```

**Request Body:**
```json
{
  "password": "string",
  "reason": "optional reason"
}
```

---

## 3. Admin Dashboard APIs

### 3.1 Admin Overview

#### Get Admin Overview
```
GET /admin/overview
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "totalUsers": 290,
    "activeUsers": 248,
    "activeSubscriptions": 162,
    "monthlyRevenue": 13850,
    "activeRate": "92%",
    "recentSignups": [
      {
        "id": "1",
        "name": "John Doe",
        "email": "john@example.com",
        "plan": "Professional"
      }
    ],
    "planDistribution": [
      { "plan": "Free", "count": 25, "percentage": 9 },
      { "plan": "Starter", "count": 45, "percentage": 16 },
      { "plan": "Professional", "count": 80, "percentage": 58 },
      { "plan": "Enterprise", "count": 12, "percentage": 17 }
    ],
    "systemStatus": {
      "api": "operational",
      "database": "healthy",
      "queue": "running"
    }
  }
}
```

#### Get Revenue Chart
```
GET /admin/revenue
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| days | number | 7 | Number of days |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "revenueData": [
      { "label": "Mon", "value": 5234, "color": "#10b981" },
      { "label": "Tue", "value": 6123, "color": "#3b82f6" }
    ]
  }
}
```

---

### 3.2 Analytics Module

#### Get Platform Analytics
```
GET /admin/analytics
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| dateRange | string | 7d | `7d`, `30d`, `90d` |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "avgDailyActive": 512,
    "totalScans": 12340,
    "totalReports": 2340,
    "totalRevenue": 45230,
    "userActivityData": [
      { "label": "Mon", "value": 452, "color": "#3b82f6" }
    ],
    "revenueData": [
      { "label": "Mon", "value": 5234, "color": "#10b981" }
    ],
    "newUsersData": [
      { "label": "Mon", "value": 89, "color": "#f59e0b" }
    ],
    "scansData": [
      { "label": "Mon", "value": 1234, "color": "#8b5cf6" }
    ],
    "retentionRate": 75
  }
}
```

#### Export Analytics
```
GET /admin/analytics/export
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | `csv`, `xlsx` |
| dateRange | string | Date range |

---

### 3.3 Users Management Module

#### Get All Users
```
GET /admin/users
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter: `active`, `inactive`, `suspended` |
| plan | string | Filter by plan |
| search | string | Search by name/email |
| page | number | Page number |
| limit | number | Items per page |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "users": [
      {
        "id": "1",
        "email": "john.doe@example.com",
        "name": "John Doe",
        "company": "Acme Corp",
        "status": "active",
        "role": "user",
        "plan": "Professional",
        "joinedAt": "2023-08-15",
        "lastActive": "2024-01-16",
        "sitesCount": 12,
        "keywordsCount": 2847
      }
    ],
    "stats": {
      "totalCount": 290,
      "activeCount": 248,
      "totalSites": 1240,
      "totalKeywords": 125000
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 290,
      "pages": 15
    }
  }
}
```

#### Get User Distribution
```
GET /admin/users/distribution
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "byPlan": [
      { "label": "Free", "value": 25, "color": "#6b7280" },
      { "label": "Starter", "value": 45, "color": "#3b82f6" },
      { "label": "Pro", "value": 80, "color": "#8b5cf6" },
      { "label": "Ent", "value": 12, "color": "#f59e0b" }
    ],
    "growthTrend": [
      { "label": "Jan", "value": 120, "color": "#3b82f6" },
      { "label": "Feb", "value": 145, "color": "#8b5cf6" }
    ]
  }
}
```

#### Create User
```
POST /admin/users
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "name": "New User",
  "plan": "professional",
  "role": "user"
}
```

#### Get User Details
```
GET /admin/users/:id
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "1",
      "email": "john.doe@example.com",
      "name": "John Doe",
      "company": "Acme Corp",
      "status": "active",
      "role": "user",
      "plan": "Professional",
      "joinedAt": "2023-08-15",
      "lastActive": "2024-01-16",
      "sitesCount": 12,
      "keywordsCount": 2847
    }
  }
}
```

#### Update User
```
PUT /admin/users/:id
```

**Request Body:**
```json
{
  "name": "Updated Name",
  "plan": "enterprise",
  "status": "active"
}
```

#### Suspend User
```
POST /admin/users/:id/suspend
```

**Request Body:**
```json
{
  "reason": "Violation of terms"
}
```

#### Activate User
```
POST /admin/users/:id/activate
```

#### Delete User
```
DELETE /admin/users/:id
```

#### Send Email to User
```
POST /admin/users/:id/email
```

**Request Body:**
```json
{
  "subject": "Account Update",
  "message": "Your account has been upgraded..."
}
```

---

### 3.4 Subscriptions Module

#### Get All Subscriptions
```
GET /admin/subscriptions
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| status | string | Filter: `active`, `inactive`, `past_due`, `cancelled` |
| plan | string | Filter by plan |
| search | string | Search by user name/email |
| page | number | Page number |
| limit | number | Items per page |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "subscriptions": [
      {
        "id": "sub_12345",
        "userId": "1",
        "userName": "John Doe",
        "userEmail": "john.doe@example.com",
        "plan": "Professional",
        "status": "active",
        "amount": 99,
        "billingCycle": "monthly",
        "startDate": "2023-08-15",
        "nextBillingDate": "2024-02-15"
      }
    ],
    "stats": {
      "totalMRR": 13850,
      "activeCount": 162,
      "pastDueCount": 3,
      "avgRevenuePerUser": 85
    },
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 162,
      "pages": 9
    }
  }
}
```

#### Get Revenue Data
```
GET /admin/subscriptions/revenue
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "byPlan": [
      { "label": "Free", "value": 0, "color": "#6b7280" },
      { "label": "Starter", "value": 2250, "color": "#3b82f6" },
      { "label": "Pro", "value": 8000, "color": "#8b5cf6" },
      { "label": "Ent", "value": 3600, "color": "#f59e0b" }
    ],
    "mrrTrend": [
      { "label": "Jan", "value": 8500, "color": "#3b82f6" },
      { "label": "Feb", "value": 9200, "color": "#8b5cf6" }
    ]
  }
}
```

#### Get Subscription Details
```
GET /admin/subscriptions/:id
```

#### Renew Subscription
```
POST /admin/subscriptions/:id/renew
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "newExpiryDate": "2024-03-15",
    "message": "Subscription renewed successfully"
  }
}
```

#### Cancel Subscription
```
POST /admin/subscriptions/:id/cancel
```

**Request Body:**
```json
{
  "reason": "User request",
  "immediate": false
}
```

#### Export Subscriptions
```
GET /admin/subscriptions/export
```

#### Get Upcoming Renewals
```
GET /admin/subscriptions/upcoming-renewals
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "renewals": [
      {
        "id": "sub_12345",
        "userName": "John Doe",
        "plan": "Professional",
        "amount": 99,
        "nextBillingDate": "2024-02-15"
      }
    ]
  }
}
```

---

### 3.5 Admin Reports Module

#### Get System Reports
```
GET /admin/reports
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | Filter by type: `system`, `user`, `revenue` |
| status | string | Filter by status |
| page | number | Page number |
| limit | number | Items per page |

**Response (200):**
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "id": "1",
        "name": "System Health Report",
        "type": "system",
        "status": "completed",
        "createdAt": "2024-01-16",
        "size": "1.2 MB"
      }
    ],
    "counts": {
      "total": 56,
      "completed": 45,
      "processing": 8,
      "failed": 3
    }
  }
}
```

#### Get Reports Distribution
```
GET /admin/reports/distribution
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "byStatus": [
      { "label": "Done", "value": 45, "color": "#10b981" },
      { "label": "Proc", "value": 8, "color": "#f59e0b" },
      { "label": "Fail", "value": 3, "color": "#ef4444" }
    ],
    "byType": [
      { "label": "SEO", "value": 15, "color": "#3b82f6" },
      { "label": "Key", "value": 12, "color": "#8b5cf6" }
    ]
  }
}
```

#### Generate System Report
```
POST /admin/reports
```

**Request Body:**
```json
{
  "type": "system",
  "name": "Weekly System Health",
  "parameters": {
    "includeLogs": true,
    "dateRange": "7d"
  }
}
```

---

### 3.6 Admin Settings Module

#### Get Platform Settings
```
GET /admin/settings
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "platform": {
      "name": "SEO Lens",
      "supportEmail": "support@seolens.com",
      "maintenanceMode": false,
      "userRegistration": true,
      "emailVerification": true
    },
    "rateLimits": {
      "apiCallsPerHour": 1000,
      "scansPerDay": 100,
      "reportsPerDay": 50
    }
  }
}
```

#### Update Platform Settings
```
PUT /admin/settings
```

**Request Body:**
```json
{
  "platform": {
    "name": "SEO Lens",
    "supportEmail": "support@seolens.com",
    "maintenanceMode": false
  },
  "rateLimits": {
    "apiCallsPerHour": 1000
  }
}
```

#### Get API Keys
```
GET /admin/api-keys
```

#### Generate API Key
```
POST /admin/api-keys
```

**Request Body:**
```json
{
  "name": "Production Key",
  "permissions": ["read", "write"]
}
```

#### Revoke API Key
```
DELETE /admin/api-keys/:id
```

#### Get Integrations
```
GET /admin/integrations
```

#### Update Integration
```
PUT /admin/integrations/:id
```

#### Get Database Status
```
GET /admin/database/status
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "PostgreSQL 14.5",
    "lastBackup": "2024-01-16T03:00:00Z",
    "backupFrequency": "daily"
  }
}
```

#### Run Database Backup
```
POST /admin/database/backup
```

---

## 4. Public Website APIs

### 4.1 Analyze Site SEO

```
POST /tools/analyze-site
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "crawlMode": "SITEMAP_ONLY" | "FULL_CRAWL",
  "maxPages": 100
}
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "crawlId": "uuid",
    "baseUrlChecks": {
      "baseUrl": "https://example.com",
      "isSecure": true,
      "redirects": []
    },
    "seoScore": 78,
    "pageCount": 45,
    "issues": {
      "critical": [
        {
          "type": "missing_title",
          "page": "/page1",
          "description": "Page is missing title tag"
        }
      ],
      "warnings": [
        {
          "type": "long_title",
          "page": "/page2",
          "description": "Title tag exceeds 60 characters"
        }
      ],
      "passed": [
        {
          "type": "has_canonical",
          "page": "/page3"
        }
      ]
    },
    "performance": {
      "loadTime": 2.3,
      "pageSize": 1240000
    },
    "mobileFriendly": true,
    "pages": [
      {
        "url": "https://example.com/page1",
        "title": "Page Title",
        "metaDescription": "Description here",
        "statusCode": 200,
        "loadTime": 1.2,
        "wordCount": 1200,
        "links": {
          "internal": 15,
          "external": 5
        }
      }
    ]
  }
}
```

#### Check Crawl Status
```
GET /tools/crawl-status/:crawlId
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "crawlId": "uuid",
    "status": "processing",
    "progress": 65,
    "pagesScanned": 29,
    "totalPages": 45,
    "currentUrl": "https://example.com/page30"
  }
}
```

---

### 4.2 Analyze Keyword Rank

```
POST /tools/analyze-rank
```

**Request Body:**
```json
{
  "url": "https://example.com",
  "keywords": ["seo tools", "keyword research"],
  "location": "US",
  "language": "en"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "keyword": "seo tools",
      "rank": 5,
      "searchResults": [
        {
          "position": 1,
          "url": "https://competitor1.com",
          "title": "Best SEO Tools 2024"
        },
        {
          "position": 2,
          "url": "https://competitor2.com",
          "title": "Top SEO Software"
        }
      ],
      "targetPosition": 5,
      "volume": 12400,
      "difficulty": 45
    }
  ]
}
```

---

### 4.3 Suggest Keywords

```
POST /tools/suggest-keywords
```

**Request Body:**
```json
{
  "keywords": ["seo"],
  "location": "US",
  "language": "en"
}
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "keyword": "seo tools",
      "searchVolume": 12400,
      "difficulty": 45,
      "cpc": 2.50,
      "competition": "medium",
      "suggestions": [
        "best seo tools",
        "free seo tools"
      ],
      "relatedKeywords": [
        "seo software",
        "seo optimization"
      ],
      "trends": [
        { "month": "Jan", "volume": 11000 },
        { "month": "Feb", "volume": 12500 }
      ]
    }
  ]
}
```

---

## 5. Common Response Patterns

### 5.1 Success Response

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-16T10:00:00Z",
    "requestId": "req_123"
  }
}
```

### 5.2 Error Response

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input provided",
    "details": {
      "field": "email",
      "issue": "Email is required"
    }
  },
  "meta": {
    "timestamp": "2024-01-16T10:00:00Z",
    "requestId": "req_123"
  }
}
```

**Error Codes:**
| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid input data |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

### 5.3 Pagination Response

```json
{
  "success": true,
  "data": [ ... ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 100,
    "pages": 5,
    "hasNext": true,
    "hasPrev": false
  }
}
```

---

## Summary

| Category | Endpoint Count |
|----------|---------------|
| Authentication APIs | 8 |
| User Dashboard APIs | 52 |
| Admin Dashboard APIs | 32 |
| Public Website APIs | 5 |
| **TOTAL** | **97** |

---

## Rate Limits

| Endpoint Type | Limit |
|--------------|-------|
| Authentication | 10 requests/minute |
| Public Tools | 5 requests/hour (unauthenticated) |
| User Dashboard | 1000 requests/hour |
| Admin Dashboard | 2000 requests/hour |

---

## Webhooks (Future)

The following webhook events may be supported:

- `report.completed` - Report generation completed
- `ranking.changed` - Keyword ranking changed
- `subscription.updated` - Subscription status changed
- `user.created` - New user registered
- `audit.completed` - Site audit completed

---

*Document Version: 1.0*
*Last Updated: 2024-01-16*
