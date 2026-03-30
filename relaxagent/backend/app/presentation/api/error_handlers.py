from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.chat.exceptions import ChatDomainError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ChatDomainError)
    async def handle_chat_domain_error(_, exc: ChatDomainError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": str(exc)})

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc.detail)})
