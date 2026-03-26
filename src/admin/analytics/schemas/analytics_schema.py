from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class AdminOverviewResponse(BaseModel):
    total_users: int
    active_users: int
    new_this_week: int
    admin_count: int
    user_growth: list


class DailyActiveUser(BaseModel):
    date: str
    count: int


class PlatformUsageItem(BaseModel):
    label: str
    value: int
    color: str


class AdminAnalyticsResponse(BaseModel):
    seo_analyses_total: int
    keyword_research_total: int
    rank_checks_total: int
    daily_active_users: list[DailyActiveUser]
    platform_usage: list[PlatformUsageItem]