from typing import Any, Dict, List, Optional
import json

import asyncpg

from src.auth.schemas.db import get_pool


async def init_reports_table() -> None:
    """Create reports table if it doesn't exist."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                report_type TEXT NOT NULL,
                report JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            """
        )
        await conn.execute(
            """
            CREATE INDEX IF NOT EXISTS reports_report_type_idx
            ON reports(report_type);
            """
        )


def _validate_report(report: Dict[str, Any]) -> Dict[str, Any]:
    if report is None:
        raise ValueError("report cannot be null")
    if not isinstance(report, dict):
        raise ValueError("report must be a dictionary")
    return report


async def create_report(report_type: str, report: Dict[str, Any]) -> asyncpg.Record:
    """Create a report row."""
    payload = _validate_report(report)
    payload_json = json.dumps(payload)
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            INSERT INTO reports (report_type, report)
            VALUES ($1, $2::jsonb)
            RETURNING id, report_type, report, created_at, updated_at;
            """,
            report_type,
            payload_json,
        )


async def get_report_by_id(report_id: str) -> Optional[asyncpg.Record]:
    """Fetch one report by UUID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            """
            SELECT id, report_type, report, created_at, updated_at
            FROM reports
            WHERE id = $1::uuid;
            """,
            report_id,
        )


async def list_reports(
    report_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[asyncpg.Record]:
    """List reports, optionally filtered by report_type."""
    safe_limit = max(1, min(limit, 500))
    safe_offset = max(0, offset)
    pool = await get_pool()
    async with pool.acquire() as conn:
        if report_type:
            return await conn.fetch(
                """
                SELECT id, report_type, report, created_at, updated_at
                FROM reports
                WHERE report_type = $1
                ORDER BY created_at DESC
                LIMIT $2 OFFSET $3;
                """,
                report_type,
                safe_limit,
                safe_offset,
            )

        return await conn.fetch(
            """
            SELECT id, report_type, report, created_at, updated_at
            FROM reports
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2;
            """,
            safe_limit,
            safe_offset,
        )


async def update_report(
    report_id: str,
    report: Dict[str, Any],
    report_type: Optional[str] = None,
) -> Optional[asyncpg.Record]:
    """Update report JSON payload and optionally report_type."""
    payload = _validate_report(report)
    payload_json = json.dumps(payload)
    pool = await get_pool()
    async with pool.acquire() as conn:
        if report_type is not None:
            return await conn.fetchrow(
                """
                UPDATE reports
                SET report_type = $2,
                    report = $3::jsonb,
                    updated_at = now()
                WHERE id = $1::uuid
                RETURNING id, report_type, report, created_at, updated_at;
                """,
                report_id,
                report_type,
                payload_json,
            )

        return await conn.fetchrow(
            """
            UPDATE reports
            SET report = $2::jsonb,
                updated_at = now()
            WHERE id = $1::uuid
            RETURNING id, report_type, report, created_at, updated_at;
            """,
            report_id,
            payload_json,
        )


async def delete_report(report_id: str) -> bool:
    """Delete report by UUID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            DELETE FROM reports
            WHERE id = $1::uuid;
            """,
            report_id,
        )
    return result.endswith(" 1")

