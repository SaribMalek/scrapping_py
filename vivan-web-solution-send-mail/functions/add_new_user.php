<?php
function add_new_user()
{
    if (isset($_POST["action"]) && $_POST["action"] === "add_user") {
        // Sanitize the data received from the AJAX request
        $name = sanitize_text_field($_POST["name"]);
        $type = sanitize_text_field($_POST["type"]);
        $email = sanitize_email($_POST["email"]); // Use sanitize_email() for email field
        $id = isset($_POST["id"]) ? intval($_POST["id"]) : 0; // Convert id to integer
        global $wpdb;
        $table_name = $wpdb->prefix . "send_email";
        // Check if the email already exists for a different user
        $existing_user = $wpdb->get_row(
            $wpdb->prepare(
                "SELECT * FROM $table_name WHERE email = %s AND id != %d",
                $email,
                $id
            )
        );
        if ($existing_user) {
            // Email already exists for a different user, return a response indicating the failure
            $response = [
                "success" => false,
                "message" => "User with this email already exists",
            ];
        } elseif (empty($id)) {
            // Insert a new record
            $data_to_insert = [
                "name" => $name,
                "type" => $type,
                "email" => $email,
            ];
            $wpdb->insert($table_name, $data_to_insert);
            // Return a response indicating successful insertion
            $response = [
                "success" => true,
                "message" => "User data inserted successfully",
            ];
        } else {
            // Update the existing record with the given id
            $data_to_update = [
                "name" => $name,
                "type" => $type,
                "email" => $email,
            ];
            $where = ["id" => $id];
            $wpdb->update(
                $table_name,
                $data_to_update,
                $where,
                $format = null,
                $where_format = null
            );
            // Return a response indicating successful update
            $response = [
                "success" => true,
                "message" => "User data updated successfully",
            ];
        }
        wp_send_json($response); // Send JSON response
    }
}

add_action("wp_ajax_add_user", "add_new_user"); // For logged-in users
add_action("wp_ajax_nopriv_add_user", "add_new_user"); // For non-logged-in users