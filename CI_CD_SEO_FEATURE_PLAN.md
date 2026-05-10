# CI/CD SEO Auto-Analysis Feature Plan

## Overview
Auto-generate SEO reports when users create Pull Requests or merge code to their main branch.

---

## Is It Possible? 

**✅ YES - Absolutely Possible!**

This feature can be implemented using a hybrid approach combining webhooks and CI/CD integrations.

---

## Implementation Approaches

### Approach 1: GitHub/GitLab Webhooks ⭐ (Recommended Primary)

**How it works:**
1. User configures webhook in their repo settings (or we configure it via API if they auth)
2. GitHub/GitLab sends POST request to our endpoint on PR/merge events
3. Backend receives payload, extracts website URL
4. Triggers SEO analysis asynchronously
5. Posts results back as PR comment or stores for viewing

**Pros:**
- Real-time triggers
- No code changes needed in user's repo
- Can post results directly to PR

**Cons:**
- Requires webhook configuration (unless using GitHub App)
- Need to handle webhook security (signature verification)

---

### Approach 2: GitHub Actions / GitLab CI ⭐ (Recommended Complementary)

**How it works:**
1. User adds workflow file (`.github/workflows/seo-lens.yml`) to their repo
2. On PR/merge, workflow runs and calls our API
3. API analyzes and returns results
4. Results posted as PR comment or check status

**Pros:**
- Easy to set up (just copy workflow file)
- Works with just an API key
- No webhook configuration needed
- Can see analysis in Action logs

**Cons:**
- Requires adding file to repo
- Slightly slower (Action startup time)

---

### Approach 3: GitHub App (Advanced, Full Integration)

**How it works:**
1. User installs "SEO Lens" GitHub App on their repos
2. App has permissions to read repos and post comments
3. App subscribes to PR/merge events automatically
4. Full control over UI/UX within GitHub

**Pros:**
- Best UX - automatic webhook setup
- Can show checks in PR interface
- Marketplace discoverability

**Cons:**
- More complex to develop
- Requires GitHub App registration
- Overkill for initial implementation

---

### Approach 4: Browser Extension + Manual Trigger

**Status:** ❌ Not recommended for this use case (not truly automated)

---

### Approach 5: Email Notifications ⭐⭐ (BEST - No Auth Required!)

**How it works:**
1. User triggers analysis via GitHub Action OR webhook
2. Analysis runs asynchronously
3. **Report is emailed to user** instead of posted as PR comment
4. Email contains summary + link to full report

**Pros:**
- ✅ **No GitHub OAuth required!**
- ✅ **Works immediately** with just API key
- ✅ **User gets notified** in their inbox
- ✅ **Can attach PDF** of full report
- ✅ **Works with both** GitHub Actions and webhooks
- ✅ **Privacy-friendly** - no GitHub permissions needed

**Cons:**
- ❌ Not visible directly in GitHub PR (but email link takes them there)
- ❌ Could end up in spam folder

**Workflow Example:**
```yaml
# GitHub Actions
- uses: seo-lens/action@v1
  with:
    api-key: ${{ secrets.SEO_LENS_API_KEY }}
    email: ${{ secrets.SEO_LENS_EMAIL }}  # or we use account email
```

---

## 🏆 Recommended Strategy: Hybrid Approach

| Component | Approach | Purpose |
|-----------|----------|---------|
| **Primary** | Webhooks | Real-time triggers from GitHub/GitLab |
| **Secondary** | GitHub Actions | Fallback, works without webhook setup |
| **Delivery** | **Email** ⭐ | No auth required, works immediately |
| **Optional** | PR Comments | For users who connect GitHub (enhanced UX) |

---

## Do Users Need to Connect Their GitHub/GitLab Account?

### Short Answer: **It depends on the approach**

| Approach | Account Connection Required? | Notes |
|----------|------------------------------|-------|
| **GitHub Actions** | ❌ No | Only needs an API key from our platform |
| **Manual Webhooks** | ❌ No | User manually configures webhook in repo settings |
| **GitHub App** | ✅ Yes | Must install app, requires authentication |
| **Auto Webhook Setup** | ✅ Yes | We need OAuth to configure webhooks via API |
| **PR Comments** | ✅ Yes | Need GitHub token to post comments |
| **Email Reports** | ❌ No | Just need user's email (from account or config) |

### Detailed Breakdown:

#### 1. **GitHub Actions (Easiest for Users)**
- **No account connection needed**
- User gets API key from SEO Lens dashboard
- Adds workflow file to their repo
- Action calls our API directly
- **Limitation:** Can't post fancy PR comments (only through Action outputs)

#### 2. **Manual Webhook Setup**
- **No account connection needed**
- User manually adds webhook URL in GitHub repo settings
- Payload sent to our endpoint
- We analyze and store results
- **Limitation:** User must check our dashboard for results (can't post back to PR without auth)

#### 3. **Automatic PR Comments** ✅ Recommended
- **Requires GitHub connection**
- We need GitHub OAuth to get user's token
- Can post formatted SEO reports as PR comments
- Can update comments when PR is updated
- **Best UX** - everything happens in GitHub

#### 4. **GitHub App** (Future)
- **Requires app installation**
- User clicks "Install" on GitHub
- We get all necessary permissions
- Automatic webhook setup
- Can show check statuses

### Recommended Flow:

```
Option 1: Quick Start (No Auth Required)
├── User copies GitHub Actions workflow
├── Adds API key from dashboard
├── SEO analysis runs on PRs
└── Results visible in Action logs + our dashboard

Option 2: Full Integration (GitHub OAuth)
├── User connects GitHub account
├── We auto-configure webhooks
├── Analysis triggers instantly
└── Results posted as PR comments
```

---

## Implementation Plan

### Phase 1: Webhook Infrastructure (Core)

New module: `src/webhooks/`
```
src/webhooks/
├── __init__.py
├── github_webhook_router.py    # GitHub webhook handler
├── gitlab_webhook_router.py    # GitLab webhook handler  
├── webhook_service.py          # Business logic
├── webhook_models.py           # Pydantic schemas
├── webhook_repository.py       # DB operations
└── utils/
    ├── signature_verification.py  # HMAC signature check
    └── url_discovery.py           # Find website URL from repo
```

**Features:**
- Verify webhook signatures (security)
- Parse PR/merge events
- Extract target URL (from PR description, repo settings, or `.seo-lens.yml` config)
- Trigger async SEO analysis via existing service
- Post results back via GitHub API (if authenticated)

---

### Phase 2: GitHub Action (Easy Adoption)

Create public GitHub Action in separate repo: `seo-lens/action`

```yaml
# .github/workflows/seo-lens.yml
name: SEO Lens Analysis
on:
  pull_request:
    types: [opened, synchronize]
  push:
    branches: [main, master]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run SEO Lens Analysis
        uses: seo-lens/action@v1
        with:
          api-key: ${{ secrets.SEO_LENS_API_KEY }}
          url: 'https://your-website.com'  # Or auto-detect from repo
```

---

### Phase 3: Results Delivery (Email-Based) ⭐

**Primary Delivery: Email Notifications**

This is the **recommended approach** because it requires NO GitHub OAuth!

**Email Features:**
- 📧 Sent to user's registered email (from their account)
- 📊 Contains summary of SEO analysis
- 🔗 Link to full detailed report on dashboard
- 📎 Optional PDF attachment of full report
- 🎨 Beautiful HTML email template

**Example Email:**
```
Subject: SEO Analysis Complete for PR #123 - Score: 78/100

Hi [User],

Your SEO analysis for Pull Request #123 in repo "my-website" is complete!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 OVERALL SCORE: 78/100 ⚠️
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

URL Analyzed: https://example.com
Pages Crawled: 42
Analysis Date: 2025-01-15 14:30 UTC

QUICK SUMMARY:
✅ Meta Tags          ✅ Mobile Responsive
✅ HTTPS/SSL          ⚠️ Page Speed (2.3s)
⚠️ Image Alt Tags     ❌ Schema Markup

[View Full Report] [Download PDF]

---
This analysis was triggered by a Pull Request to your main branch.
You can manage email preferences in your dashboard.
```

---

**Alternative: PR Comments (Requires GitHub Auth)**
For users who connect their GitHub account:
- Post SEO report as PR comment (Markdown formatted)
- Show check status (✅/❌ based on SEO score)
- Update comment when PR is updated

**Example PR Comment:**
```markdown
## 🔍 SEO Lens Analysis Report

**URL:** https://example.com  
**Pages Analyzed:** 42  
**Overall Score:** 78/100 ⚠️

### Summary
| Check | Status |
|-------|--------|
| Meta Tags | ✅ Pass |
| Mobile Responsiveness | ✅ Pass |
| Page Speed | ⚠️ Warning (2.3s) |
| Image Alt Tags | ❌ Fail (12 missing) |

[View Full Report](https://seo-lens.com/dashboard/reports/123)
```

---

### Phase 4: Configuration Options

Users can configure via:

**1. Config file in repo:** `.seo-lens.yml`
```yaml
# SEO Lens Configuration
url: https://my-website.com
crawl_mode: standard  # or 'deep'
thresholds:
  score_warning: 70
  score_failure: 50
excluded_paths:
  - /admin/
  - /api/
notifications:
  email: true
  pr_comment: true
```

**2. Environment variables** in GitHub Action
```yaml
with:
  api-key: ${{ secrets.SEO_LENS_API_KEY }}
  url: ${{ vars.WEBSITE_URL }}
  crawl-mode: 'deep'
```

**3. Webhook URL parameters**
```
https://api.seo-lens.com/webhooks/github?url=https://example.com&mode=standard
```

---

## Database Schema Additions

### New Tables:

```sql
-- Stores webhook configurations
CREATE TABLE webhook_configs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR(20) NOT NULL,  -- 'github' or 'gitlab'
    repository_name VARCHAR(255) NOT NULL,
    repository_id VARCHAR(100),     -- GitHub's repo ID
    webhook_secret VARCHAR(255),    -- For signature verification
    target_url VARCHAR(500),        -- Website URL to analyze
    crawl_mode VARCHAR(20) DEFAULT 'standard',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Logs incoming webhook events
CREATE TABLE webhook_events (
    id UUID PRIMARY KEY,
    webhook_config_id UUID REFERENCES webhook_configs(id),
    event_type VARCHAR(50) NOT NULL,  -- 'pull_request', 'push', etc.
    delivery_id VARCHAR(100),         -- GitHub's delivery ID
    payload JSONB,                    -- Full webhook payload
    status VARCHAR(20),               -- 'received', 'processing', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Links PR to SEO analysis reports
CREATE TABLE pr_analyses (
    id UUID PRIMARY KEY,
    webhook_event_id UUID REFERENCES webhook_events(id),
    pr_number INTEGER,
    pr_title VARCHAR(500),
    branch_name VARCHAR(255),
    commit_sha VARCHAR(100),
    seo_insight_id UUID REFERENCES seo_insights(id),
    status VARCHAR(20),               -- 'pending', 'running', 'completed', 'failed'
    score INTEGER,
    github_comment_id VARCHAR(100),   -- ID of posted PR comment
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Stores user's GitHub/GitLab tokens (encrypted)
CREATE TABLE user_vcs_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR(20) NOT NULL,
    access_token TEXT NOT NULL,       -- Encrypted
    refresh_token TEXT,               -- Encrypted (if applicable)
    scope VARCHAR(255),
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## New API Endpoints

### Webhook Endpoints (Public)
```python
POST /webhooks/github          # GitHub webhook receiver
POST /webhooks/gitlab          # GitLab webhook receiver
```

### Webhook Management (Authenticated)
```python
GET    /webhooks/configs       # List user's webhook configs
POST   /webhooks/configs       # Create new webhook config
PUT    /webhooks/configs/{id}  # Update config
DELETE /webhooks/configs/{id}  # Delete config
POST   /webhooks/test/{id}     # Test webhook delivery
```

### GitHub/GitLab Integration
```python
GET  /auth/github/connect      # Start GitHub OAuth flow
GET  /auth/github/callback     # OAuth callback
GET  /auth/gitlab/connect      # Start GitLab OAuth flow
GET  /auth/gitlab/callback     # OAuth callback
```

### PR Analysis
```python
GET /pr-analyses               # List PR analyses for user
GET /pr-analyses/{id}          # Get specific analysis
GET /pr-analyses/{id}/report   # Get full SEO report
```

---

## Technical Implementation Steps

### Step 1: Database Migration
- Create new tables for webhook configs, events, PR analyses
- Add user_vcs_tokens table for OAuth tokens

### Step 2: Webhook Router
- Create webhook endpoints with signature verification
- Implement GitHub webhook payload parser
- Implement GitLab webhook payload parser

### Step 3: GitHub API Integration
- Use `PyGithub` or `httpx` for API calls
- Implement PR comment posting
- Implement check status updates

### Step 4: URL Discovery Logic
```python
# Priority order for finding website URL:
1. Query parameter in webhook URL (?url=https://...)
2. Config file in repo (.seo-lens.yml)
3. Repository "website" field in GitHub
4. README.md link detection
5. CNAME file (for GitHub Pages)
```

### Step 5: Async Processing
- Use existing Redis + Celery (or FastAPI background tasks)
- Queue SEO analysis jobs
- Update PR comment when complete

### Step 5.5: Email Service Setup (CRITICAL)
- Choose email provider: SendGrid, AWS SES, or Mailgun
- Create HTML email templates for SEO reports
- Set up email queue for async sending
- Add email preferences to user model

**Email Template Structure:**
```
src/notifications/
├── __init__.py
├── email_service.py         # Email sending logic
├── email_templates/
│   ├── __init__.py
│   ├── base.html           # Base email template
│   ├── seo_report.html     # SEO report email
│   └── seo_report.txt      # Plain text version
└── queue/
    └── email_queue.py      # Email job queue
```

**Example Email Service:**
```python
async def send_seo_report_email(
    to_email: str,
    user_name: str,
    report_data: dict,
    pdf_attachment: bytes = None
):
    """Send SEO analysis report via email"""
    subject = f"SEO Report: {report_data['url']} - Score: {report_data['score']}/100"
    
    html_content = render_template(
        'seo_report.html',
        user_name=user_name,
        report=report_data
    )
    
    await email_client.send(
        to=to_email,
        subject=subject,
        html=html_content,
        attachments=[pdf_attachment] if pdf_attachment else None
    )
```

### Step 6: GitHub Action
- Create separate public repo for the Action
- Simple Docker-based action that calls our API
- Support for custom inputs (URL, crawl mode, thresholds)

---

## Security Considerations

### Webhook Signature Verification
```python
# GitHub webhook HMAC signature verification
import hmac
import hashlib

def verify_github_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = 'sha256=' + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

### API Key Security
- Keys should be stored in GitHub Secrets
- Rate limiting per API key
- Keys can be revoked from dashboard

### OAuth Token Encryption
- Tokens encrypted at rest (AES-256)
- Never log tokens
- Regular token rotation

---

## Rate Limiting Considerations

| Service | Limit | Strategy |
|---------|-------|----------|
| GitHub API | 5,000/hour | Cache aggressively, batch requests |
| GitLab API | Varies by plan | Respect rate limit headers |
| Our API | Configurable | Rate limit per API key |
| SEO Crawler | Resource-based | Queue jobs, limit concurrent |

**Mitigation:**
- Implement caching for GitHub API calls
- Use conditional requests (If-None-Match)
- Queue PR analyses to smooth load
- Implement exponential backoff

---

## Cost Considerations

**Potential Costs:**
- SEO crawling is resource-intensive
- Every PR push could trigger re-analysis
- GitHub Actions minutes (for user)
- Our server resources for crawling

**Mitigation:**
- Only analyze on PR open (not every commit)
- Implement smart caching (don't re-crawl unchanged pages)
- Free tier: X analyses per month
- Premium: Unlimited analyses

---

## User Flows

### Flow 1: GitHub Actions + Email (Recommended - No Auth!) ⭐
```
1. User signs up on SEO Lens → Gets API key
2. User copies workflow file from docs
3. User adds API key to repo secrets
4. User creates PR
5. Analysis runs automatically
6. 📧 EMAIL SENT with SEO report!
7. User clicks email link to view full report
```

**GitHub Actions Workflow:**
```yaml
name: SEO Analysis
on: [pull_request]

jobs:
  seo:
    runs-on: ubuntu-latest
    steps:
      - uses: seo-lens/action@v1
        with:
          api-key: ${{ secrets.SEO_LENS_API_KEY }}
          # Email is fetched from user's account automatically!
```

---

### Flow 2: Manual Webhook + Email
```
1. User gets webhook URL from dashboard
2. User manually adds webhook in GitHub repo settings
3. User configures events (PR, push)
4. Webhooks sent to our endpoint
5. Analysis runs
6. 📧 EMAIL SENT with SEO report!
7. Full report available in dashboard
```

---

### Flow 3: Full Integration (With Auth - Optional Enhancement)
```
1. User clicks "Connect GitHub" in dashboard (optional)
2. OAuth flow to get permissions
3. User selects repos to enable
4. We auto-configure webhooks
5. User creates PR
6. Analysis triggers instantly
7. 📧 EMAIL SENT + PR comment posted
```

**This gives users BOTH email AND PR comments!**

---

## Success Metrics

- Number of repos with CI/CD integration enabled
- Number of PR analyses run per week
- User engagement (comments viewed, reports opened)
- Conversion rate (free users → paid for more analyses)

---

## Future Enhancements

1. **GitHub Checks API**: Show SEO status as PR check
2. **Branch Protection**: Block merge if SEO score < threshold
3. **Comparative Analysis**: Compare PR branch vs main branch
4. **Inline Comments**: Comment on specific files with issues
5. **Slack/Discord Integration**: Send notifications to channels
6. **GitLab Support**: Full GitLab CI/CD integration
7. **Bitbucket**: Support Bitbucket webhooks

---

## Summary

**Is it possible?** ✅ Yes  
**Can we use email instead of PR comments?** ✅ **Absolutely!** (This is actually BETTER!)

**Do users need to connect their account?** 
| Feature | Account Connection? |
|---------|-------------------|
| GitHub Actions + Email | ❌ **NO** - Just API key |
| Webhook + Email | ❌ **NO** - Just API key/token |
| PR Comments | ✅ Yes - Requires GitHub OAuth |

**🏆 Recommended approach:**

### Phase 1: GitHub Actions + Email (Start Here!)
- ✅ No auth required
- ✅ Works immediately
- ✅ Users get reports in email
- ✅ Simple workflow file

### Phase 2: Webhook Support
- ✅ For users who want real-time triggers
- ✅ Still uses email for delivery

### Phase 3: Optional GitHub OAuth (Future)
- ✅ For users who want PR comments
- ✅ Enhanced UX but not required

**Bottom Line:** Email delivery makes this feature accessible to everyone without any GitHub permissions! 🎉
