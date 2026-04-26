"""
Custom exception handlers for API responses
"""
import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error responses
    """
    response = exception_handler(exc, context)

    if response is not None:
        # Add timestamp to error response
        response.data = {
            "error": True,
            "detail": response.data.get("detail") or response.data,
            "status_code": response.status_code,
        }
        
        # Log the exception
        logger.warning(
            f"API Exception: {exc.__class__.__name__} - {str(exc)}",
            extra={"context": context},
        )
    else:
        # Handle unexpected errors
        logger.error(
            f"Unhandled Exception: {exc.__class__.__name__} - {str(exc)}",
            exc_info=True,
            extra={"context": context},
        )
        response = Response(
            {
                "error": True,
                "detail": "Internal server error",
                "status_code": 500,
            },
            status=500,
        )

    return response
