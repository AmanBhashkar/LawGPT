# --- Library Imports ---
from typing import Union
from fastapi import Request
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.exception_handlers import (
    request_validation_exception_handler as _request_validation_exception_handler,
)
from fastapi.responses import JSONResponse
from fastapi.responses import PlainTextResponse
from fastapi.responses import Response
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.tracer import Tracer
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.span import SpanKind
from opencensus.trace.attributes_helper import COMMON_ATTRIBUTES
import traceback

# ---

# --- User Imports ---
from app.config.env import env
from app.utils.app_logger.logger import logger

# ---

# --- Constants ---
OPENAI_TRACER = Tracer(
    exporter=AzureExporter(connection_string=env.APPLICATIONINSIGHTS_CONNECTION_STRING), sampler=ProbabilitySampler(1.0)
)
HTTP_URL = COMMON_ATTRIBUTES["HTTP_URL"]
HTTP_STATUS_CODE = COMMON_ATTRIBUTES["HTTP_STATUS_CODE"]
ERROR_NAME = COMMON_ATTRIBUTES["ERROR_NAME"]
ERROR_MESSAGE = COMMON_ATTRIBUTES["ERROR_MESSAGE"]
HTTP_METHOD = COMMON_ATTRIBUTES["HTTP_METHOD"]
HTTP_PATH = COMMON_ATTRIBUTES["HTTP_PATH"]
STACKTRACE = COMMON_ATTRIBUTES["STACKTRACE"]
# ---


def add_trace_to_azure_appinsight(request: Request, exc: HTTPException):
    """
    This function adds required traces to azure app insight logs for proper identification and dashboarding
    """
    exception_traceback = traceback.format_exc(limit=2)
    error_message_args = getattr(exc, "args", None)
    error_message_details = getattr(exc, "detail", None)
    error_message = error_message_details
    if not error_message_details:
        if error_message_args:
            error_message = error_message_args[0]
        else:
            error_message = "Something went wrong"
    with OPENAI_TRACER.span("main") as span:
        span.span_kind = SpanKind.SERVER
        OPENAI_TRACER.add_attribute_to_current_span(
            attribute_key=HTTP_STATUS_CODE, attribute_value=getattr(exc, "status_code", 500)
        )
        OPENAI_TRACER.add_attribute_to_current_span(attribute_key=HTTP_URL, attribute_value=str(request.url))
        OPENAI_TRACER.add_attribute_to_current_span(attribute_key=ERROR_NAME, attribute_value=str(type(exc).__name__))
        OPENAI_TRACER.add_attribute_to_current_span(attribute_key=ERROR_MESSAGE, attribute_value=error_message)
        OPENAI_TRACER.add_attribute_to_current_span(attribute_key=HTTP_METHOD, attribute_value=str(request.method))
        OPENAI_TRACER.add_attribute_to_current_span(attribute_key=HTTP_PATH, attribute_value=str(request.url.path))
        OPENAI_TRACER.add_attribute_to_current_span(attribute_key=STACKTRACE, attribute_value=str(exception_traceback))


async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    This is a wrapper to the default RequestValidationException handler of FastAPI.
    This function will be called when client input is not valid.
    """
    logger.debug("Our custom request_validation_exception_handler was called")
    body = await request.body()
    query_params = request.query_params._dict  # pylint: disable=protected-access
    detail = {"errors": exc.errors(), "body": body.decode(), "query_params": query_params}
    logger.info(detail)
    return await _request_validation_exception_handler(request, exc)


async def http_exception_handler(request: Request, exc: HTTPException) -> Union[JSONResponse, Response]:
    """
    This is a wrapper to the default HTTPException handler of FastAPI.
    This function will be called when a HTTPException is explicitly raised.
    """
    exception_traceback = traceback.format_exc(limit=2)
    url = f"{request.url.path}?{request.query_params}" if request.query_params else request.url.path
    logger.exception(
        {
            "status": exc.status_code,
            "message": exc.detail,
            "url": url,
            "method": request.method,
            "trace": exception_traceback,
        }
    )
    add_trace_to_azure_appinsight(request, exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": exc.status_code, "message": exc.detail, "success": False},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> PlainTextResponse:
    """
    This middleware will log all unhandled exceptions.
    Unhandled exceptions are all exceptions that are not HTTPExceptions or RequestValidationErrors.
    """
    exception_traceback = traceback.format_exc(limit=2)
    url = f"{request.url.path}?{request.query_params}" if request.query_params else request.url.path
    logger.exception(
        {
            "status": 500,
            "message": exc,
            "url": url,
            "method": request.method,
            "trace": exception_traceback,
        }
    )
    add_trace_to_azure_appinsight(request, exc)
    return JSONResponse(
        status_code=500,
        content={"status": 500, "message": str(exc), "success": False},
    )
