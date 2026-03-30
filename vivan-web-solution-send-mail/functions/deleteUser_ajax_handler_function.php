<?php 

add_action("wp_ajax_delete_user", "deleteUser_ajax_handler_function");
add_action("wp_ajax_nopriv_delete_user", "deleteUser_ajax_handler_function");
function deleteUser_ajax_handler_function()
{
    if (isset($_POST["action"]) && $_POST["action"] === "delete_user") {
        $ids = $_POST["data"]["id"]; // Get the comma-separated string of IDs
        // Convert the comma-separated string of IDs to an array
        $id_array = explode(",", $ids);
        // Sanitize each ID in the array to prevent SQL injection
        $sanitized_ids = array_map("absint", $id_array);
        global $wpdb;
        $table_name = $wpdb->prefix . "send_email";
        // Prepare the placeholders for the IN clause based on the number of IDs
        $placeholders = array_fill(0, count($sanitized_ids), "%d");
        $in_clause = "(" . implode(",", $placeholders) . ")";
        // Use prepare() to safely insert the sanitized IDs in the query
        $query = $wpdb->prepare(
            "DELETE FROM $table_name WHERE id IN $in_clause",
            $sanitized_ids
        );
        // Execute the query
        $wpdb->query($query);
        $msg = ["msg" => "records are successfully deleted"];
        echo json_encode($msg);
        wp_die();
    }
}