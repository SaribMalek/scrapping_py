    <div class="modal fade" id="Send-Mail-Modal" tabindex="-1" role="dialog" aria-labelledby="exampleModalCenterTitle" aria-hidden="true">
       <div class="modal-dialog modal-dialog-centered" role="document">
          <div class="modal-content">
             <div class="modal-header bg-info text-light font-weight-bold">
                <h5 class="modal-title" id="exampleModalLongTitle">Send Email</h5>
                <button type="button" class="close text-light" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
                </button>
             </div>
             <form id="Mail-Sent" method="post" enctype="multipart/form-data" action="<?php echo esc_url($_SERVER['REQUEST_URI']); ?>">
                <div class="modal-body">
                  <!--  <div class="form-group">
                      <label for="To">To</label>
                      <input type="text" name="to" id="To" class="form-control">

                   </div> -->
                   <style type="text/css">
                      .email-tags {
      border: 1px solid #ccc;
      min-height: 30px;
      padding: 5px;
      display: flex;
      flex-wrap: wrap;
    }

    .email-tag {
      background-color: #f1f1f1;
      border-radius: 3px;
      padding: 2px 5px;
      margin: 2px;
      display: flex;
      align-items: center;
    }

    .email-tag .email {
      margin-right: 5px;
    }

    .email-tag .cross {
      cursor: pointer;
    }

                   </style>
    <input type="text" name="user-id-multiple" id="user-id-multiple" class="d-none">
    <input type="text" name="user-name-multiple" id="user-name-multiple" class="d-none">
                   <label for="To">To</label>
                   <div class="email-tags"></div>
                   <div class="form-group d-none">
                     <label for="To">To</label>
                     <input type="text" id="get_send_mail_value" class="form-control" name="to" >
                   </div>



                   <!-- <div class="form-group">
                    <label for="to">To</label>
                    <textarea class="form-control" id="To" name="to" rows="3"></textarea>
                  </div> -->


                   <div class="form-group mt-2">
                      <label for="subject">Subject</label>
                      <input type="text" name="subject" id="subject" class="form-control">
                   </div>
                    
                  


                   <div class="form-group w-100">
                       <label for="exampleFormControlSelect1">Select Mail Template</label>
                       <select class="form-control" id="selected-email-template" name="selected-email-template-multiple" required>
                         <option value="" disabled selected>Please select email template</option>
                           <?php 
                           global $wpdb;
                           $table_name = $wpdb->prefix . 'email_templates';
                           
                           $data = $wpdb->get_results("SELECT * FROM $table_name");
                           if ($data) {
                               foreach ($data as $row) {
                                   echo '<option value="' . esc_html($row->id) . '|' . esc_html($row->name) . '">' . esc_html($row->name) . '</option>';
                               }   
                           } else {
                               // Add a default option if there are no templates available
                               echo '<option>No templates available</option>';
                           }
                           ?>
                       </select>
                   </div>
                   

                   <div class="form-group d-none">
                       <label for="exampleFormControlTextarea1">Example textarea</label>
                       <textarea class="form-control" id="email-template-content" rows="3" name="content"></textarea>
                     </div>


                   <div class="form-group">
                      <label for="attachments">Attachments</label>
                      <input type="file" name="attachment[]" multiple>
                      <small class="form-text text-muted">You can attach multiple files.</small>
                   </div>

                   <div class="progress d-none" id="progress-send-mail">
                       <div class="progress-bar progress-bar-striped progress-bar-animated " role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%" id="loader-send-mail">
                       </div> 
                   </div>
                </div>

                <div class="modal-footer">
                   <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                   <button type="submit" name="sent-email" class="btn btn-primary" id="send-mail">Send Mail</button>
                </div>
             </form>
          </div>
       </div>
    </div>




    <div class="modal fade" id="Send-Mail-Modal-single" tabindex="-1" role="dialog" aria-labelledby="exampleModalCenterTitle" aria-hidden="true">
       <div class="modal-dialog modal-dialog-centered" role="document">
          <div class="modal-content">
             <div class="modal-header bg-info text-light font-weight-bold">
                <h5 class="modal-title" id="exampleModalLongTitle">Send Email</h5>
                <button type="button" class="close text-light" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
                </button>
             </div>
             <form id="Mail-Sent-single" method="post" enctype="multipart/form-data" action="<?php echo esc_url($_SERVER['REQUEST_URI']); ?>">
                <div class="modal-body">
                   
                    <div class="form-group">
                      <label for="To">To</label>
                      <input type="text" name="to" id="To" class="form-control" readonly>

                   </div> 
                   <input type="text" name="user-name-single" id="user-name-single" class="d-none">
    <input type="number" name="user-id" id="user-id-single" class="d-none">
                   <div class="form-group mt-2">
                      <label for="subject">Subject</label>
                      <input type="text" name="subject" id="subject" class="form-control">
                   </div>
                    
                   
                   <div class="form-group w-100">
    <label for="exampleFormControlSelect1">Select Mail Template</label>
    <select class="form-control" id="selected-email-template-single" name="selected-email-template-single" required>
        <option value="" disabled selected>Please select email template</option>
        <?php 
        global $wpdb;
        $table_name = $wpdb->prefix . 'email_templates';
        
        $data = $wpdb->get_results("SELECT * FROM $table_name");
        if ($data) {
            foreach ($data as $row) {
                // Set both id and name in the value attribute
                echo '<option value="' . esc_html($row->id) . '|' . esc_html($row->name) . '">' . esc_html($row->name) . '</option>';
            }   
        } else {
            // Add a default option if there are no templates available
            echo '<option>No templates available</option>';
        }
        ?>
    </select>
</div>



                   <div class="form-group d-none">
                       <label for="exampleFormControlTextarea1">Example textarea</label>
                       <textarea class="form-control" id="email-template-content-single" rows="3" name="content"></textarea>
                     </div>


                   <div class="form-group">
                      <label for="attachments">Attachments</label>
                      <input type="file" name="attachment[]" multiple>
                      <small class="form-text text-muted">You can attach multiple files.</small>
                   </div>
                   <div class="progress d-none" id="progress-send-mail-single">
                       <div class="progress-bar progress-bar-striped progress-bar-animated " role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%" id="loader-send-mail-single">
                       </div> 
                   </div>
                </div>

               

                <div class="modal-footer">
                   <button type="button" class="btn btn-secondary" data-dismiss="modal">Close</button>
                   <button type="submit" name="sent-email" class="btn btn-primary" id="send-mail">Send Mail</button>
                </div>
             </form>
          </div>
       </div>
    </div>

    <div id="required-minimum-two-email-modal" class="modal fade" tabindex="-1">
       <div class="modal-dialog modal-dialog-centered">
          <div class="modal-content">
             <div class="modal-header bg-danger">
                <h6 class="modal-title text-white">Warning</h6>
                <button type="button" class="close text-white" data-dismiss="modal" aria-label="Close">
                <span aria-hidden="true">&times;</span>
                </button>
             </div>
             <div class="modal-body">
                <p>No emails selected. Please select at least two emails to proceed.</p>
             </div>
          </div>
       </div>
    </div>