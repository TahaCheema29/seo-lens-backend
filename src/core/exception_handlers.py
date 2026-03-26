from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from src.core.response_status import RESPONSE_STATUS_ERROR


async def http_exception_handler(_: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": RESPONSE_STATUS_ERROR,
            "message": exc.detail,
            "data": None,
        },
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={
            "status": RESPONSE_STATUS_ERROR,
            "message": "Validation error",
            "data": exc.errors(),
        },
    )