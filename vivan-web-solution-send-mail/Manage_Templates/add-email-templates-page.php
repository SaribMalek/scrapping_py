<?php
function custom_email_templates_page()
{

?>
<div class="wrap">
   <div class="container">
      <!-- Display TinyMCE editor -->
      <div class="d-flex justify-content-between align-items-center mt-4">
         <h1 class="">Add Email template</h1>
         <a class="btn btn-primary" href="?page=manage-email-templates"><i class="fa-solid fa-list-check"></i>&nbsp;Manage Email Templates</a>
      </div>
      <br>
      <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" enctype="multipart/form-data">
         <div class="form-group">
            <label>Enter Name</label>
            <input type="text" name="template_name" class="form-control">
         </div>
         <?php
            $content = ''; // Initialize the content with an empty string or use any default content if needed
            
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
         <?php wp_nonce_field('save_email_template_action', 'email_template_nonce'); ?>
         <input type="hidden" name="action" value="save_email_template">
         <!-- Rest of your form elements... -->
         <input type="submit" class="btn btn-primary mt-4" value="Save Email Template">
      </form>
   </div>
</div>


<?php

}
