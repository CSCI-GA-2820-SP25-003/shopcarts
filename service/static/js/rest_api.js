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
    
        ajax.done(function(res){
            $("#search_results").empty();
            let table = '<table class="table table-striped">';
            table += '<thead><tr>';
            table += '<th class="col-md-1">User ID</th>';
            table += '<th class="col-md-2">Item ID</th>';
            table += '<th class="col-md-4">Description</th>';
            table += '<th class="col-md-2">Price</th>';
            table += '<th class="col-md-1">Quantity</th>';
            table += '<th class="col-md-2">Created At</th>';
            table += '</tr></thead><tbody>';

            // Flatten items from all carts
            let items = [];
            for (let cart of res) {
                for (let item of cart.items) {
                    items.push(item);
                }
            }

            let firstItem = null;
            for(let i = 0; i < items.length; i++) {
                let item = items[i];
                table += `<tr id="row_${i}">
                    <td>${item.user_id}</td>
                    <td>${item.item_id}</td>
                    <td>${item.description}</td>
                    <td>${item.price.toFixed(2)}</td>
                    <td>${item.quantity}</td>
                    <td>${item.created_at}</td>
                </tr>`;
                if (i == 0) {
                    firstItem = item;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // Make table rows clickable to populate the form with the selected item
            $("#search_results tbody").off("click", "tr");  // Remove any existing handlers
            $("#search_results tbody").on("click", "tr", function() {
                let index = $(this).attr('id').split('_')[1];
                let item = items[parseInt(index)];
                update_form_data(item);
                
                // Highlight the selected row
                $("#search_results tbody tr").removeClass("info");
                $(this).addClass("info");
                
                // Flash a message about the selected item
                flash_message(`Selected item ${item.item_id}: ${item.description}`);
            });

            // Copy the first result to the form
            if (firstItem) {
                update_form_data(firstItem);
                flash_message("All shopcarts listed.");
            } else {
                flash_message("No items found matching the search criteria.");
            }
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

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/api/shopcarts/${user_id}`,
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res){
            // Display the cart items in the search results table
            $("#search_results").empty();
            let table = '<table class="table table-striped">';
            table += '<thead><tr>';
            table += '<th class="col-md-1">User ID</th>';
            table += '<th class="col-md-2">Item ID</th>';
            table += '<th class="col-md-4">Description</th>';
            table += '<th class="col-md-2">Price</th>';
            table += '<th class="col-md-1">Quantity</th>';
            table += '<th class="col-md-2">Created At</th>';
            table += '</tr></thead><tbody>';

            // Flatten items from all carts
            let items = [];
            for (let cart of res) {
                for (let item of cart.items) {
                    items.push(item);
                }
            }

            let firstItem = null;
            for(let i = 0; i < items.length; i++) {
                let item = items[i];
                table += `<tr id="row_${i}">
                    <td>${item.user_id}</td>
                    <td>${item.item_id}</td>
                    <td>${item.description}</td>
                    <td>${item.price.toFixed(2)}</td>
                    <td>${item.quantity}</td>
                    <td>${item.created_at}</td>
                </tr>`;
                if (i == 0) {
                    firstItem = item;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // Make table rows clickable to populate the form with the selected item
            $("#search_results tbody").off("click", "tr");  // Remove any existing handlers
            $("#search_results tbody").on("click", "tr", function() {
                let index = $(this).attr('id').split('_')[1];
                let item = items[parseInt(index)];
                update_form_data(item);
                
                // Highlight the selected row
                $("#search_results tbody tr").removeClass("info");
                $(this).addClass("info");
                
                // Flash a message about the selected item
                flash_message(`Selected item ${item.item_id}: ${item.description}`);
            });

            // Copy the first result to the form
            if (firstItem) {
                update_form_data(firstItem);
                flash_message("Shopcart retrieved successfully!");
            } else {
                flash_message("No items found in shopcart.");
            }
        });

        ajax.fail(function(res){
            clear_form_data();
            if (res.status == 404) {
                flash_message("Shopcart not found for this user.");
            } else {
                flash_message(res.responseJSON.error || "Server error!");
            }
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

        ajax.done(function(res){
            $("#search_results").empty();
            let table = '<table class="table table-striped">';
            table += '<thead><tr>';
            table += '<th class="col-md-1">User ID</th>';
            table += '<th class="col-md-2">Item ID</th>';
            table += '<th class="col-md-4">Description</th>';
            table += '<th class="col-md-2">Price</th>';
            table += '<th class="col-md-1">Quantity</th>';
            table += '<th class="col-md-2">Created At</th>';
            table += '</tr></thead><tbody>';

            // Flatten items from all carts
            let items = [];
            for (let cart of res) {
                for (let item of cart.items) {
                    items.push(item);
                }
            }

            let firstItem = null;
            for(let i = 0; i < items.length; i++) {
                let item = items[i];
                table += `<tr id="row_${i}">
                    <td>${item.user_id}</td>
                    <td>${item.item_id}</td>
                    <td>${item.description}</td>
                    <td>${item.price.toFixed(2)}</td>
                    <td>${item.quantity}</td>
                    <td>${item.created_at}</td>
                </tr>`;
                if (i == 0) {
                    firstItem = item;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // Make table rows clickable to populate the form with the selected item
            $("#search_results tbody").off("click", "tr");  // Remove any existing handlers
            $("#search_results tbody").on("click", "tr", function() {
                let index = $(this).attr('id').split('_')[1];
                let item = items[parseInt(index)];
                update_form_data(item);
                
                // Highlight the selected row
                $("#search_results tbody tr").removeClass("info");
                $(this).addClass("info");
                
                // Flash a message about the selected item
                flash_message(`Selected item ${item.item_id}: ${item.description}`);
            });

            // Copy the first result to the form
            if (firstItem) {
                update_form_data(firstItem);
                flash_message("Search results found!");
            } else {
                flash_message("No items found matching the search criteria.");
            }
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
            $("#search_results").empty();
            let table = '<table class="table table-striped">';
            table += '<thead><tr>';
            table += '<th class="col-md-1">User ID</th>';
            table += '<th class="col-md-2">Item ID</th>';
            table += '<th class="col-md-4">Description</th>';
            table += '<th class="col-md-2">Price</th>';
            table += '<th class="col-md-1">Quantity</th>';
            table += '<th class="col-md-2">Created At</th>';
            table += '</tr></thead><tbody>';

            // Flatten items from all carts
            let items = [];
            for (let cart of res) {
                for (let item of cart.items) {
                    items.push(item);
                }
            }

            let firstItem = null;
            for(let i = 0; i < items.length; i++) {
                let item = items[i];
                table += `<tr id="row_${i}">
                    <td>${item.user_id}</td>
                    <td>${item.item_id}</td>
                    <td>${item.description}</td>
                    <td>${item.price.toFixed(2)}</td>
                    <td>${item.quantity}</td>
                    <td>${item.created_at}</td>
                </tr>`;
                if (i == 0) {
                    firstItem = item;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // Make table rows clickable to populate the form with the selected item
            $("#search_results tbody").off("click", "tr");  // Remove any existing handlers
            $("#search_results tbody").on("click", "tr", function() {
                let index = $(this).attr('id').split('_')[1];
                let item = items[parseInt(index)];
                update_form_data(item);
                
                // Highlight the selected row
                $("#search_results tbody tr").removeClass("info");
                $(this).addClass("info");
                
                // Flash a message about the selected item
                flash_message(`Selected item ${item.item_id}: ${item.description}`);
            });

            // Copy the first result to the form
            if (firstItem) {
                update_form_data(firstItem);
                flash_message("Search results found!");
            } else {
                flash_message("No items found matching the search criteria.");
            }
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
    // Get All Items for a User
    // ****************************************

    $("#get_items-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();

        if (!user_id) {
            flash_message("User ID is required to get items.");
            return;
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/api/shopcarts/${user_id}/items`,
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res){
            // Display the cart items in the search results table
            $("#search_results").empty();
            let table = '<table class="table table-striped">';
            table += '<thead><tr>';
            table += '<th class="col-md-1">User ID</th>';
            table += '<th class="col-md-2">Item ID</th>';
            table += '<th class="col-md-4">Description</th>';
            table += '<th class="col-md-2">Price</th>';
            table += '<th class="col-md-1">Quantity</th>';
            table += '</tr></thead><tbody>';

            // Flatten items from all carts
            let items = [];
            for (let cart of res) {
                for (let item of cart.items) {
                    items.push(item);
                }
            }

            let firstItem = null;
            for(let i = 0; i < items.length; i++) {
                let item = items[i];
                table += `<tr id="row_${i}">
                    <td>${item.user_id}</td>
                    <td>${item.item_id}</td>
                    <td>${item.description}</td>
                    <td>${item.price.toFixed(2)}</td>
                    <td>${item.quantity}</td>
                </tr>`;
                if (i == 0) {
                    firstItem = item;
                }
            }
            table += '</tbody></table>';
            $("#search_results").append(table);

            // Make table rows clickable
            $("#search_results tbody").off("click", "tr");
            $("#search_results tbody").on("click", "tr", function() {
                let index = $(this).attr('id').split('_')[1];
                let item = items[parseInt(index)];
                update_form_data(item);
                
                // Highlight the selected row
                $("#search_results tbody tr").removeClass("info");
                $(this).addClass("info");
                
                flash_message(`Selected item ${item.item_id}: ${item.description}`);
            });

            if (firstItem) {
                update_form_data(firstItem);
                flash_message("Items retrieved successfully!");
            } else {
                flash_message("No items found for this user.");
            }
        });

        ajax.fail(function(res){
            if (res.status == 404) {
                flash_message("No items found for this user.");
            } else {
                flash_message(res.responseJSON?.error || "Server error!");
            }
        });
    });

    // ****************************************
    // Get a Specific Item
    // ****************************************

    $("#get_item-btn").click(function () {
        let user_id = $("#shopcart_user_id").val();
        let item_id = $("#shopcart_item_id").val();

        if (!user_id) {
            flash_message("User ID is required to get an item.");
            return;
        }

        if (!item_id) {
            flash_message("Item ID is required to get an item.");
            return;
        }

        $("#flash_message").empty();

        let ajax = $.ajax({
            type: "GET",
            url: `/api/shopcarts/${user_id}/items/${item_id}`,
            contentType: "application/json",
            data: ''
        });

        ajax.done(function(res){
            update_form_data(res);
            flash_message("Item retrieved successfully!");
        });

        ajax.fail(function(res){
            if (res.status == 404) {
                if (res.responseJSON?.error?.includes("not found")) {
                    flash_message(`Item ${item_id} not found in user ${user_id}'s cart.`);
                } else {
                    flash_message("No cart found for this user.");
                }
            } else {
                flash_message(res.responseJSON?.error || "Server error!");
            }
        });
    });
    
});
