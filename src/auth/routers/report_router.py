from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query, status

from src.auth.repository.report_repository import (
    create_report,
    delete_report,
    get_report_by_id,
    list_reports,
    update_report,
)
from src.auth.schemas.schemas import CreateReportRequest, UpdateReportRequest
from src.constants.response_status import RESPONSE_STATUS_SUCCESS
from src.utils.response_helper import create_response


router = APIRouter(prefix="/auth/reports", tags=["Auth Reports"])


def _record_to_dict(record: Any) -> Dict[str, Any]:
    return dict(record)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_report_endpoint(payload: CreateReportRequest):
    record = await create_report(payload.report_type, payload.report)
    return create_response(RESPONSE_STATUS_SUCCESS, "Report created", _record_to_dict(record))


@router.get("/{report_id}", status_code=status.HTTP_200_OK)
async def get_report_endpoint(report_id: str):
    record = await get_report_by_id(report_id)
    if not record:
        raise HTTPException(status_code=404, detail="Report not found")
    return create_response(RESPONSE_STATUS_SUCCESS, "Report fetched", _record_to_dict(record))


@router.get("", status_code=status.HTTP_200_OK)
async def list_reports_endpoint(
    report_type: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    rows = await list_reports(report_type=report_type, limit=limit, offset=offset)
    return create_response(
        RESPONSE_STATUS_SUCCESS,
        "Reports listed",
        [_record_to_dict(row) for row in rows],
    )


@router.put("/{report_id}", status_code=status.HTTP_200_OK)
async def update_report_endpoint(report_id: str, payload: UpdateReportRequest):
    record = await update_report(
        report_id=report_id, report=payload.report, report_type=payload.report_type
    )
    if not record:
        raise HTTPException(status_code=404, detail="Report not found")
    return create_response(RESPONSE_STATUS_SUCCESS, "Report updated", _record_to_dict(record))


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report_endpoint(report_id: str):
    deleted = await delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
    return create_response(RESPONSE_STATUS_SUCCESS, "Report deleted", {"deleted": True})

