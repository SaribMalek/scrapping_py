<?php

function manage_email_templates_page()
{ 

   $screen = get_current_screen();
  
   if($screen->id === 'send-mail-to-users_page_manage-email-templates'){

   if (isset($_GET['id'])) {
       $id = $_GET['id'];
   
       global $wpdb;
       $table_name = $wpdb->prefix . 'email_templates';
   
       // Perform the delete query
       $deleted = $wpdb->delete($table_name, array('id' => $id));
   
       if ($deleted === false) {
          $error_message = 'Error: Failed to delete the item.';
       } else {
           // If the delete query was successful
          echo '<div class="notice notice-success is-dismissible"><p>Successfully deleted</p></div>';
       }
   }
   
   // Redirect after handling the delete operation
    $redirect_url = remove_query_arg('id', $_SERVER['REQUEST_URI']);
   
       // Redirect after handling the delete operation
       //wp_redirect($redirect_url);
   ?>
<div class="container">
   <div class="d-flex justify-content-between align-items-center mt-4">
      <h1 class="h5">Manage Email Templates</h1>
      
   </div>
   <div class="wrap">
       <div class="d-flex align-items-center mb-4">
         <a class="btn btn-success mb-4 text-light font-weight-bold " href="?page=add-email-templates">
         <i class="fa-solid fa-plus"></i>&nbsp;Add New Template
      </a>
       </div>  
     <table id="emailTemplatesTable"class="display table table-striped table-bordered nowrap dataTable no-footer" style="width:100%">
    <thead>
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Operations</th>
        </tr>
    </thead>
    <tbody>
        <!-- Table rows will be added dynamically using DataTables -->
    </tbody>
</table>

   </div>
</div>



<?php
}
}