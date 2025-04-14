$(function () {

    // ****************************************
    //  U T I L I T Y   F U N C T I O N S
    // ****************************************

    // Updates the form with data from the response
    function update_form_data(res) {
        $("#shopcart_user_id").val(res.user_id);
        $("#shopcart_item_id").val(res.item_id);
        $("#shopcart_item_description").val(res.description);
        $("#shopcart_item_price").val(res.price);
        $("#shopcart_item_quantity").val(res.quantity);
        $("#shopcart_item_created_at").val(res.created_at);
    }

    /// Clears all form fields
    function clear_form_data() {
        $("#shopcart_user_id").val("");
        $("#shopcart_item_id").val("");
        $("#shopcart_item_description").val("");
        $("#shopcart_item_price").val("");
        $("#shopcart_item_quantity").val("");
        $("#shopcart_item_stock").val("");
        $("#shopcart_item_purchase_limit").val("");
        $("#shopcart_item_created_at").val("");
        $("#shopcart_price_range").val("");
        $("#shopcart_quantity_range").val("");
        $("#shopcart_min_price").val("");
        $("#shopcart_max_price").val("");
        $("#shopcart_created_at_range").val("");
    }
    

    // Updates the flash message area
    function flash_message(message) {
        $("#flash_message").empty();
        $("#flash_message").append(message);
    }

    // ****************************************
    // Check API Health Status
    // ****************************************
    
    function check_health() {
        let ajax = $.ajax({
            type: "GET",
            url: "/health",
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res){
            $("#shopcart_health_status").html('<span class="text-success">✓ API Online</span>');
            console.log("Health check passed: " + JSON.stringify(res));
        });

        ajax.fail(function(){
            $("#shopcart_health_status").html('<span class="text-danger">✗ API Offline</span>');
            console.log("Health check failed");
        });
    }

    // Check health when page loads
    check_health();

    // ****************************************
    // List All
    // ****************************************

    $("#list-btn").click(function () {
        $("#flash_message").empty();
    
        let ajax = $.ajax({
            type: "GET",
            url: "/api/shopcarts",
            contentType: "application/json",
            data: ""
        });
    
        ajax.done(function(res) {
            // Use the new formatSearchResults function
            let table = formatSearchResults(res);
            $("#search_results").html(table);
            
            // Add click handlers to rows
            addItemClickHandlers();
            
            flash_message("List results found!");
        });
    
        ajax.fail(function(res){
            flash_message(res.responseJSON?.error || "Server error!");
        });
    });
    

    // ****************************************
    // Create / Add Item to Cart
    // ****************************************

    $("#create-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        let item_id = $("#shopcart_item_id").val();
        let description = $("#shopcart_item_description").val();
        let price = $("#shopcart_item_price").val();
        let quantity = $("#shopcart_item_quantity").val();

        let data = {
            "item_id": parseInt(item_id),
            "description": description,
            "price": parseFloat(price),
            "quantity": parseInt(quantity)
        };

        $("#flash_message").empty();
        
        let ajax = $.ajax({
            type: "POST",
            url: `/api/shopcarts/${user_id}`,
            contentType: "application/json",
            data: JSON.stringify(data),
        });

        ajax.done(function(res){
            if (res.length > 0) {
                // Find the item we just added
                let added_item = res.find(item => item.item_id == item_id);
                if (added_item) {
                    update_form_data(added_item);
                }
            }
            flash_message("Item successfully added to cart!");
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.error || "Server error!");
        });
    });

    $("#create_item-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        let product_id = $("#shopcart_item_id").val();
        let name = $("#shopcart_item_description").val();
        let price = $("#shopcart_item_price").val();
        let quantity = $("#shopcart_item_quantity").val();
        let stock = $("#shopcart_item_stock").val();
        let purchase_limit = $("#shopcart_item_purchase_limit").val();
    
        let data = {
            "product_id": parseInt(product_id),
            "name": name,
            "price": parseFloat(price),
            "quantity": parseInt(quantity),
            "stock": parseInt(stock),
            "purchase_limit": parseInt(purchase_limit)
        };
    
        $("#flash_message").empty();
    
        let ajax = $.ajax({
            type: "POST",
            url: `/api/shopcarts/${user_id}/items`,
            contentType: "application/json",
            data: JSON.stringify(data)
        });
    
        ajax.done(function(res){
            flash_message("Product added from items!");
            if (res.length > 0) {
                update_form_data(res[0]);
            }
        });
    
        ajax.fail(function(res){
            flash_message(res.responseJSON?.error || "Server error!");
        });
    });
    

    // ****************************************
    // Update an Item in Cart
    // ****************************************

    $("#update-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        let item_id = $("#shopcart_item_id").val();
        let quantity = $("#shopcart_item_quantity").val();

        let data = {
            "quantity": parseInt(quantity)
        };

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "PUT",
            url: `/api/shopcarts/${user_id}/items/${item_id}`,
            contentType: "application/json",
            data: JSON.stringify(data)
        });

        ajax.done(function(res){
            if (res.message) {
                // Item was removed (quantity set to 0)
                clear_form_data();
                flash_message(res.message);
            } else {
                update_form_data(res);
                flash_message("Item updated successfully!");
            }
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.error || "Server error!");
        });
    });

    // ****************************************
    // Delete an Item from Cart
    // ****************************************

    $("#delete_item-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        let item_id = $("#shopcart_item_id").val();

        if (!user_id) {
            flash_message("User ID is required to delete an item.");
            return;
        }

        if (!item_id) {
            flash_message("Item ID is required to delete an item.");
            return;
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/api/shopcarts/${user_id}/items/${item_id}`,
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res){
            clear_form_data();
            flash_message("Item has been deleted from the cart!");
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON?.error || "Server error!");
        });
    });

    // ****************************************
    // Retrieve a Shopcart
    // ****************************************

    $("#retrieve-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        
        if (!user_id) {
            flash_message("User ID is required to retrieve a shopcart");
            return;
        }
        
        $("#flash_message").empty();
        
        let ajax = $.ajax({
            type: "GET",
            url: `/shopcarts/${user_id}`, // Note: Don't use /api prefix yet
            contentType: "application/json"
        });
        
        ajax.done(function(res) {
            // Display the results
            let table = formatSearchResults(res);
            $("#search_results").html(table);
            
            // Add click event to the rows
            addItemClickHandlers();
            
            flash_message("Shopcart retrieved successfully!");
        });
        
        ajax.fail(function(res) {
            clear_form_data();
            flash_message(res.responseJSON.error || "Shopcart not found for this user.");
        });
    });

    // ****************************************
    // Retrieve All Items from a User's Shopcart
    // ****************************************

    $("#retrieve_items-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        
        if (!user_id) {
            flash_message("User ID is required to retrieve items");
            return;
        }
        
        $("#flash_message").empty();
        
        let ajax = $.ajax({
            type: "GET",
            url: `/shopcarts/${user_id}/items`,
            contentType: "application/json"
        });
        
        ajax.done(function(res) {
            // Display the results
            let table = formatSearchResults(res);
            $("#search_results").html(table);
            
            // Add click event to the rows
            addItemClickHandlers();
            
            flash_message("Items retrieved successfully!");
        });
        
        ajax.fail(function(res) {
            clear_form_data();
            flash_message(res.responseJSON.error || "Failed to retrieve items");
        });
    });

    // ****************************************
    // Retrieve a Specific Item from a User's Shopcart
    // ****************************************

    $("#retrieve_item-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        let item_id = $("#shopcart_item_id").val();
        
        if (!user_id) {
            flash_message("User ID is required to retrieve an item");
            return;
        }
        
        if (!item_id) {
            flash_message("Item ID is required to retrieve an item");
            return;
        }
        
        $("#flash_message").empty();
        
        let ajax = $.ajax({
            type: "GET",
            url: `/shopcarts/${user_id}/items/${item_id}`,
            contentType: "application/json"
        });
        
        ajax.done(function(res) {
            // Update the form fields with this item's details
            update_form_data(res);
            flash_message("Item retrieved successfully!");
        });
        
        ajax.fail(function(res) {
            clear_form_data();
            flash_message(res.responseJSON.error || "Item not found");
        });
    });

    // ****************************************
    // Delete a Shopcart
    // ****************************************

    $("#delete-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "DELETE",
            url: `/api/shopcarts/${user_id}`,
            contentType: "application/json",
            data: '',
        });

        ajax.done(function(res){
            clear_form_data();
            $("#search_results").empty();
            flash_message("Shopcart has been deleted!");
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.error || "Server error!");
        });
    });

    // ****************************************
    // Clear the form
    // ****************************************

    $("#clear-btn").click(function () {
        $("#shopcart_shopcart_user_id").val("");
        clear_form_data();
        $("#flash_message").empty();
    });

    // ****************************************
    // Search for Shopcarts
    // ****************************************

    $("#search-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        let item_id = $("#shopcart_item_id").val();
        let price = $("#shopcart_item_price").val();
        let quantity = $("#shopcart_item_quantity").val();

        let price_range = $("#shopcart_price_range").val();
        let quantity_range = $("#shopcart_quantity_range").val();
        let min_price = $("#shopcart_min_price").val();
        let max_price = $("#shopcart_max_price").val();
        let created_at_range = $("#shopcart_created_at_range").val();

        let queryString = "";

        if (user_id) {
            queryString += 'user_id=' + user_id;
        }
        
        if (item_id) {
            if (queryString.length > 0) {
                queryString += '&item_id=' + item_id;
            } else {
                queryString += 'item_id=' + item_id;
            }
        }
        
        if (price) {
            if (queryString.length > 0) {
                queryString += '&price=' + price;
            } else {
                queryString += 'price=' + price;
            }
        }
        
        if (quantity) {
            if (queryString.length > 0) {
                queryString += '&quantity=' + quantity;
            } else {
                queryString += 'quantity=' + quantity;
            }
        }

        if (price_range) {
            if (queryString.length > 0) {
                queryString += '&price_range=' + price_range;
            } else {
                queryString += 'price_range=' + price_range;
            }
        }
        
        if (quantity_range) {
            if (queryString.length > 0) {
                queryString += '&quantity_range=' + quantity_range;
            } else {
                queryString += 'quantity_range=' + quantity_range;
            }
        }
        
        if (min_price) {
            if (queryString.length > 0) {
                queryString += '&min-price=' + min_price;
            } else {
                queryString += 'min-price=' + min_price;
            }
        }
        
        if (max_price) {
            if (queryString.length > 0) {
                queryString += '&max-price=' + max_price;
            } else {
                queryString += 'max-price=' + max_price;
            }
        }
        
        if (created_at_range) {
            if (queryString.length > 0) {
                queryString += '&created_at_range=' + created_at_range;
            } else {
                queryString += 'created_at_range=' + created_at_range;
            }
        }
        

        $("#flash_message").empty();

        // Default search URL if no queryString
        let searchUrl = "/api/shopcarts";
        if (queryString.length > 0) {
            searchUrl += "?" + queryString;
        }

        let ajax = $.ajax({
            type: "GET",
            url: searchUrl,
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res) {
            // Use the new formatSearchResults function
            let table = formatSearchResults(res);
            $("#search_results").html(table);
            
            // Add click handlers to rows
            addItemClickHandlers();
            
            flash_message("Search results found!");
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.error || "Server error!");
        });
    });

    $("#search_user-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        let item_id = $("#shopcart_item_id").val();
        let price = $("#shopcart_item_price").val();
        let quantity = $("#shopcart_item_quantity").val();

        let price_range = $("#shopcart_price_range").val();
        let quantity_range = $("#shopcart_quantity_range").val();
        let min_price = $("#shopcart_min_price").val();
        let max_price = $("#shopcart_max_price").val();
        let created_at_range = $("#shopcart_created_at_range").val();

        let queryString = "";

        if (!user_id) {
            flash_message("User ID is required to search user cart.");
            return;
        }
        
        if (item_id) {
            if (queryString.length > 0) {
                queryString += '&item_id=' + item_id;
            } else {
                queryString += 'item_id=' + item_id;
            }
        }
        
        if (price) {
            if (queryString.length > 0) {
                queryString += '&price=' + price;
            } else {
                queryString += 'price=' + price;
            }
        }
        
        if (quantity) {
            if (queryString.length > 0) {
                queryString += '&quantity=' + quantity;
            } else {
                queryString += 'quantity=' + quantity;
            }
        }

        if (price_range) {
            if (queryString.length > 0) {
                queryString += '&price_range=' + price_range;
            } else {
                queryString += 'price_range=' + price_range;
            }
        }
        
        if (quantity_range) {
            if (queryString.length > 0) {
                queryString += '&quantity_range=' + quantity_range;
            } else {
                queryString += 'quantity_range=' + quantity_range;
            }
        }
        
        if (min_price) {
            if (queryString.length > 0) {
                queryString += '&min-price=' + min_price;
            } else {
                queryString += 'min-price=' + min_price;
            }
        }
        
        if (max_price) {
            if (queryString.length > 0) {
                queryString += '&max-price=' + max_price;
            } else {
                queryString += 'max-price=' + max_price;
            }
        }
        
        if (created_at_range) {
            if (queryString.length > 0) {
                queryString += '&created_at_range=' + created_at_range;
            } else {
                queryString += 'created_at_range=' + created_at_range;
            }
        }
        

        $("#flash_message").empty();

        // Default search URL if no queryString
        let searchUrl = `/api/shopcarts/${user_id}`;
        if (queryString.length > 0) {
            searchUrl += "?" + queryString;
        }

        let ajax = $.ajax({
            type: "GET",
            url: searchUrl,
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res){
            display_search_results(res);
        });

        ajax.fail(function(res){
            flash_message(res.responseJSON.error || "Server error!");
        });
    });

    // ****************************************
    // Checkout for Shopcarts
    // ****************************************

    $("#checkout-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
    
        $("#flash_message").empty();
    
        let ajax = $.ajax({
            type: "POST",
            url: `/api/shopcarts/${user_id}/checkout`,
            contentType: "application/json",
            data: "",
        });
    
        ajax.done(function (res) {
            flash_message(`${res.message} Total: $${res.total_price.toFixed(2)}`);
        });
    
        ajax.fail(function (res) {
            flash_message(res.responseJSON?.error || "Server error!");
        });
    });

    // ****************************************
    // For search results rendering
    // ****************************************

    function display_search_results(res) {
        let table = '<table class="table table-striped" cellpadding="10">';
        table += '<thead><tr>';
        table += '<th class="col-md-2">User ID</th>';
        table += '<th class="col-md-2">Item ID</th>';
        table += '<th class="col-md-4">Description</th>';
        table += '<th class="col-md-2">Quantity</th>';
        table += '<th class="col-md-2">Price</th>';
        table += '</tr></thead><tbody>';
        
        // Add id attribute to each row for making items clickable
        res.forEach((cart) => {
            cart.items.forEach((item) => {
                table += `<tr id="item_${item.item_id}" class="item-row" data-id="${item.item_id}" data-user-id="${item.user_id}">
                    <td>${item.user_id}</td>
                    <td>${item.item_id}</td>
                    <td>${item.description}</td>
                    <td>${item.quantity}</td>
                    <td>${item.price}</td>
                </tr>`;
            });
        });
        
        table += '</tbody></table>';
        $("#search_results").html(table);
        
        // Add click handlers to the rows
        $(".item-row").click(function() {
            let itemId = $(this).data("id");
            let userId = $(this).data("user-id");
            get_item_details(userId, itemId);
        });
    }

    // ****************************************
    // Function to get item details when clicked
    // ****************************************

    function get_item_details(userId, itemId) {
        $.ajax({
            type: "GET",
            url: `/shopcarts/${userId}/items/${itemId}`,
            contentType: "application/json",
            success: function(res) {
                // Fill in the form with item details
                update_form_data(res);
                flash_message("Item details retrieved!");
            },
            error: function(res) {
                flash_message(res.responseJSON?.error || "Server error!");
            }
        });
    }

    // ****************************************
    // Helper Functions for Search Results
    // ****************************************

    // Function to format search results with clickable rows
    function formatSearchResults(data) {
        let table = '<table class="table table-striped" cellpadding="10">';
        table += '<thead><tr>';
        table += '<th class="col-md-2">User ID</th>';
        table += '<th class="col-md-2">Item ID</th>';
        table += '<th class="col-md-4">Description</th>';
        table += '<th class="col-md-2">Quantity</th>';
        table += '<th class="col-md-2">Price</th>';
        table += '</tr></thead><tbody>';
        
        // Process the result data based on its structure
        if (Array.isArray(data)) {
            // Handle array of items or shopcarts
            data.forEach((item) => {
                if (item.items) {
                    // This is a shopcart with items
                    item.items.forEach((cartItem) => {
                        table += formatItemRow(cartItem);
                    });
                } else {
                    // This is a single item
                    table += formatItemRow(item);
                }
            });
        } else if (data.items) {
            // Handle single shopcart with items
            data.items.forEach((item) => {
                table += formatItemRow(item);
            });
        } else {
            // Handle single item
            table += formatItemRow(data);
        }
        
        table += '</tbody></table>';
        return table;
    }

    // Format a single item row
    function formatItemRow(item) {
        return `<tr id="item_${item.item_id}" class="item-row" data-id="${item.item_id}" data-user-id="${item.user_id}">
            <td>${item.user_id}</td>
            <td>${item.item_id}</td>
            <td>${item.description}</td>
            <td>${item.quantity}</td>
            <td>${item.price}</td>
        </tr>`;
    }

    // Add click handlers to item rows
    function addItemClickHandlers() {
        $(".item-row").click(function() {
            let itemId = $(this).data("id");
            let userId = $(this).data("user-id");
            
            // Get the item details
            $.ajax({
                type: "GET",
                url: `/shopcarts/${userId}/items/${itemId}`,
                contentType: "application/json",
                success: function(res) {
                    update_form_data(res);
                    flash_message("Item details retrieved!");
                },
                error: function(res) {
                    flash_message(res.responseJSON?.error || "Error retrieving item details");
                }
            });
        });
    }
    
});
