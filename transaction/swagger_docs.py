from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from .serializers import TransactionSerializer

# Define common responses
error_response = openapi.Response("Error Response", openapi.Schema(type=openapi.TYPE_OBJECT))

def transaction_list_docs():
    return swagger_auto_schema(
        operation_description="Retrieve all transactions for the authenticated user.",
        responses={200: TransactionSerializer(many=True)},
    )

def transaction_create_docs():
    return swagger_auto_schema(
        operation_description="Create a new transaction.",
        request_body=TransactionSerializer,
        responses={201: TransactionSerializer(), 400: error_response},
    )

def transaction_detail_docs():
    return swagger_auto_schema(
        operation_description="Retrieve details of a specific transaction.",
        responses={200: TransactionSerializer()},
    )

def transaction_update_docs():
    return swagger_auto_schema(
        operation_description="Update a transaction (full update).",
        request_body=TransactionSerializer,
        responses={200: TransactionSerializer()},
    )

def transaction_partial_update_docs():
    return swagger_auto_schema(
        operation_description="Partially update a transaction.",
        request_body=TransactionSerializer,
        responses={200: TransactionSerializer()},
    )

def transaction_delete_docs():
    return swagger_auto_schema(
        operation_description="Delete a transaction (soft delete).",
        responses={204: "No Content"},
    )
