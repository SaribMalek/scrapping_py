<?php
/*
Plugin Name: Vivan Web Solution - Send mail
Description: This is a custom WordPress plugin for sending emails to users.
Version: 1.0
Author: Vivan Web Solution
Author URI: https://vivanwebsolution.com/
Text Domain: vivan-web-solution-send-mail
*/
/* Enqueue Bootstrap files for the WordPress admin area from CDN */



function enqueue_custom_plugin_admin_scripts()
{
    // Check if the current admin page is your plugin's settings page
    $screen = get_current_screen();
    
    if ($screen && $screen->id === 'toplevel_page_custom-send-mail-users' || $screen && $screen->id === 'send-mail-to-users_page_manage-email-templates' || $screen && $screen->id === 'admin_page_add-email-templates' || $screen && $screen->id === 'admin_page_edit-email-templates' || $screen && $screen->id === 'send-mail-to-users_page_custom-send-mail-settings') {
        
            // Enqueue jQuery
        wp_enqueue_script("jquery");

        add_action('wp_enqueue_scripts', 'my_enqueue_scripts');
        function my_enqueue_scripts() {
            wp_localize_script('my-script', 'my_ajax_object', array('ajaxurl' => admin_url('admin-ajax.php')));
        }

        // Enqueue Bootstrap CSS from CDN
        wp_enqueue_style(
            "bootstrap-css",
            "https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css",
            [],
            "4.0.0",
            "all"
        );

        // Enqueue Bootstrap JavaScript from CDN
        wp_enqueue_script(
            "bootstrap-js",
            "https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/js/bootstrap.min.js",
            ["jquery"],
            "4.0.0",
            true
        );


        // Enqueue Bootstrap DataTables CSS from CDN
        wp_enqueue_style(
            "datatables-css",
            "https://cdn.datatables.net/1.11.5/css/dataTables.bootstrap4.min.css",
            [],
            "1.11.5",
            "all"
        );

        // Enqueue Bootstrap DataTables JavaScript from CDN
        wp_enqueue_script(
            "datatables-js",
            "https://cdn.datatables.net/1.11.5/js/jquery.dataTables.min.js",
            ["jquery"],
            "1.11.5",
            true
        );


        // Enqueue Bootstrap DataTables Bootstrap 4 Compatibility JavaScript from CDN
        wp_enqueue_script(
            "datatables-bs-js",
            "https://cdn.datatables.net/1.11.5/js/dataTables.bootstrap4.min.js",
            ["jquery", "datatables-js"],
            "1.11.5",
            true
        );

        // Enqueue CKEditor
        wp_enqueue_script(
            "ckeditor",
            "https://cdn.ckeditor.com/ckeditor5/34.1.0/classic/ckeditor.js",
            ["jquery"],
            "4.1.0",
            true
        );

         // Enqueue your custom script
        wp_enqueue_script(
            "custom-script",
            plugin_dir_url(__FILE__) . "assets/custom-script.js",
            ["jquery", "ckeditor"],
            "1.0",
            true
        );

        wp_localize_script( 'custom-script', 'serverProcessingUrl', plugins_url( 'get_user_data.php', __FILE__ ) );

        wp_localize_script( 'custom-script', 'getTemplateDataUrl', plugins_url( 'get_template_data.php', __FILE__ ) );

        // Enqueue Google Fonts
        wp_enqueue_style(
            "google-fonts",
            "https://fonts.googleapis.com/icon?family=Material+Icons",
            [],
            "1.0"
        );

        // Enqueue Font Awesome
        wp_enqueue_style(
            "font-awesome",
            "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css",
            [],
            "4.7.0"
        );

        // Enqueue Font Awesome Kit
        wp_enqueue_script(
            "font-awesome",
            "https://kit.fontawesome.com/10c8819e0b.js",
            [],
            "10c8819e0b",
            false
        );

        // Enqueue Bootstrap Spinner CSS from CDN
        wp_enqueue_style(
            "bootstrap-spinner-css",
            "https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/css/bootstrap.min.css",
            [],
            "4.0.0",
            "all"
        );

        // Enqueue Bootstrap Spinner JavaScript from CDN
        wp_enqueue_script(
            "bootstrap-spinner-js",
            "https://cdn.jsdelivr.net/npm/bootstrap@4.0.0/dist/js/bootstrap.min.js",
            ["jquery"],
            "4.0.0",
            true
        );
    }
}

// Hook the function to the admin_enqueue_scripts action only for your plugin's page
add_action("admin_enqueue_scripts", "enqueue_custom_plugin_admin_scripts");



// Hook the function to the admin_enqueue_scripts action only for your plugin's page
add_action("admin_enqueue_scripts", "enqueue_custom_plugin_admin_scripts");

function custom_send_mail_to_users_activate()
{
    global $wpdb;
    $charset_collate = $wpdb->get_charset_collate();

    // Create 'send_email' table
    $table_name_send_email = $wpdb->prefix . 'send_email';
    $sql_send_email = "CREATE TABLE $table_name_send_email (
        id INT(11) NOT NULL AUTO_INCREMENT,
        name VARCHAR(100) NOT NULL,
        type VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL,
        is_verified TINYINT(1) NOT NULL DEFAULT 0,
        PRIMARY KEY (id)
    ) $charset_collate;";

    // Create 'email_templates' table
    $table_name_email_templates = $wpdb->prefix . 'email_templates';
    $sql_email_templates = "CREATE TABLE $table_name_email_templates (
        id INT(11) NOT NULL AUTO_INCREMENT,
        name VARCHAR(255) NOT NULL, -- Adding a new field called 'name'
        content LONGTEXT NOT NULL,
        PRIMARY KEY (id)
    ) $charset_collate;";

    // Create 'email_template_tracking' table (note the corrected variable name)
    $table_name_email_template_tracking = $wpdb->prefix . 'email_template_tracking';
    $sql_email_template_tracking = "CREATE TABLE $table_name_email_template_tracking (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        template_data JSON NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) $charset_collate;";

    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    dbDelta($sql_send_email);
    dbDelta($sql_email_templates);
    dbDelta($sql_email_template_tracking);
}
register_activation_hook(__FILE__, 'custom_send_mail_to_users_activate');




/* this code are used to create menu in custom plugin */
add_action("admin_menu", "custom_send_mail_to_users_add_menu");
function custom_send_mail_to_users_add_menu()
{
    // Main menu
    add_menu_page(
        "Send Mail to Users", // Page title (displayed in the browser window/tab)
        "Send Mail to Users", // Menu title (displayed in the WordPress admin menu)
        "manage_options", // Capability required to access the menu item
        "custom-send-mail-users", // Menu slug (unique identifier)
        null, // Callback function to render the admin page
        "dashicons-email" // Icon URL or dashicon class name for the menu item
    );
    // Submenu - Manage Email Templates
    // Submenu - Manage Users
    add_submenu_page(
        "custom-send-mail-to-users", // Parent menu slug
        "Manage Users", // Page title
        "Send Mail to Users", // Menu title
        "manage_options", // Capability required to access the menu item
        "custom-send-mail-users", // Menu slug (unique identifier)
        "custom_send_mail_users_page" // Callback function to render the admin page for users
    );
    // Submenu - Email Templates
    add_submenu_page(
        null,
        "Email Templates", // Page title
        "Add Templates", // Menu title
        "manage_options", // Capability required to access the menu item
        "add-email-templates", // Menu slug (unique identifier)
        "custom_email_templates_page" // Callback function to render the admin page for email templates
    );


    // Submenu - Email Templates
    add_submenu_page(
        null,
        "edit Email Templates", // Page title
        "Edit Templates", // Menu title
        "manage_options", // Capability required to access the menu item
        "edit-email-templates", // Menu slug (unique identifier)
        "edit_email_templates_page" // Callback function to render the admin page for email templates
    );

    add_submenu_page(
        "custom-send-mail-users", // Parent menu slug
        "Email Templates", // Page title
        "Email Templates", // Menu title
        "manage_options", // Capability required to access the menu item
        "manage-email-templates", // Menu slug (unique identifier)
        "manage_email_templates_page" // Callback function to render the admin page for email templates
    );

    // Submenu - Settings
    add_submenu_page(
        "custom-send-mail-users",
        "Settings", // Page title
        "Settings", // Menu title
        "manage_options", // Capability required to access the menu item
        "custom-send-mail-settings", // Menu slug (unique identifier)
        "custom_send_mail_settings_page" // Callback function to render the settings page
    );
}

require_once plugin_dir_path(__FILE__) . "settings/manage_settings.php";

require_once plugin_dir_path(__FILE__) . "Manage_Users/users-page.php";

require_once plugin_dir_path(__FILE__) . "Manage_Users/users-page.php";

require_once plugin_dir_path(__FILE__) . "functions/deleteUser_ajax_handler_function.php";

require_once plugin_dir_path(__FILE__) . "functions/Email_Validator.php";

require_once plugin_dir_path(__FILE__) . "functions/Local_Email_Verifier.php";

require_once plugin_dir_path(__FILE__) . "functions/add_new_user.php";

require_once plugin_dir_path(__FILE__) . "functions/upload_csv.php";

require_once plugin_dir_path(__FILE__) . "functions/save_email_template_callback.php";

require_once plugin_dir_path(__FILE__) . "functions/get_email_template_content.php";

require_once plugin_dir_path(__FILE__) . "functions/failed_email_logs.php";  

require_once plugin_dir_path(__FILE__) . "functions/send_mail.php";

require_once plugin_dir_path(__FILE__) . "Manage_Templates/add-email-templates-page.php";

require_once plugin_dir_path(__FILE__) . "Manage_Templates/edit-email-templates-page.php";

require_once plugin_dir_path(__FILE__) . "Manage_Templates/manage-email-templates-page.php";









