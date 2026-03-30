<?php

function upload_csv_file(){
  
  if ($_SERVER["REQUEST_METHOD"] == "POST" && isset($_FILES["csv_file"])) {
    $file = $_FILES["csv_file"];

    // Check if the uploaded file is a CSV
    $file_extension = pathinfo($file["name"], PATHINFO_EXTENSION);
    if (strtolower($file_extension) === 'csv') {
        $file_tmp_name = $file["tmp_name"];

        // Read the CSV file
        $handle = fopen($file_tmp_name, "r");

        // Skip the header row if it exists
        $header = fgetcsv($handle);

        // Prepare the database query
        global $wpdb;
        $table_name = $wpdb->prefix . "send_email"; // Adjust the table name as needed

        // Loop through the CSV data and insert or update records
        $count = 0;
        $response_data = array();
        while (($data = fgetcsv($handle)) !== false) {
            
            $name = $data[1];
            $type = $data[2];
            $email = $data[3];
            $email = str_replace("Â", "", $email);
            $email = str_replace(" ", "", $email);
            $email = str_replace("(at)", "@", $email);
            $email = str_replace("(dot)", ".", $email);
            $email = str_replace("[at]", "@", $email);
            $email = str_replace("(a)", "@", $email);
            $email = str_replace("#", "@", $email);
            $email = str_replace(" ", "", $email);
            // Check if the email already exists in the database
            $existing_record = $wpdb->get_row(
                $wpdb->prepare("SELECT * FROM $table_name WHERE email = %s", $email)
            );

            if ($existing_record) {
                // Email already exists, update the record
                $wpdb->update(
                    $table_name,
                    array(
                        'name' => $name,
                        'type' => $type,
                    ),
                    array('email' => $email)
                );
            } else {
                // Email does not exist, insert a new record
                $wpdb->insert(
                    $table_name,
                    array(
                       
                        'name' => $name,
                        'type' => $type,
                        'email' => $email,
                    )
                );
            }
            $count++;
            $response_data['count'] = $count;

        }

        // Close the CSV file
        fclose($handle);

        // Provide a response indicating success
        echo "CSV data has been successfully imported into the database.";

        echo json_encode($response_data);
        wp_die();
    } else {
        echo "Only CSV files are allowed.";
    }
} else {
    echo "Invalid request.";
}

  
}
add_action("wp_ajax_upload_csv_file", "upload_csv_file"); // For logged-in users
add_action("wp_ajax_nopriv_upload_csv_file", "upload_csv_file"); // For non-logged-in users