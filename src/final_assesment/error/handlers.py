from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.final_assesment.error.exceptions import WorkflowException

def register_error_handlers(app: FastAPI):
    @app.exception_handler(WorkflowException)
    async def workflow_exception_handler(request: Request, exc: WorkflowException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.message,
                "detail": exc.message,
                "status_code": exc.status_code
            }
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": str(exc.detail),
                "detail": str(exc.detail),
                "status_code": exc.status_code
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": "Validation error",
                "detail": exc.errors(),
                "status_code": 422
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(exc),
                "detail": str(exc),
                "status_code": 500
            }
        )

