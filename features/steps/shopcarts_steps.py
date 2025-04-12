######################################################################
# Copyright 2016, 2024 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################

"""
Shopcart Steps

Steps file for Shopcart.feature

For information on Waiting until elements are present in the HTML see:
    https://selenium-python.readthedocs.io/waits.html
"""
import requests
from compare3 import expect
from behave import given  # pylint: disable=no-name-in-module

# HTTP Return Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204

WAIT_TIMEOUT = 60


@given("the following shopcart items")
def step_impl(context):
    """Delete all Shopcarts and load new ones"""

    # Get a list of all shopcarts
    rest_endpoint = f"{context.base_url}/shopcarts"
    context.resp = requests.get(rest_endpoint, timeout=WAIT_TIMEOUT)
    expect(context.resp.status_code).equal_to(HTTP_200_OK)

    # Delete existing shopcarts for each user
    user_ids = set()
    for cart in context.resp.json():
        for item in cart.get("items", []):
            user_id = item["user_id"]
            if user_id not in user_ids:
                user_ids.add(user_id)
                context.resp = requests.delete(
                    f"{context.base_url}/shopcarts/{user_id}", timeout=WAIT_TIMEOUT
                )
                expect(context.resp.status_code).equal_to(HTTP_204_NO_CONTENT)

    # Load the database with new shopcart items
    for row in context.table:
        user_id = int(row["user_id"])
        payload = {
            "item_id": int(row["item_id"]),
            "description": row["description"],
            "price": float(row["price"]),
            "quantity": int(row["quantity"]),
        }
        shopcart_endpoint = f"{context.base_url}/shopcarts/{user_id}"
        context.resp = requests.post(
            shopcart_endpoint, json=payload, timeout=WAIT_TIMEOUT
        )
        expect(context.resp.status_code).equal_to(HTTP_201_CREATED)
