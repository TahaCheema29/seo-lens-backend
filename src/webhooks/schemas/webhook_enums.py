from enum import Enum


class WebhookProvider(str, Enum):
    GITHUB = "github"
    GITLAB = "gitlab"


class WebhookEventType(str, Enum):
    PULL_REQUEST = "pull_request"
    PUSH = "push"
    MERGE_REQUEST = "merge_request"


class WebhookEventStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlMode(str, Enum):
    STANDARD = "standard"
    DEEP = "deep"
    LIGHT = "light"