from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from exceptions import CognovaError


async def cognova_exception_handler(
    request: Request, exc: CognovaError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": type(exc).__name__, "detail": exc.message},
        headers=exc.headers,
    )


def add_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(CognovaError, cognova_exception_handler)
