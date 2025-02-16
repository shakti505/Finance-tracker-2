# from rest_framework.views import exception_handler
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework.exceptions import APIException, AuthenticationFailed
# from django.core.exceptions import ValidationError, PermissionDenied

# from django.http import Http404
# from django.contrib.auth.models import User

# from .logging import logger


# def custom_exception_handler(exc, context):
#     """
#     Custom exception handler for DRF that removes DRF's default "detail"
#     and provides a structured error response.
#     """
#     response = exception_handler(exc, context)  # Call DRF's default handler first

#     if isinstance(exc, Http404):
#         response = Response(
#             {"errors": {"message": "Resource not found", "code": "not_found"}},
#             status=status.HTTP_404_NOT_FOUND,
#         )

#     elif isinstance(exc, PermissionDenied):
#         response = Response(
#             {
#                 "errors": {
#                     "message": "You do not have permission",
#                     "code": "forbidden",
#                 }
#             },
#             status=status.HTTP_403_FORBIDDEN,
#         )

#     elif isinstance(exc, AuthenticationFailed):
#         response = Response(
#             {
#                 "errors": {
#                     "message": "Invalid or expired token",
#                     "code": "authentication_failed",
#                 }
#             },
#             status=status.HTTP_401_UNAUTHORIZED,
#         )

#     elif isinstance(exc, ValidationError):
#         response = Response(
#             {
#                 "errors": {
#                     "message": (exc.messages if hasattr(exc, "messages") else str(exc)),
#                     "code": "validation_error",
#                 }
#             },
#             status=status.HTTP_400_BAD_REQUEST,
#         )

#     else:
#         logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
#         response = Response(
#             {
#                 "errors": {
#                     "message": "An unexpected error occurred",
#                     "code": "server_error",
#                 }
#             },
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#         )

#     return response


from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    PermissionDenied as DRFPermissionDenied,
    NotAuthenticated,
)
from django.core.exceptions import ValidationError, PermissionDenied as DjangoPermissionDenied
from django.http import Http404

from .logging import logger


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF that removes DRF's default "detail"
    and provides a structured error response.
    """
    response = exception_handler(exc, context)  # Call DRF's default handler first

    if isinstance(exc, Http404):
        response = Response(
            {"errors": {"detail": "Resource not found",}},
            status=status.HTTP_404_NOT_FOUND,
        )

    elif isinstance(exc, (DRFPermissionDenied, DjangoPermissionDenied)):
        response = Response(
            {
                "errors": {
                    "detail": "You do not have permission",

                }
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    elif isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        response = Response(
            {
                "errors": {
                    "detail": "Invalid or expired token",
                }
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    elif isinstance(exc, ValidationError):
        response = Response(
            {
                "errors": {
                    "detail": (exc.details if hasattr(exc, "details") else str(exc)),

                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    elif isinstance(exc, APIException) and response is not None:
        # Catch any other APIExceptions properly
        response.data = {
            "errors": {
                "detail": response.data.get("detail", "A server error occurred"),

            }
        }

    else:
        logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
        response = Response(
            {
                "errors": {
                    "detail": "An unexpected error occurred",

                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
