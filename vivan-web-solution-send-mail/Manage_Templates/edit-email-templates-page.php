<?php
function edit_email_templates_page()
{


?>

<div class="wrap">
   <div class="container">
      <div class="d-flex justify-content-between align-items-center">
         <h1 class="mb-4">Edit Email Template</h1>
         <a class="btn btn-primary" href="?page=manage-email-templates"><i class="fa-solid fa-list-check"></i>&nbsp;Manage Email Templates</a>
      </div>
      <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" enctype="multipart/form-data">
         <!-- Display TinyMCE editor -->
         <?php
            // Check if the ID is provided in the URL
            if (isset($_GET['id']) && absint($_GET['id'])) {
                $template_id = absint($_GET['id']);
                // Retrieve the email template details based on the provided ID
                global $wpdb;
                $table_name = $wpdb->prefix . 'email_templates';
                $template = $wpdb->get_row($wpdb->prepare("SELECT * FROM $table_name WHERE id = %d", $template_id));
            
                // Set the content with the retrieved data
                $content = ($template) ? $template->content : '';
                $template_name = ($template) ? $template->name : '';
            
                $id = ($template) ? $template->id : '';
            } else {
                // If no ID is provided, initialize the content and template_name with empty values
                $content = '';
                $template_name = '';
            }
             ?>
         <div class="form-group">
            <label>Template Name</label>
            <input type="text" name="template_name" class="form-control" value="<?php echo esc_attr($template_name); ?>">
            <input type="text" name="template_id" class="form-control d-none" value="<?php echo esc_attr($id); ?>">
         </div>
         <?php
            // Display TinyMCE editor with the retrieved content
            wp_editor($content, 'newsletter_email_template', array(
                'textarea_name' => 'newsletter_email_template_content',
                'media_buttons' => true,
                'tinymce' => array(
                    'toolbar1' => 'undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image | code',
                    'toolbar2' => '',
                    'toolbar3' => '',
                ),
                'textarea_rows' => 20,
            ));
            ?>
         <br>
         <?php
            // Add the hidden input field for the template ID
            if (isset($_GET['id']) && absint($_GET['id'])) {
                echo '<input type="hidden" name="template_id" value="' . esc_attr($template_id) . '">';
            }
            ?>
         <?php wp_nonce_field('save_email_template_action', 'email_template_nonce'); ?>
         <input type="hidden" name="action" value="save_email_template">
         <!-- Rest of your form elements... -->
         <input type="submit" class="btn btn-primary mt-4" value="update Email Template">
      </form>
   </div>
</div>



<?php
}
