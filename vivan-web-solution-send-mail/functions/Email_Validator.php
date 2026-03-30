<?php

add_action("wp_ajax_validateEmails", "validateEmails_ajax_handler_function");
add_action("wp_ajax_nopriv_validateEmails", "validateEmails_ajax_handler_function");
function validateEmails_ajax_handler_function()
{
    if ($_POST['action'] == 'validateEmails') {
        $api_key = get_option('custom_send_mail_api_key');
        if (empty($api_key)) {
            wp_send_json_error(array('api_not_found' => 'Please add the QuickEmailVerification API key in settings.'));
            wp_die(); // Terminate the script
        }
        $url = 'https://api.quickemailverification.com/v1/verify';

        $Emails = $_POST['data']['emails'];
        // It's better to trim and sanitize input data to remove any leading/trailing spaces and ensure it's safe to use in the URL.
        $Emails = str_replace(" ", "", $Emails);
        $Emails = str_replace("(at)", "@", $Emails);
        $Emails = str_replace("(dot)", ".", $Emails);
        $Emails = str_replace("[at]", "@", $Emails);
        $Emails = str_replace("(a)", "@", $Emails);
        $Emails = str_replace("#", "@", $Emails);
        $Emails = str_replace(" ", "", $Emails);
        $Emails = trim($Emails);
        $Emails = trim($Emails);
        $Emails = str_replace(" ", "", $Emails);
        $to_emails = explode(',', $Emails);

        global $wpdb;
        $failed_emails = [];

        foreach ($to_emails as $email) {
            $to = trim($email);
            $validation_url = "{$url}?email={$to}&apikey={$api_key}";

            // Initialize cURL to make an API request
            $ch = curl_init($validation_url);

            // Set cURL options
            curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
            
            // Execute the cURL request
            $response = curl_exec($ch);

            // Check for cURL errors
            if (curl_errno($ch)) {
                // Handle cURL error here
                echo '<div class="notice notice-error is-dismissible"><p>cURL error: ' . curl_error($ch) . '</p></div>';
            }

            // Close the cURL session
            curl_close($ch);

            // Parse the JSON response
            $json_response = json_decode($response, true);

            if ($json_response['result'] == 'valid') {
                $wpdb->update(
                    $wpdb->prefix . 'send_email',
                    array('is_verified' => 1),
                    array('email' => $to)
                );
            } else if ($json_response['result'] == 'invalid') {
                echo '<div class="notice notice-error is-dismissible"><p>Email validation failed for: ' .
                    $to .
                    "</p></div>";

                $failed_emails[] = $to;
                $wpdb->delete($wpdb->prefix . 'send_email', array('email' => $to));

                $valid_mails = ["msg" => "Delete All Invalid Mails"];
                echo json_encode($valid_mails);
            } else if($json_response['result'] == 'unknown'){
                $wpdb->update(
                    $wpdb->prefix . 'send_email',
                    array('is_verified' => 2),
                    array('email' => $to)
                );
            } else {
                //var_dump($json_response);
                wp_send_json_error(array('api_rate_limit' => 'API rate limit exceeded for today. Please try again later.'));
                
                wp_die(); // Terminate the script
            }
        }

        $log_file_path = dirname(plugin_dir_path(__FILE__)) . '/failed_emails.json'; // Path to your JSON file in the parent folder

if (!empty($failed_emails)) {
    $date = date('Y-m-d'); // Get the current date in YYYY-MM-DD format

    // Load existing JSON data if the file exists
    $existing_data = [];
    if (file_exists($log_file_path)) {
        $existing_data = json_decode(file_get_contents($log_file_path), true);
    }

    // Check if there is already data for today's date
    $today_data = null;
    foreach ($existing_data as $key => $data) {
        if ($data['date'] === $date) {
            $today_data = &$existing_data[$key];
            break;
        }
    }

    // If there is no data for today, create a new structure
    if ($today_data === null) {
        $today_data = [
            'date' => $date,
            'failed_emails' => []
        ];
        $existing_data[] = $today_data;
    }

    // Add the new failed emails to today's data
    $today_data['failed_emails'] = array_merge($today_data['failed_emails'], $failed_emails);

    // Encode the updated data as JSON
    $updated_data = json_encode($existing_data);

    // Write the updated data to the JSON file
    if (file_put_contents($log_file_path, $updated_data . PHP_EOL) === false) {
        echo '<div class="notice notice-error is-dismissible"><p>Error writing to JSON file</p></div>';
    }
}

    }
}
