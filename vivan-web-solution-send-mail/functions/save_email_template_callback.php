<?php

add_action('admin_post_save_email_template', 'save_email_template_callback');

function save_email_template_callback()
{
    $error_message = ''; // Initialize error message to empty
    $success_message = ''; // Initialize success message to empty

    if (
        isset($_POST['email_template_nonce'])
        && wp_verify_nonce($_POST['email_template_nonce'], 'save_email_template_action')
        && isset($_POST['newsletter_email_template_content'])
    ) {
        $content = stripslashes($_POST['newsletter_email_template_content']);
        $name = $_POST['template_name'];
        $id = isset($_POST['template_id']) ? absint($_POST['template_id']) : 0; // Get the ID if available

        global $wpdb;
        $table_name = $wpdb->prefix . 'email_templates';

        if ($id) {
            // Update the data if ID is provided
            $data = array(
                'content' => $content,
                'name' => $name,
                // Add more fields if needed
            );
            $where = array('id' => $id);
            $format = array('%s', '%s');
            $updated = $wpdb->update($table_name, $data, $where, $format);

            if ($updated !== false) {
                // Email template updated successfully
                $success_message = 'Email Template are successfully Updated.';
            } else {
                // Error updating the email template
                $error_message = 'Error: Failed to update the Email Template.';
            }
        } else {
            // Insert new data if ID is not provided
            $data = array(
                'content' => $content,
                'name' => $name,
                // Add more fields if needed
            );
            $format = array('%s', '%s');
            $inserted = $wpdb->insert($table_name, $data, $format);

            if ($inserted !== false) {
                // Email template inserted successfully
                $success_message = 'Email Template are successfully Created.';
            } else {
                // Error inserting the email template
                $error_message = 'Error: Failed to create the Email Template.';
            }
        }
    }

    // Redirect back to the email templates page after saving
    wp_safe_redirect(admin_url('admin.php?page=manage-email-templates'));

    // Append the success or error message to the URL as a query parameter
    if ($success_message) {
        wp_safe_redirect(add_query_arg('message', urlencode($success_message), admin_url('admin.php?page=manage-email-templates')));
    } elseif ($error_message) {
        wp_safe_redirect(add_query_arg('error', urlencode($error_message), admin_url('admin.php?page=manage-email-templates')));
    }
    exit; // Make sure to add the exit() function after the redirect
}

// Display the alert messages after redirection
add_action('admin_notices', 'display_email_template_messages');
function display_email_template_messages()
{
    if (isset($_GET['message'])) {
        echo '<div class="notice notice-success is-dismissible"><p>' . esc_html($_GET['message']) . '</p></div>';
    } elseif (isset($_GET['error'])) {
        echo '<div class="notice notice-error is-dismissible"><p>' . esc_html($_GET['error']) . '</p></div>';
    }
}


