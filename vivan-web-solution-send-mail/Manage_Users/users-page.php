<?php 

// Callback function to render the admin page for managing users
function custom_send_mail_users_page() {
   
   $screen = get_current_screen();
   if($screen->id === 'toplevel_page_custom-send-mail-users'){
   $emailLogFunctionality = get_option('email_log_functionality', null); 
   
     ?>
     <style>
         .container {
             margin-top: 20px;
         }
         h1 {
             margin-bottom: 20px;
         }
         th {
             background-color: #f2f2f2;
             font-weight: bold;
         }
         td {
             vertical-align: middle;
         }
         .btn {
             margin-right: 5px;
         }

         .custom-width {
            width: 80px; /* Set the width for the columns */
            height: 40px; /* Set the height for the columns */
        }
        
        .truncated-text {
            display: inline-block;
            max-width: 100px; /* Adjust this value as needed */
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            cursor: pointer;
        }
        /* Style for the full text on hover */
        .truncated-text:hover::after {
            content: attr(data-full-text);
            position: absolute;
            background-color: #fff; /* Background color for full text */
            z-index: 1000;
            padding: 10px; /* Adjust padding as needed */
            border: 1px solid #ccc; /* Border style for full text */
            border-radius: 5px; /* Adjust border radius as needed */
            box-shadow: 2px 2px 5px rgba(0, 0, 0, 0.2); /* Add a subtle box shadow */
            white-space: normal;
            max-width: 300px; /* Adjust the maximum width for full text */
            font-size: 14px; /* Adjust font size for full text */
            color: #333; /* Text color for full text */
        }
        #preloader {
            position: fixed;
            top: 0;
            left: 13%;
            width: 90%;
            height: 100%;
            background-color: rgba(255, 255, 255, 0.7); /* Semi-transparent background */
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9999; /* Ensure it's above other elements */
        }
        #preloader .spinner-border {
            margin-bottom: 10px; /* Adjust spacing between spinner and message */
        }
     </style>
     <div class="container">
         <div class="wrap">
          <div class="notice notice-success is-dismissible d-none" id="spinner">
              <!-- Replace this with your preferred spinner implementation -->
              <div class="spinner-wrapper">
                <div class="spinner"></div>
            </div>
            <p>Please Wait...</p>
        </div>

        <div class="notice notice-success is-dismissible d-none" id="error-alert">
          <p id="msg-error"></p>
      </div>

      <h1 class="text-dark mb-4">Manage Users</h1>
      
      <div class="notice notice-error is-dismissible d-none" id="datatbl-loading">
         <p id="datatbl-msg">Loading data. Please wait...</p>
      </div>
      
      <div id="preloader">
            <img src="<?php echo dirname(plugin_dir_url(__FILE__)) . "/assets/preloader.gif" ?>" alt="Loading...">
      </div>
      
      <!-- Use Bootstrap's "d-flex" class to create a flex container -->
      <div class="alert alert-danger alert-dismissible fade show d-none" role="alert" id="delete-alert">
       <strong>Success!</strong> User are Deleted.
       <button type="button" class="close" data-dismiss="alert" aria-label="Close">
           <span aria-hidden="true">&times;</span>
       </button>
   </div>
   <div class="alert alert-info alert-dismissible fade show d-none" role="alert" id="update-alert">
       <strong>Holy guacamole!</strong> You should check in on some of those fields below.
       <button type="button" class="close" data-dismiss="alert" aria-label="Close">
           <span aria-hidden="true">&times;</span>
       </button>
   </div>
   <div class="alert alert-success alert-dismissible fade show d-none" role="alert" id="create-alert">
       <strong>Success!</strong><span id="success-msg"> </span>
       <button type="button" class="close" data-dismiss="alert" aria-label="Close">
           <span aria-hidden="true">&times;</span>
       </button>
   </div>
   <div class="d-flex">
       <!-- Button for sending mail -->
       <button class="btn btn-primary mb-4 font-weight-bold" id="sendMailBtn">
           <i class="fa-solid fa-paper-plane"></i>&nbsp;Send Mail
       </button>
       <!-- Button for uploading CSV -->
       <button class="btn btn-primary mb-4 font-weight-bold upload-csv" id="upload-csv-btn">
           <i class="fa-solid fa-upload"></i>&nbsp;Upload CSV
       </button>
       <!-- Button for downloading CSV -->
       <a class="btn btn-primary text-light mb-4 font-weight-bold" href="../wp-content/plugins/vivan-web-solution-send-mail/assets/csv-sample/users.csv">
           <i class="fa-solid fa-download"></i>&nbsp;Download CSV
       </a>
       <button class="btn btn-primary mb-4 text-light font-weight-bold " id="valid-email-btn">
           <i class="fa-solid fa-list-check"></i>&nbsp;Validate Emails
       </button>


      

       <!-- Button for deleting selected users -->
       <!-- "Add New User" button on the right side -->
       
       <button class="btn btn-success mb-4 text-light font-weight-bold ml-auto" data-toggle="modal" data-target="#add-new-user">
           <i class="fa-solid fa-plus"></i>&nbsp;Add New User
       </button>
       <button class="btn btn-danger mb-4 font-weight-bold " id="delete-selected-user">
           <i class="fa-solid fa-trash-can"></i>&nbsp;Delete Selected User
       </button>

   </div>

   
        <div class="d-flex align-items-center mb-4">
           <div>
              <label for="page-input" class="m-0">Go to Page:</label>
           </div>
           <div class="ml-4 mr-4">
              <input type="number" id="page-input" min="1" value="1" class="form-control" style="
                 width: 96px;
                 ">
           </div>
           <div class="mr-4">
              <select id="is-verified-filter" class="form-control" style="
                 width: 158px;
                 ">
                 <option disabled selected>-- Filter is_verified --</option>
                 <option value="">All</option>
                 <option value="1">Verified</option>
                 <option value="3">Unverified</option>
                 <option value="2">Unknown</option>
              </select>
           </div>
           <div class="mr-4">
              <select id="template-filter" class="form-control" style="width: 158px;">
                 <option disabled selected>-- Filter Template --</option>
                 <option value="">All Templates</option>
                 <option value="not_send">Not Send Mails</option>
                 <!-- <option value="choose_template">Choose Template</option> -->
              </select>
           </div>
           <div class="btn-group d-flex mx-auto" role="group">
              <i class="fa-solid fa-trash-can text-danger border p-2 border-danger rounded-left"></i>
              <button class="btn btn-outline-danger   ml-auto<?php echo $emailLogFunctionality != 1 ? ' d-none' : ''; ?>" id="dlt-Email-logs">Trash Email Log's
              </button>
           </div>
        </div>

        
   <table id="User-Tbl" class="display table table-striped table-bordered nowrap dataTable no-footer" style="width:100%">

    <thead>
        <tr>
            <th><input type="checkbox" id="selectAllCheckbox" data-toggle="switch" data-on-text="Active" data-off-text="Inactive" data-on-color="success" data-off-color="danger"><span class="badge badge-primary d-none" id="count-selected-checkbox"></span></th>
            <th>Name</th>
            <th>Type</th>
            <th>Email</th>
            <th>Is verified</th>
            <th>Template Info</th>
            <th>Id</th>
             <th>Operation</th>
            <th class="d-none">Ids</th>
        </tr>
    </thead>
    <tbody></tbody>
</table>
</div>
</div>
<?php require_once plugin_dir_path(__FILE__) . "../Bootstrap_modals/Send-Mail-Modal.php"; ?>
<?php require_once plugin_dir_path(__FILE__) . "../Bootstrap_modals/No-emails-selected-modal.php"; ?>
<?php require_once plugin_dir_path(__FILE__) . "../Bootstrap_modals/No-user-checkbox-selected-modal.php"; ?>
<?php require_once plugin_dir_path(__FILE__) . "../Bootstrap_modals/upload-csv-file.php"; ?>
<?php require_once plugin_dir_path(__FILE__) . "../Bootstrap_modals/delete_user_model.php"; ?>
<?php require_once plugin_dir_path(__FILE__) . "../Bootstrap_modals/add-new-user.php"; ?>
<?php require_once plugin_dir_path(__FILE__) . "../Bootstrap_modals/failed_email_logs.php"; ?>
<?php require_once plugin_dir_path(__FILE__) . "../Bootstrap_modals/user-template-send-list.php"; ?>
<?php
}
}