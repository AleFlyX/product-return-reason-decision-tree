"""Custom exception classes and global error handlers."""

from fastapi import Request
from fastapi.responses import JSONResponse


class ServiceUnavailableError(Exception):
    """Raised when HDFS/HBase is not available."""

    def __init__(self, detail: str = "Service unavailable"):
        self.detail = detail
        super().__init__(detail)


class ModelNotLoadedError(Exception):
    """Raised when the model file has not been loaded."""

    def __init__(self, detail: str = "Model not loaded"):
        self.detail = detail
        super().__init__(detail)


async def service_unavailable_handler(request: Request, exc: ServiceUnavailableError):
    return JSONResponse(status_code=503, content={"detail": exc.detail})


async def model_not_loaded_handler(request: Request, exc: ModelNotLoadedError):
    return JSONResponse(status_code=503, content={"detail": exc.detail})
