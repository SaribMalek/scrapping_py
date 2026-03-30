      <div id="upload-csv-file" class="modal fade" tabindex="-1">
         <div class="modal-dialog modal-dialog-centered">
            <div class="modal-content">
               <div class="modal-header bg-primary ">
                  <h6 class="modal-title text-white">Upload Csv File</h6>
                  <button type="button" class="close text-white" data-dismiss="modal" aria-label="Close">
                     <span aria-hidden="true">&times;</span>
                  </button>
               </div>
               <div class="modal-body">

                  <form id="csv-upload-form" method="post" enctype="multipart/form-data">
                    <div class="form-group">
                     <label for="recipient-name" class="col-form-label">Upload CSV:</label>
                     <input type="file" id="csv-file-input" name="csv_file" class="form-control">
                  </div>

                  <div class="progress d-none" id="progress">
                   <div class="progress-bar progress-bar-striped progress-bar-animated " role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%" id="loader">
                   </div> 
                </div>

                <br>
                <button class="btn btn-primary" type="submit" id="submit-csv-upload">Submit</button>
             </form>
             <div id="csv-upload-message"></div>


          </div>
       </div>
    </div>
   </div>