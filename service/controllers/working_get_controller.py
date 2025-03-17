# """
# GET Controller logic for Shopcart Service
# """

# from datetime import datetime, timedelta
# from sqlalchemy import and_, or_
# from werkzeug.exceptions import HTTPException
# from flask import jsonify, abort, request
# from flask import current_app as app
# from service.models import Shopcart
# from service.common import status

# RANGE_OPERATORS = {"lt": "<", "lte": "<=", "gt": ">", "gte": ">="}

# VALID_FIELDS = {
#     "user_id": (Shopcart.user_id, int),
#     "item_id": (Shopcart.item_id, int),
#     "description": (Shopcart.description, str),
#     "quantity": (Shopcart.quantity, int),
#     "price": (Shopcart.price, float),
#     "created_at": (Shopcart.created_at, datetime),
#     "last_updated": (Shopcart.last_updated, datetime),
# }


# def parse_datetime(value):
#     """Convert 'YYYY-MM-DD' to a datetime object."""
#     try:
#         return datetime.strptime(value, "%Y-%m-%d")
#     except ValueError:
#         raise ValueError(f"Invalid date format: {value}. Expected YYYY-MM-DD.")


# def get_shopcarts_controller():
#     """List all shopcarts with optional filtering based on query parameters"""
#     app.logger.info("Request to list shopcarts with filters")

#     try:
#         filters = []
#         query_params = request.args.to_dict(
#             flat=False
#         )  # Allows multiple values per key

#         for key, values in query_params.items():
#             if key in VALID_FIELDS:
#                 field, cast_type = VALID_FIELDS[key]
#                 condition_list = []

#                 for value in values:
#                     try:
#                         # **Range Filtering (e.g., created_at=~gte~2025-03-17)**
#                         if "~" in value:
#                             _, operator, filter_value = value.split("~")
#                             filter_value = (
#                                 parse_datetime(filter_value)
#                                 if cast_type is datetime
#                                 else cast_type(filter_value)
#                             )

#                             # Adjust datetime filtering to capture full days
#                             if cast_type is datetime and operator in ["lt", "lte"]:
#                                 filter_value += timedelta(days=1) - timedelta(seconds=1)

#                             expr = eval(
#                                 f"field {RANGE_OPERATORS[operator]} filter_value"
#                             )
#                             condition_list.append(expr)

#                         # **Multiple Date Filtering (`created_at=YYYY-MM-DD,YYYY-MM-DD`)**
#                         elif cast_type is datetime and "," in value:
#                             date_conditions = []
#                             for date_str in value.split(","):
#                                 date_obj = parse_datetime(date_str.strip())
#                                 start_date = date_obj  # `YYYY-MM-DD 00:00:00`
#                                 end_date = (
#                                     start_date
#                                     + timedelta(days=1)
#                                     - timedelta(seconds=1)
#                                 )  # `YYYY-MM-DD 23:59:59`
#                                 date_conditions.append(
#                                     and_(field >= start_date, field <= end_date)
#                                 )

#                             condition_list.append(or_(*date_conditions))

#                         # **Exact Date Filtering (`created_at=YYYY-MM-DD`)**
#                         elif cast_type is datetime:
#                             start_date = parse_datetime(value)
#                             end_date = (
#                                 start_date + timedelta(days=1) - timedelta(seconds=1)
#                             )
#                             condition_list.append(
#                                 and_(field >= start_date, field <= end_date)
#                             )

#                         # **List-Based Filtering (e.g., `user_id=1,2,3`)**
#                         elif "," in value:
#                             parsed_values = [
#                                 cast_type(v.strip()) for v in value.split(",")
#                             ]
#                             condition_list.append(field.in_(parsed_values))

#                         # **Exact Match for Other Fields (`user_id=5`)**
#                         else:
#                             condition_list.append(field == cast_type(value))

#                     except (ValueError, TypeError) as e:
#                         return jsonify({"error": str(e)}), status.HTTP_400_BAD_REQUEST

#                 if condition_list:
#                     filters.append(or_(*condition_list))

#         # Execute query with filters
#         if filters:
#             filtered_items = Shopcart.query.filter(and_(*filters)).all()
#         else:
#             filtered_items = Shopcart.all()

#         # Group results by `user_id`
#         user_items = {}
#         for item in filtered_items:
#             if item.user_id not in user_items:
#                 user_items[item.user_id] = []
#             user_items[item.user_id].append(item.serialize())

#         # Format final JSON response
#         shopcarts_list = [
#             {"user_id": user_id, "items": items}
#             for user_id, items in user_items.items()
#         ]

#         return jsonify(shopcarts_list), status.HTTP_200_OK

#     except Exception as e:
#         app.logger.error(f"Error filtering shopcarts: {str(e)}")
#         return (
#             jsonify({"error": f"Internal server error: {str(e)}"}),
#             status.HTTP_500_INTERNAL_SERVER_ERROR,
#         )


# def get_user_shopcart_controller(user_id):
#     """Gets the shopcart for a specific user id"""
#     app.logger.info("Request to get shopcart for user_id: '%s'", user_id)

#     try:

#         user_items = Shopcart.find_by_user_id(user_id=user_id)

#         if not user_items:
#             return abort(
#                 status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found."
#             )

#         user_list = [{"user_id": user_id, "items": []}]
#         for item in user_items:
#             user_list[0]["items"].append(item.serialize())
#         return jsonify(user_list), status.HTTP_200_OK
#     except HTTPException as e:
#         raise e
#     except Exception as e:  # pylint: disable=broad-except
#         app.logger.error(f"Error reading shopcart for user_id: '{user_id}'")
#         return (
#             jsonify({"error": f"Internal server error: {str(e)}"}),
#             status.HTTP_500_INTERNAL_SERVER_ERROR,
#         )


# def get_user_shopcart_items_controller(user_id):
#     """Gets all items in a specific user's shopcart"""
#     app.logger.info("Request to get all items for user_id: '%s'", user_id)

#     try:
#         user_items = Shopcart.find_by_user_id(user_id=user_id)

#         if not user_items:
#             return abort(
#                 status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found."
#             )
#         # Just return the serialized items directly as a list
#         items_list = [{"user_id": user_id, "items": []}]
#         for item in user_items:
#             data = item.serialize()
#             del data["created_at"]
#             del data["last_updated"]
#             items_list[0]["items"].append(data)
#         return jsonify(items_list), status.HTTP_200_OK
#     except HTTPException as e:
#         raise e
#     except Exception as e:  # pylint: disable=broad-except
#         app.logger.error(f"Error reading items for user_id: '{user_id}'")
#         return (
#             jsonify({"error": f"Internal server error: {str(e)}"}),
#             status.HTTP_500_INTERNAL_SERVER_ERROR,
#         )


# def get_cart_item_controller(user_id, item_id):
#     """Gets a specific item from a user's shopcart"""
#     app.logger.info("Request to get item %s for user_id: %s", item_id, user_id)

#     try:
#         # First check if the user exists by trying to get any items for this user
#         user_items = Shopcart.find_by_user_id(user_id=user_id)
#         if not user_items:
#             return abort(
#                 status.HTTP_404_NOT_FOUND, f"User with id '{user_id}' was not found."
#             )

#         # Now try to find the specific item
#         cart_item = Shopcart.find(user_id, item_id)
#         if not cart_item:
#             return (
#                 jsonify(
#                     {"error": f"Item {item_id} not found in user {user_id}'s cart"}
#                 ),
#                 status.HTTP_404_NOT_FOUND,
#             )

#         # Return the serialized item
#         return jsonify(cart_item.serialize()), status.HTTP_200_OK

#     except HTTPException as e:
#         raise e
#     except Exception as e:  # pylint: disable=broad-except
#         app.logger.error(f"Error retrieving item {item_id} for user_id: '{user_id}'")
#         return (
#             jsonify({"error": f"Internal server error: {str(e)}"}),
#             status.HTTP_500_INTERNAL_SERVER_ERROR,
#         )
