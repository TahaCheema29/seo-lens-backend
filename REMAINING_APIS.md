# Remaining APIs to Implement

This document lists all APIs that are NOT yet implemented, excluding:
- Competitive Analysis APIs (Section 2.5)
- Subscription APIs (Section 2.7 subscription-related, Section 3.4)
- GitHub Integration APIs

---

## Already Implemented ✅

### Authentication APIs
- ✅ `POST /auth/register` - User registration
- ✅ `POST /auth/login` - User login
- ✅ `POST /auth/logout` - User logout
- ✅ `GET /auth/me` - Get current user
- ✅ `PUT /auth/me` - Update current user
- ✅ `DELETE /auth/me` - Delete current user

### Admin Authentication APIs
- ✅ `POST /admin/auth/register` - Admin registration
- ✅ `POST /admin/auth/login` - Admin login
- ✅ `POST /admin/auth/logout` - Admin logout
- ✅ `GET /admin/auth/me` - Get current admin
- ✅ `GET /admin/auth/admins` - Get all admins

### Admin User Management APIs
- ✅ `GET /admin/users` - Get all users
- ✅ `GET /admin/users/:id` - Get user by ID
- ✅ `PUT /admin/users/:id/activate` - Activate user
- ✅ `PUT /admin/users/:id/deactivate` - Deactivate user
- ✅ `PUT /admin/users/:id/role/:role` - Update user role
- ✅ `DELETE /admin/users/:id` - Delete user

### Keyword Rank APIs
- ✅ `POST /keyword-rank/analyze` - Analyze keyword ranking
- ✅ `GET /keyword-rank/results` - Get user's keyword rank results
- ✅ `GET /keyword-rank/results/:id` - Get specific result
- ✅ `DELETE /keyword-rank/results/:id` - Delete result

### Keyword Suggestion APIs
- ✅ `POST /keyword-suggestion/analyze` - Analyze keyword suggestions
- ✅ `GET /keyword-suggestion/results` - Get user's suggestions
- ✅ `GET /keyword-suggestion/results/:id` - Get specific suggestion
- ✅ `DELETE /keyword-suggestion/results/:id` - Delete suggestion

### SEO Insight APIs
- ✅ `POST /seo-insight/analyze` - Analyze site SEO
- ✅ `GET /seo-insight/results` - Get user's SEO insights
- ✅ `GET /seo-insight/results/:id` - Get specific insight
- ✅ `DELETE /seo-insight/results/:id` - Delete insight

---

## Remaining APIs to Implement ❌

### 1. Authentication APIs (4 endpoints)

#### 1.1 Refresh Token
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
  "status": "success",
  "message": "Token refreshed successfully",
  "data": {
    "token": "new_jwt_access_token",
    "refreshToken": "new_jwt_refresh_token"
  }
}
```

#### 1.2 Forgot Password
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
  "status": "success",
  "message": "Password reset email sent"
}
```

#### 1.3 Reset Password
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

**Response (200):**
```json
{
  "status": "success",
  "message": "Password reset successfully"
}
```

#### 1.4 Verify Email
```
POST /auth/verify-email
```

**Request Body:**
```json
{
  "token": "verification_token"
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Email verified successfully"
}
```

---

### 2. Dashboard APIs (3 endpoints)

#### 2.1 Get Dashboard Overview
```
GET /dashboard/overview
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Dashboard overview retrieved successfully",
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
      { "label": "Tue", "value": 78, "color": "#10b981" }
    ],
    "planUsage": {
      "sites": { "used": 12, "limit": 50, "percentage": 24 },
      "keywords": { "used": 2847, "limit": 10000, "percentage": 28 },
      "reports": { "used": 127, "limit": 500, "percentage": 25 }
    },
    "recentReports": [...],
    "seoInsights": [...],
    "topKeywords": [...],
    "rankOverview": [...]
  }
}
```

#### 2.2 Run New Audit
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
  "status": "success",
  "message": "Audit started successfully",
  "data": {
    "auditId": "uuid",
    "status": "processing",
    "estimatedTime": 300
  }
}
```

#### 2.3 Run Full Site Audit
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
  "status": "success",
  "message": "Full audit started successfully",
  "data": {
    "auditId": "uuid",
    "status": "processing",
    "estimatedTime": 600
  }
}
```

---

### 3. SEO Insights Module (4 endpoints)

#### 3.1 Get All Insights
```
GET /insights
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | Filter: `issue`, `opportunity`, `success` |
| severity | string | Filter: `critical`, `warning`, `info` |
| page | number | Page number |
| limit | number | Items per page |

**Response (200):**
```json
{
  "status": "success",
  "message": "Insights retrieved successfully",
  "data": {
    "insights": [...],
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

#### 3.2 Get Insights Trends
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
  "status": "success",
  "message": "Insights trends retrieved successfully",
  "data": {
    "scoreTrend": [...],
    "issuesTrend": [...]
  }
}
```

#### 3.3 Get Issue Categories
```
GET /insights/categories
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Issue categories retrieved successfully",
  "data": {
    "categories": [
      { "name": "Meta Tags", "count": 23, "percentage": 45, "color": "#8b5cf6" },
      { "name": "Page Speed", "count": 12, "percentage": 25, "color": "#f59e0b" }
    ]
  }
}
```

#### 3.4 Export Insights Report
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
  "status": "success",
  "message": "Export generated successfully",
  "data": {
    "downloadUrl": "https://api.seolens.com/v1/insights/export/uuid",
    "expiresAt": "2024-01-16T12:00:00Z"
  }
}
```

---

### 4. Keyword Analyzer Module (6 endpoints)

#### 4.1 Get Keywords
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
| limit | number | Items per page |

**Response (200):**
```json
{
  "status": "success",
  "message": "Keywords retrieved successfully",
  "data": {
    "keywords": [...],
    "stats": {
      "totalCount": 2847,
      "avgDifficulty": 42,
      "totalVolume": 1250000,
      "lowCompetitionCount": 45,
      "risingKeywords": 23
    },
    "pagination": { "page": 1, "limit": 20, "total": 2847, "pages": 143 }
  }
}
```

#### 4.2 Get Keyword Trends
```
GET /keywords/trends
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Keyword trends retrieved successfully",
  "data": {
    "volumeTrend": [...],
    "distribution": [...]
  }
}
```

#### 4.3 Research Keywords
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
  "status": "success",
  "message": "Keyword research completed successfully",
  "data": {
    "suggestions": [...],
    "relatedKeywords": [...],
    "questions": [...]
  }
}
```

#### 4.4 Add Keywords
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
  "status": "success",
  "message": "Keywords added successfully",
  "data": {
    "added": 2,
    "duplicates": 0,
    "failed": 0,
    "keywords": [...]
  }
}
```

#### 4.5 Delete Keyword
```
DELETE /keywords/:id
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Keyword deleted successfully"
}
```

#### 4.6 Export Keywords
```
GET /keywords/export
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | `csv`, `xlsx`, `pdf` |

**Response:** File download

---

### 5. Rank Tracker Module (6 endpoints)

#### 5.1 Get Rankings
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
  "status": "success",
  "message": "Rankings retrieved successfully",
  "data": {
    "rankings": [...],
    "stats": {
      "trackedCount": 45,
      "top10Count": 12,
      "top3Count": 3,
      "improvedCount": 8,
      "declinedCount": 5,
      "unchangedCount": 32
    },
    "trendData": [...],
    "pagination": {...}
  }
}
```

#### 5.2 Get Ranking Distribution
```
GET /rankings/distribution
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Ranking distribution retrieved successfully",
  "data": {
    "distribution": [
      { "label": "#1-3", "value": 8, "color": "#10b981" },
      { "label": "#4-10", "value": 15, "color": "#3b82f6" }
    ]
  }
}
```

#### 5.3 Add Ranking Keywords
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

**Response (201):**
```json
{
  "status": "success",
  "message": "Keywords added for tracking",
  "data": {...}
}
```

#### 5.4 Get Improvements
```
GET /rankings/improvements
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Rank improvements retrieved successfully",
  "data": {
    "improvements": [...]
  }
}
```

#### 5.5 Get Declines
```
GET /rankings/declines
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Rank declines retrieved successfully",
  "data": {
    "declines": [...]
  }
}
```

#### 5.6 Export Rankings
```
GET /rankings/export
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | `csv`, `pdf` |
| dateRange | string | `7d`, `30d`, `90d` |

**Response:** File download

---

### 6. Reports Module (8 endpoints)

#### 6.1 Get Reports
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
  "status": "success",
  "message": "Reports retrieved successfully",
  "data": {
    "reports": [...],
    "counts": {
      "total": 45,
      "completed": 42,
      "processing": 2,
      "failed": 1
    },
    "pagination": {...}
  }
}
```

#### 6.2 Get Report Distribution
```
GET /reports/distribution
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Report distribution retrieved successfully",
  "data": {
    "byType": [...],
    "byMonth": [...]
  }
}
```

#### 6.3 Generate Report
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
  "status": "success",
  "message": "Report generation started",
  "data": {
    "reportId": "uuid",
    "status": "processing",
    "estimatedTime": 120
  }
}
```

#### 6.4 Get Report Details
```
GET /reports/:id
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Report retrieved successfully",
  "data": {
    "id": "uuid",
    "name": "Monthly SEO Audit",
    "type": "seo-audit",
    "status": "completed",
    "createdAt": "2024-01-15",
    "downloadUrl": "..."
  }
}
```

#### 6.5 Download Report
```
GET /reports/:id/download
```

**Response:** File download (PDF, CSV, etc.)

#### 6.6 Delete Report
```
DELETE /reports/:id
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Report deleted successfully"
}
```

#### 6.7 Get Scheduled Reports
```
GET /reports/scheduled
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Scheduled reports retrieved successfully",
  "data": {
    "scheduled": [...]
  }
}
```

#### 6.8 Schedule Report
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

**Response (201):**
```json
{
  "status": "success",
  "message": "Report scheduled successfully",
  "data": {...}
}
```

---

### 7. User Settings Module (8 endpoints)

#### 7.1 Get User Profile
```
GET /user/profile
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Profile retrieved successfully",
  "data": {
    "user": {
      "id": "uuid",
      "email": "john.doe@example.com",
      "name": "John Doe",
      "company": "Acme Corp",
      "website": "https://acme.com",
      "avatarUrl": "...",
      "role": "user",
      "createdAt": "2023-08-15T10:00:00Z"
    }
  }
}
```

#### 7.2 Update Profile
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

**Response (200):**
```json
{
  "status": "success",
  "message": "Profile updated successfully",
  "data": {...}
}
```

#### 7.3 Upload Avatar
```
POST /user/avatar
```

**Content-Type:** `multipart/form-data`

**Request Body:**
- `image`: File (JPG, PNG, GIF, max 2MB)

**Response (200):**
```json
{
  "status": "success",
  "message": "Avatar uploaded successfully",
  "data": {
    "avatarUrl": "https://api.seolens.com/avatars/uuid.jpg"
  }
}
```

#### 7.4 Get User Settings
```
GET /user/settings
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Settings retrieved successfully",
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

#### 7.5 Update Settings
```
PUT /user/settings
```

**Request Body:**
```json
{
  "notifications": {
    "email": true,
    "weeklyReport": true
  },
  "preferences": {
    "timezone": "America/New_York"
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Settings updated successfully",
  "data": {...}
}
```

#### 7.6 Change Password
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

**Response (200):**
```json
{
  "status": "success",
  "message": "Password changed successfully"
}
```

#### 7.7 Enable 2FA
```
POST /user/2fa/enable
```

**Response (200):**
```json
{
  "status": "success",
  "message": "2FA enabled successfully",
  "data": {
    "qrCodeUrl": "data:image/png;base64,...",
    "backupCodes": ["code1", "code2", "..."]
  }
}
```

#### 7.8 Delete Account
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

**Response (200):**
```json
{
  "status": "success",
  "message": "Account deleted successfully"
}
```

---

### 8. Admin Overview APIs (2 endpoints)

#### 8.1 Get Admin Overview
```
GET /admin/overview
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Admin overview retrieved successfully",
  "data": {
    "totalUsers": 290,
    "activeUsers": 248,
    "activeSubscriptions": 162,
    "monthlyRevenue": 13850,
    "activeRate": "92%",
    "recentSignups": [...],
    "planDistribution": [...],
    "systemStatus": {...}
  }
}
```

#### 8.2 Get Revenue Chart
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
  "status": "success",
  "message": "Revenue data retrieved successfully",
  "data": {
    "revenueData": [...]
  }
}
```

---

### 9. Admin Analytics Module (2 endpoints)

#### 9.1 Get Platform Analytics
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
  "status": "success",
  "message": "Analytics retrieved successfully",
  "data": {
    "avgDailyActive": 512,
    "totalScans": 12340,
    "totalReports": 2340,
    "totalRevenue": 45230,
    "userActivityData": [...],
    "revenueData": [...],
    "newUsersData": [...],
    "scansData": [...],
    "retentionRate": 75
  }
}
```

#### 9.2 Export Analytics
```
GET /admin/analytics/export
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| format | string | `csv`, `xlsx` |
| dateRange | string | Date range |

**Response:** File download

---

### 10. Admin Reports Module (3 endpoints)

#### 10.1 Get System Reports
```
GET /admin/reports
```

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| type | string | Filter: `system`, `user`, `revenue` |
| status | string | Filter by status |
| page | number | Page number |
| limit | number | Items per page |

**Response (200):**
```json
{
  "status": "success",
  "message": "System reports retrieved successfully",
  "data": {
    "reports": [...],
    "counts": {
      "total": 56,
      "completed": 45,
      "processing": 8,
      "failed": 3
    }
  }
}
```

#### 10.2 Get Reports Distribution
```
GET /admin/reports/distribution
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Reports distribution retrieved successfully",
  "data": {
    "byStatus": [...],
    "byType": [...]
  }
}
```

#### 10.3 Generate System Report
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

**Response (202):**
```json
{
  "status": "success",
  "message": "Report generation started",
  "data": {
    "reportId": "uuid",
    "status": "processing",
    "estimatedTime": 120
  }
}
```

---

### 11. Admin Settings Module (9 endpoints)

#### 11.1 Get Platform Settings
```
GET /admin/settings
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Settings retrieved successfully",
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

#### 11.2 Update Platform Settings
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

**Response (200):**
```json
{
  "status": "success",
  "message": "Settings updated successfully",
  "data": {...}
}
```

#### 11.3 Get API Keys
```
GET /admin/api-keys
```

**Response (200):**
```json
{
  "status": "success",
  "message": "API keys retrieved successfully",
  "data": {
    "apiKeys": [...]
  }
}
```

#### 11.4 Generate API Key
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

**Response (201):**
```json
{
  "status": "success",
  "message": "API key generated successfully",
  "data": {
    "id": "uuid",
    "name": "Production Key",
    "key": "sk_live_...",
    "permissions": ["read", "write"],
    "createdAt": "2024-01-16T10:00:00Z"
  }
}
```

#### 11.5 Revoke API Key
```
DELETE /admin/api-keys/:id
```

**Response (200):**
```json
{
  "status": "success",
  "message": "API key revoked successfully"
}
```

#### 11.6 Get Integrations
```
GET /admin/integrations
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Integrations retrieved successfully",
  "data": {
    "integrations": [...]
  }
}
```

#### 11.7 Update Integration
```
PUT /admin/integrations/:id
```

**Request Body:**
```json
{
  "enabled": true,
  "config": {
    "apiKey": "...",
    "webhookUrl": "..."
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Integration updated successfully",
  "data": {...}
}
```

#### 11.8 Get Database Status
```
GET /admin/database/status
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Database status retrieved successfully",
  "data": {
    "status": "healthy",
    "version": "PostgreSQL 14.5",
    "lastBackup": "2024-01-16T03:00:00Z",
    "backupFrequency": "daily"
  }
}
```

#### 11.9 Run Database Backup
```
POST /admin/database/backup
```

**Response (202):**
```json
{
  "status": "success",
  "message": "Database backup started",
  "data": {
    "backupId": "uuid",
    "status": "processing",
    "estimatedTime": 300
  }
}
```

---

## Summary

| Category | Endpoints to Implement |
|----------|----------------------|
| Authentication APIs | 4 |
| Dashboard APIs | 3 |
| SEO Insights Module | 4 |
| Keyword Analyzer Module | 6 |
| Rank Tracker Module | 6 |
| Reports Module | 8 |
| User Settings Module | 8 |
| Admin Overview APIs | 2 |
| Admin Analytics Module | 2 |
| Admin Reports Module | 3 |
| Admin Settings Module | 9 |
| **TOTAL** | **55** |

---

## Implementation Priority

### High Priority (Core Functionality)
1. Authentication (refresh token, password reset)
2. Dashboard Overview
3. User Settings (profile, settings, password)
4. Reports Module

### Medium Priority (Features)
5. SEO Insights Module
6. Keyword Analyzer Module
7. Rank Tracker Module
8. Admin Settings Module

### Low Priority (Admin/Analytics)
9. Admin Overview APIs
10. Admin Analytics Module
11. Admin Reports Module