import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


logger = logging.getLogger(__name__)


def success_response(data=None, message: str = "success") -> dict:
    return {
        "code": 0,
        "message": message,
        "data": data,
    }


def error_response(message: str, code: int = 1, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "code": code,
            "message": message,
            "data": None,
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(_: Request, exc: StarletteHTTPException):
        return error_response(
            message=str(exc.detail),
            code=exc.status_code,
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        logger.warning("Request validation failed: %s", exc.errors())
        return error_response(
            message="请求参数校验失败",
            code=422,
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(_: Request, exc: Exception):
        logger.exception("Unhandled server exception: %s", exc)
        return error_response(
            message="服务器内部错误，请稍后重试",
            code=500,
            status_code=500,
        )
