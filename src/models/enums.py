import enum


class AnalysisStatus(str, enum.Enum):
    """Status of analysis"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"