<?php
// Add this to your WordPress plugin's PHP file
function process_date_selection() {
    if (isset($_POST['selected_date'])) {
        $selected_date = sanitize_text_field($_POST['selected_date']);

        // Get the path to the JSON file
        $json_file_path = dirname(plugin_dir_path(__FILE__)) . '/failed_emails.json';

        // Check if the JSON file exists
        if (file_exists($json_file_path)) {
            // Read the JSON data from the file
            $json_data = file_get_contents($json_file_path);

            // Parse the JSON data into an array
            $email_records = json_decode($json_data, true);

            if ($email_records !== null) {
                // Initialize an array to store filtered data
                $filtered_data = [];

                // Loop through the email records and filter by the selected date
                foreach ($email_records as $record) {
                    if ($record['date'] === $selected_date) {
                        $filtered_data[] = $record;
                    }
                }

                // Send the filtered JSON data as a response
                echo json_encode($filtered_data);
            } else {
                // Handle JSON parsing error
                echo json_encode(['error' => 'Error parsing JSON data.']);
            }
        } else {
            // Handle file not found error
            echo json_encode(['error' => 'JSON file not found.']);
        }
    }

    wp_die(); // Always include this at the end to terminate the AJAX request
}

// Hook the PHP function to the WordPress AJAX action
add_action('wp_ajax_process_date_selection', 'process_date_selection');
add_action('wp_ajax_nopriv_process_date_selection', 'process_date_selection'); // For non-logged-in users
?>
