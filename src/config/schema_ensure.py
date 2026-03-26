from __future__ import annotations

from sqlalchemy import text

from src.config.database import engine


async def ensure_status_columns() -> None:
    """
    Ensure `status` column exists on results tables.
    This is additive and safe for existing deployments.
    """
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "ALTER TABLE seo_insight_results "
                "ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'completed';"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE keyword_suggestions "
                "ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'completed';"
            )
        )
        await conn.execute(
            text(
                "ALTER TABLE keyword_rank_results "
                "ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'completed';"
            )
        )

