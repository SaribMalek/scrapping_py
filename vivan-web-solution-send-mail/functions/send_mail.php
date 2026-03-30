<?php


// Add this in your plugin or theme's functions.php
function send_mail_ajax_handler() {
        $to_mails = str_replace(' ', '', $_POST['to']);
        $to_emails = explode(',', $to_mails);
        

        $user_name_multiple = $_POST['user-name-multiple'];
        $to_names_multiple = explode(',', $user_name_multiple);

        $user_id_multiple = $_POST['user-id-multiple'];
        $to_id = explode(',', $user_id_multiple);

        $to_names_single = [$_POST['user-name-single']]; // For single email

        $to_names = count($to_emails) > 1 ? $to_names_multiple : $to_names_single;
        
        $subject_mail = isset($_POST['subject']) ? sanitize_text_field($_POST['subject']) : '';
        $message_mail = stripslashes($_POST['content']);
        $attachments = [];
        if (isset($_FILES['attachment']['name']) && is_array($_FILES['attachment']['name'])) {
            $upload_dir = wp_upload_dir();
            $temp_dir = $upload_dir['basedir'] . '/temp_attachments/';
            if (!is_dir($temp_dir)) {
                wp_mkdir_p($temp_dir);
            }
            foreach ($_FILES['attachment']['name'] as $i => $file_name) {
                $file_name = sanitize_file_name($file_name);
                $temp_file_path = $_FILES['attachment']['tmp_name'][$i];
                $destination = $temp_dir . $file_name;
                move_uploaded_file($temp_file_path, $destination);
                $attachments[] = $destination;
            }
        }
        $combinedData = array_map(function($email, $name, $id) {
            return [
                'email' => $email,
                'name' => $name,
                'id' => $id
            ];
        }, $to_emails, $to_names, $to_id);


        $success = array(); // Initialize a success flag
        $count1=0;
        $countSuccess=0;
        $countFail=0;
        $colors = [
    "#FF5733", "#8E44AD", "#3498DB", "#27AE60", "#F1C40F", "#D35400", "#34495E", "#E74C3C", "#1ABC9C", "#D35400",
    "#2980B9", "#C0392B", "#F39C12", "#884EA0", "#D35400", "#27AE60", "#E74C3C", "#2980B9", "#8E44AD", "#F39C12",
    "#3498DB", "#1ABC9C", "#D35400", "#F1C40F", "#2980B9", "#8E44AD", "#27AE60", "#F39C12", "#C0392B", "#D35400",
    "#3498DB", "#27AE60", "#34495E", "#E74C3C", "#3498DB", "#884EA0", "#F1C40F", "#1ABC9C", "#D35400", "#F39C12",
    "#8E44AD", "#27AE60", "#C0392B", "#34495E", "#2980B9", "#E74C3C", "#1ABC9C", "#D35400", "#F1C40F", "#3498DB",
    "#884EA0", "#27AE60", "#E74C3C", "#8E44AD", "#F39C12", "#34495E", "#3498DB", "#D35400", "#2980B9", "#C0392B",
    "#1ABC9C", "#F1C40F", "#E74C3C", "#27AE60", "#8E44AD", "#34495E", "#F39C12", "#2980B9", "#3498DB", "#D35400",
    "#884EA0", "#C0392B", "#E74C3C", "#1ABC9C", "#F1C40F", "#8E44AD", "#27AE60", "#3498DB", "#34495E", "#F39C12",
    "#2980B9", "#D35400", "#C0392B", "#884EA0", "#1ABC9C", "#E74C3C", "#F1C40F", "#27AE60", "#8E44AD", "#3498DB",
    "#34495E", "#F39C12", "#2980B9", "#D35400", "#C0392B", "#884EA0", "#E74C3C", "#1ABC9C", "#F1C40F", "#27AE60"
];
        foreach ($combinedData as $data) {
            $to = trim($data['email']); 
            $name = $data['name'];
            $id = $data['id'];

            $subject = $subject_mail;
            $message = str_replace('{$dynamic_name}', $name, $message_mail);
            $message = str_replace('{$dynamic_id}', $id, $message);
            $color = array_shift($colors); // Get the next color from the array
            $message = str_replace('{$color}', $color, $message);
            $headers = ["Content-Type: text/html; charset=UTF-8"];
            $result = wp_mail($to, $subject, $message, $headers, $attachments);
            
            if ($result) {
                $success[$count1] = true;
                $countSuccess++;
            }else{
               $success[$count1] = false;
                
               $countFail++;
            }

            if (!function_exists('wp_mail') || $result === false) {
            // Message with a link to connect WP Mail SMTP
            $message = 'Error sending email. Please configure WP Mail SMTP to resolve email sending issues.';
            
            $response = array(
                'message' => $message,
            );
            wp_send_json_error($response);
        } 


            $count1++;
        }
        if ($success) {
            // global $wpdb;
            // $table_name = $wpdb->prefix . "email_template_tracking";
            // $user_ids = array_merge(
            //     isset($_POST["user-id"]) ? [$_POST["user-id"]] : [],
            //     isset($_POST["user-id-multiple"]) ? explode(",", $_POST["user-id-multiple"]) : []
            // );
            // $template_id = isset($_POST["selected-email-template-single"])
            //     ? $_POST["selected-email-template-single"]
            //     : (isset($_POST["selected-email-template-multiple"]) ? $_POST["selected-email-template-multiple"] : 0);
            // $count=0;
            // foreach ($user_ids as $user_id) {
            //     $existing_count = $wpdb->get_var(
            //         $wpdb->prepare(
            //             "SELECT template_count FROM $table_name WHERE user_id = %d AND template_id = %d",
            //             $user_id,
            //             $template_id
            //         )
            //     );
            //     if($success[$count]==true){
            //     if ($existing_count !== null) {
            //         $new_template_count = $existing_count + 1;
            //         $wpdb->update(
            //             $table_name,
            //             ["template_count" => $new_template_count],
            //             ["user_id" => $user_id, "template_id" => $template_id],
            //             ["%d"],
            //             ["%d", "%d"]
            //         );
            //     } else {
            //         $wpdb->insert(
            //             $table_name,
            //             ["user_id" => $user_id, "template_id" => $template_id, "template_count" => 1],
            //             ["%d", "%d", "%d"]
            //         );
            //     }}else{
            //     }
            //     $count++;
            // }
             global $wpdb;
$table_name = $wpdb->prefix . "email_template_tracking";
$user_ids = array_merge(
    isset($_POST["user-id"]) ? [$_POST["user-id"]] : [],
    isset($_POST["user-id-multiple"]) ? explode(",", $_POST["user-id-multiple"]) : []
);

$count = 0;

foreach ($user_ids as $user_id) {
    // Ensure $template_id is properly assigned here based on your logic
    $template_id = isset($_POST["selected-email-template-single"])
        ? $_POST["selected-email-template-single"]
        : (isset($_POST["selected-email-template-multiple"]) ? $_POST["selected-email-template-multiple"] : 0);
    
    $existing_data = $wpdb->get_var(
        $wpdb->prepare(
            "SELECT template_data FROM $table_name WHERE user_id = %d",
            $user_id
        )
    );

    $new_data = $existing_data ? json_decode($existing_data, true) : [];

    // Check if the $template_id already exists in the array
    $found = false;
    foreach ($new_data as &$template) {
        if ($template["template_id"] == $template_id) {
            // Increment the count
            $template["template_count"] = isset($template["template_count"]) ? $template["template_count"] + 1 : 1;
            $found = true;
            break;
        }
    }

    if (!$found) {
        // If the template_id does not exist, add it to the array
        $new_data[] = ["template_id" => $template_id, "template_count" => 1];
    }

    $json_data = json_encode($new_data);

    if ($existing_data !== null) {
        // Update existing record
        $wpdb->update(
            $table_name,
            ["template_data" => $json_data],
            ["user_id" => $user_id],
            ["%s"],
            ["%d"]
        );
    } else {
        // Insert new record
        $wpdb->insert(
            $table_name,
            ["user_id" => $user_id, "template_data" => $json_data],
            ["%d", "%s"]
        );
    }
    $count++;
}



            // wp_safe_redirect(get_permalink("toplevel_page_custom-send-mail-users"));
            // echo '<div class="notice notice-success is-dismissible"><p>' . $countFail . ' Email(s) failed and ' . $countSuccess . ' Email(s) sent successfully.</p></div>';

            $response = array(
                'message' => $countFail . ' Email(s) failed and ' . $countSuccess . ' Email(s) sent successfully.',
            );


        } else {
            $response = array(
                'message' => 'Error sending email.',
            );
            
        }
        // Example response
        $response = array(
                'message' => $countFail . ' Email(s) failed and ' . $countSuccess . ' Email(s) sent successfully.',
            );
        wp_send_json_success($response);
}

// Hook the AJAX handler function
// Hook the AJAX handler function to the custom action
add_action('wp_ajax_custom_send_mail_action', 'send_mail_ajax_handler');
add_action('wp_ajax_nopriv_custom_send_mail_action', 'send_mail_ajax_handler');

