from flask_restx import Api

api = Api(
    title="Shopcart REST API Service",
    version="1.0",
    description="Create, update, delete, and manage shopcarts for users.",
    doc="/apidocs",  # Exposes Swagger UI at this path
)
