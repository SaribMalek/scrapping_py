<?php

// Ajax handler to fetch email template content
add_action('wp_ajax_get_email_template_content', 'get_email_template_content');
add_action('wp_ajax_nopriv_get_email_template_content', 'get_email_template_content');
function get_email_template_content() {
    if (isset($_GET['template_id'])) {
        $template_id = absint($_GET['template_id']);
        // Query to get the email template content using the template_id
        global $wpdb;
        $table_name = $wpdb->prefix . 'email_templates';
        $template = $wpdb->get_row($wpdb->prepare("SELECT content FROM $table_name WHERE id = %d", $template_id));

        if ($template) {
            echo $template->content;
        } else {
            echo 'Template not found.';
        }
    }
    wp_die(); // Always include this at the end of Ajax functions
}