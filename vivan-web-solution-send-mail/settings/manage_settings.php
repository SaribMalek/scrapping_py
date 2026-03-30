<?php

function custom_send_mail_settings_page()
{
    // Display the settings form inside a Bootstrap card
    // echo '<div class="wrap">';
    // echo '<div class="card">';
    // echo '<h5 class="card-header">Settings</h5>';
    // echo '<div class="card-body">';

    // Check if the form has been submitted
    if (isset($_POST['save_settings'])) {
        // Handle form submission here, e.g., save the API key and icon

        // You can access the API key using $_POST['api_key']
        $api_key = sanitize_text_field($_POST['api_key']);

        // You can access the icon URL using $_POST['icon_url']
        // $icon_url = sanitize_text_field($_POST['icon_url']);
        $email_log_functionality = isset($_POST['email_log_functionality']) && $_POST['email_log_functionality'] == '1' ? 1 : 0;

        // Save the API key and icon to the database or options
        update_option('custom_send_mail_api_key', $api_key);
        update_option('email_log_functionality', $email_log_functionality);
        // update_option('custom_send_mail_icon_url', $icon_url);

        // Display a success message
       
        echo '<div class="notice notice-success is-dismissible"><p>Settings saved successfully!</p></div>';
    }

    // Retrieve the saved API key and icon URL
    $saved_api_key = get_option('custom_send_mail_api_key');
    $saved_icon_url = get_option('custom_send_mail_icon_url');
    ?>
    <div class="wrap">
      <div class="container "> 
           <h1 class="text-dark mb-4">Settings</h1>
           <form method="post" action="">
    <div class="border border-secondary p-4">
    <div class="form-group">
        <h1>API Settings</h1>
        <label for="api_key" class="form-label">QuickEmailVerification API Key</label>
        <select class="form-control" id="api_key" name="api_key">
            <option value="064c05eea103cedb9a6dda7a402a6117f82fe482eaf5ff427840fd08e8d1" <?php echo ($saved_api_key === '064c05eea103cedb9a6dda7a402a6117f82fe482eaf5ff427840fd08e8d1') ? 'selected' : ''; ?>>Dev Patel API</option>
            <option value="99d9aec248dcc891fa51f08b1074308a596af685a1da5788f63c8542c96e" <?php echo ($saved_api_key === '99d9aec248dcc891fa51f08b1074308a596af685a1da5788f63c8542c96e') ? 'selected' : ''; ?>>Mayur Solanki API</option>
        </select>
    </div>
    </div>

    <!-- Additional Block for Enable/Disable Functionality -->
    <div class="border border-secondary p-4 mt-4">
    <div class="form-group">
        <h1>Functionality Settings</h1>
        <div class="form-check">
                <?php
                // Retrieve the checkbox state from the database
                $emailLogFunctionality = get_option('email_log_functionality', 0); // Default to 0 if not found
                $isChecked = $emailLogFunctionality == 1 ? 'checked' : '';
                ?>
                <input class="form-check-input p-0 m-0 mt-1" type="checkbox" id="email_log_functionality" name="email_log_functionality" value="1" <?php echo $isChecked; ?>>
                <label class="form-check-label ml-4 p-0 m-0" for="email_log_functionality">
                    Deleted Email Logs
                </label>
            </div>
    </div>
</div>


    <button type="submit" name="save_settings" class="btn btn-primary mt-4">Save Settings</button>
</form>

      </div>
    </div>  

    <?php
    // // Display the settings form
    // echo '<form method="post" action="">';
    // echo '<div class="mb-3">';
    // echo '<label for="api_key" class="form-label">API Key</label>';
    // echo '<input type="text" class="form-control" id="api_key" name="api_key" value="' . esc_attr($saved_api_key) . '" >';
    // echo '</div>';

    // // echo '<div class="mb-3">';
    // // echo '<label for="icon_url" class="form-label">Icon</label>';
    // // echo '<input type="text" class="form-control" id="icon_url" name="icon_url" value="' . esc_attr($saved_icon_url) . '" >';
    // // echo '</div>';

    // echo '<button type="submit" name="save_settings" class="btn btn-success">Save Settings</button>';
    // echo '</form>';

    // echo '</div>'; // .card-body
    // echo '</div>'; // .card
    // echo '</div>'; // .wrap
}
