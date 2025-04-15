Feature: The shopcart service back-end
    As an E-commerce Platform Owner
    I need a RESTful shopcart service
    So that I can keep track of all my customers' shopping carts

Background:
    Given the following shopcart items
        | user_id | item_id | description      | price | quantity |
        | 1       | 101     | Deluxe Widget    | 19.99 | 2        |
        | 1       | 102     | Premium Gadget   | 29.99 | 1        |
        | 2       | 201     | Basic Tool       | 9.99  | 3        |
        | 3       | 301     | Fancy Accessory  | 39.99 | 1        |
        | 3       | 302     | Standard Supply  | 14.99 | 5        |

Scenario: The server is running
    When I visit the "Home Page"
    Then I should see "Shopcart RESTful Service" in the title
    And I should not see "404 Not Found"

Scenario: API health check shows online
    When I visit the "Home Page"
    Then the API health status should be "✓ API Online"

Scenario: Add an item to a user's cart via the UI
    When I visit the "Home Page"
    And I set the "User ID" to "4"
    And I set the "Item ID" to "999"
    And I set the "Item Description" to "Test Product"
    And I set the "Item Price" to "49.99"
    And I set the "Item Quantity" to "2"
    And I press the "Create" button
    Then I should see the message "Item successfully added to cart!"
    When I press the "Search" button
    Then I should see the message "Search results found!"
    And I should see "Test Product" in the results
    And I should see "4" in the results
    And I should see "999" in the results

Scenario: Adding to cart fails when quantity is 0
    When I visit the "Home Page"
    And I set the "User ID" to "6"
    And I set the "Item ID" to "1001"
    And I set the "Item Description" to "Zero Item"
    And I set the "Item Price" to "12.99"
    And I set the "Item Quantity" to "0"
    And I press the "Create" button
    Then I should see the message "Server error!"

Scenario: Add an item product to a user's cart via the UI
    When I visit the "Home Page"
    And I set the "User ID" to "5"
    And I set the "Item ID" to "888"
    And I set the "Item Description" to "Item Widget"
    And I set the "Item Price" to "29.99"
    And I set the "Item Quantity" to "3"
    And I set the "Item Stock" to "100"
    And I set the "Item Purchase Limit" to "5"
    And I press the "Create Item" button
    Then I should see the message "Product added from items!"
    When I press the "Search" button
    Then I should see "Item Widget" in the results

Scenario: Add an item product fails due to exceeding purchase limit
    When I visit the "Home Page"
    And I set the "User ID" to "5"
    And I set the "Item ID" to "888"
    And I set the "Item Description" to "Item Widget"
    And I set the "Item Price" to "29.99"
    And I set the "Item Quantity" to "3"
    And I set the "Item Stock" to "100"
    And I set the "Item Purchase Limit" to "2"
    And I press the "Create Item" button
    Then I should see the message "Server error!"

Scenario: List all shopcarts from the UI
    When I visit the "Home Page"
    And I press the "List" button
    Then I should see "Deluxe Widget" in the results
    And I should see "Premium Gadget" in the results
    And I should see "Basic Tool" in the results
    And I should see "Fancy Accessory" in the results
    And I should see "Standard Supply" in the results

Scenario: List all shopcarts from the UI (using Search Button - equivalent to List All when no arguments provided)
    When I visit the "Home Page"
    And I press the "Search" button
    Then I should see "Deluxe Widget" in the results
    And I should see "Premium Gadget" in the results
    And I should see "Basic Tool" in the results
    And I should see "Fancy Accessory" in the results
    And I should see "Standard Supply" in the results

Scenario: Delete a shopcart from the UI
    When I visit the "Home Page"
    And I set the "User ID" to "3"
    And I press the "Delete" button
    Then I should see the message "Shopcart has been deleted!"

Scenario: Delete an item from a user's cart via the UI
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I set the "Item ID" to "101"
    And I press the "Delete Item" button
    Then I should see the message "Item has been deleted from the cart!"
    When I set the "User ID" to "1"
    And I press the "Retrieve" button
    Then I should see "Premium Gadget" in the results
    And I should not see "Deluxe Widget" in the results

Scenario: Cannot delete an item without providing a User ID
    When I visit the "Home Page" 
    And I set the "Item ID" to "101"
    And I press the "Delete Item" button
    Then I should see the message "User ID is required to delete an item."

Scenario: Cannot delete an item without providing an Item ID
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I press the "Delete Item" button
    Then I should see the message "Item ID is required to delete an item."

Scenario: Checkout a user’s cart via the UI
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I press the "Checkout" button
    Then I should see the message "Cart 1 checked out successfully"
    And I should see the message "Total: $69.97"
    When I press the "Clear" button
    And I set the "User ID" to "1"
    And I press the "Search" button
    Then I should see the message "No items found matching the search criteria."

Scenario: Checkout fails when cart is empty
    When I visit the "Home Page"
    And I set the "User ID" to "999"
    And I press the "Checkout" button
    Then I should see the message "No cart found for user 999"

Scenario: Checkout fails when cart is empty
    When I visit the "Home Page"
    And I press the "Checkout" button
    Then I should see the message "Server error!"

Scenario: Filter shopcarts by price and quantity range
    When I visit the "Home Page"
    And I set the "Price Range" to "10,30"
    And I set the "Quantity Range" to "1,3"
    And I press the "Search" button
    Then I should see "Deluxe Widget" in the results
    And I should see "Premium Gadget" in the results
    But I should not see "Basic Tool" in the results
    And I should not see "Fancy Accessory" in the results
    And I should not see "Standard Supply" in the results

Scenario: Filter shopcarts by user_id
    When I visit the "Home Page"
    And I set the "User ID" to "2"
    And I press the "Search" button
    Then I should see "Basic Tool" in the results
    But I should not see "Deluxe Widget" in the results

Scenario: Filter shopcarts by price greater than 30
    When I visit the "Home Page"
    And I set the "Item Price" to "~gt~30"
    And I press the "Search" button
    Then I should see "Fancy Accessory" in the results
    But I should not see "Deluxe Widget" in the results
    And I should not see "Basic Tool" in the results
    And I should not see "Deluxe Widget" in the results
    And I should not see "Standard Supply" in the results

Scenario: Filter shopcarts by quantity less than or equal to 2
    When I visit the "Home Page"
    And I set the "Item Quantity" to "~lte~2"
    And I press the "Search" button
    Then I should see "Deluxe Widget" in the results
    And I should see "Premium Gadget" in the results
    And I should see "Fancy Accessory" in the results
    But I should not see "Standard Supply" in the results
    And I should not see "Basic Tool" in the results

Scenario: Filter shopcarts by user_id and price greater than 20
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I set the "Item Price" to "~gt~20"
    And I press the "Search" button
    Then I should see "Premium Gadget" in the results
    But I should not see "Deluxe Widget" in the results

Scenario: Filter shopcarts with min-price and max-price range
    When I visit the "Home Page"
    And I set the "Min Price" to "10"
    And I set the "Max Price" to "30"
    And I press the "Search" button
    Then I should see "Deluxe Widget" in the results
    And I should see "Premium Gadget" in the results
    And I should see "Standard Supply" in the results
    But I should not see "Fancy Accessory" in the results
    And I should not see "Basic Tool" in the results

Scenario: Return error for invalid price_range format
    When I visit the "Home Page"
    And I set the "Price Range" to "40"
    And I press the "Search" button
    Then I should see the message "Server error!"

Scenario: Return error for using both price and min-price
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I set the "Item Price" to "~gte~40"
    And I set the "Min Price" to "30"
    And I press the "Search" button
    Then I should see the message "Server error!"

Scenario: Return error for invalid min-price
    When I visit the "Home Page"
    And I set the "Min Price" to "cheap"
    And I press the "Search" button
    Then I should see the message "Server error!"

Scenario: Filter shopcarts by created_at range
    When I visit the "Home Page"
    And I set the "User ID" to "88"
    And I set the "Item ID" to "999"
    And I set the "Item Description" to "Today Widget"
    And I set the "Item Price" to "19.99"
    And I set the "Item Quantity" to "1"
    And I press the "Create" button
    And I press the "Clear" button
    And I set the "Created At Range" to "2000-01-01,2300-12-31"
    And I press the "Search" button
    Then I should see "Today Widget" in the results

Scenario: Filter shopcarts by price and quantity range
    When I visit the "Home Page"
    And I press the "Search User" button
    Then I should see the message "User ID is required to search user cart."

Scenario: Filter shopcarts by price and quantity range
    When I visit the "Home Page"
    And I set the "User Id" to "3"
    And I set the "Price Range" to "10,40"
    And I set the "Quantity Range" to "1,3"
    And I press the "Search User" button
    Then I should see "Fancy Accessory" in the results
    But I should not see "Standard Supply" in the results

Scenario: Filter shopcarts by price greater than 30
    When I visit the "Home Page"
    And I set the "User Id" to "1" 
    And I set the "Item Price" to "~gt~20"
    And I press the "Search User" button
    Then I should see "Premium Gadget" in the results
    But I should not see "Deluxe Widget" in the results

Scenario: Filter shopcarts with min-price and max-price range
    When I visit the "Home Page"
    And I set the "User Id" to "1"
    And I set the "Min Price" to "10"
    And I set the "Max Price" to "20"
    And I press the "Search User" button
    Then I should see "Deluxe Widget" in the results
    But I should not see "Premium Gadget" in the results

Scenario: Return error for invalid min-price
    When I visit the "Home Page"
    And I set the "User Id" to "1"
    And I set the "Max Price" to "expensive"
    And I press the "Search User" button
    Then I should see the message "Server error!"

Scenario: Update the quantity of an item in the user's cart via the UI
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I set the "Item ID" to "101"
    And I set the "Item Quantity" to "5"
    And I press the "Update" button
    Then I should see the message "Item updated successfully!"
    When I set the "User ID" to "1"
    And I press the "Retrieve" button
    Then I should see "5" in the results

Scenario: Cannot update an item without providing a User ID
    When I visit the "Home Page"
    And I set the "Item ID" to "101"
    And I set the "Item Quantity" to "5"
    And I press the "Update" button
    Then I should see the message "User ID is required to update an item."

Scenario: Cannot update an item without providing an Item ID
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I set the "Item Quantity" to "5"
    And I press the "Update" button
    Then I should see the message "Item ID is required to update an item."

Scenario: Updating a non-existent item should return an error
    When I visit the "Home Page"
    And I set the "User ID" to "999"
    And I set the "Item ID" to "999"
    And I set the "Item Quantity" to "5"
    And I press the "Update" button
    Then I should see the message "Item 999 not found in user 999's cart"

Scenario: Retrieve a user's shopcart via the UI
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I press the "Retrieve" button
    Then I should see the message "Shopcart retrieved successfully!"
    And I should see "Deluxe Widget" in the results
    And I should see "Premium Gadget" in the results
    And I should see "19.99" in the results
    And I should see "29.99" in the results
    And I should not see "Basic Tool" in the results

Scenario: Retrieve a specific item's details from a shopcart
    When I visit the "Home Page"
    And I set the "User ID" to "2"
    And I press the "Retrieve" button
    Then I should see the message "Shopcart retrieved successfully!"
    And I should see "Basic Tool" in the results
    And I should see "9.99" in the results
    And I should see "3" in the results
    When I set the "Item ID" to "201"
    Then I should see "Basic Tool" in the "Item Description" field
    And I should see "9.99" in the "Item Price" field
    And I should see "3" in the "Item Quantity" field

Scenario: Retrieve a non-existent user's shopcart
    When I visit the "Home Page"
    And I set the "User ID" to "999"
    And I press the "Retrieve" button
    Then I should see the message "Shopcart not found for this user."

Scenario: Get all items for a specific user's shopcart
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I press the "Get Items" button
    Then I should see the message "Items retrieved successfully!"
    And I should see "Deluxe Widget" in the results
    And I should see "Premium Gadget" in the results
    But I should not see "Basic Tool" in the results

Scenario: Get a specific item from a user's shopcart
    When I visit the "Home Page"
    And I set the "User ID" to "2"
    And I set the "Item ID" to "201"
    And I press the "Get Item" button
    Then I should see the message "Item retrieved successfully!"
    And I should see "Basic Tool" in the "Item Description" field
    And I should see "9.99" in the "Item Price" field
    And I should see "3" in the "Item Quantity" field

Scenario: Cannot get items without providing a User ID
    When I visit the "Home Page"
    And I press the "Get Items" button
    Then I should see the message "User ID is required to get items."

Scenario: Cannot get a specific item without providing a User ID
    When I visit the "Home Page"
    And I set the "Item ID" to "101"
    And I press the "Get Item" button
    Then I should see the message "User ID is required to get an item."

Scenario: Cannot get a specific item without providing an Item ID
    When I visit the "Home Page"
    And I set the "User ID" to "1"
    And I press the "Get Item" button
    Then I should see the message "Item ID is required to get an item."