"""Swagger/OpenAPI configuration for the Shopcart service.

This module configures the Flask-RESTX API documentation and Swagger UI.
It sets up the API title, version, description, and documentation endpoint.
"""

from flask_restx import Api

api = Api(
    title="Shopcart REST API Service",
    version="1.0",
    description="Create, update, delete, and manage shopcarts for users.",
    doc="/apidocs",  # Exposes Swagger UI at this path
    doc_expansion="full",  # 'list' expands all tags by default
)
