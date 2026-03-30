   <div id="add-new-user" class="modal fade" tabindex="-1">
      <div class="modal-dialog modal-dialog-centered">
         <div class="modal-content">
            <div class="modal-header bg-success ">
               <h6 class="modal-title text-white font-weight-bold">Add New User</h6>
               <button type="button" class="close text-white" data-dismiss="modal" aria-label="Close">
               <span aria-hidden="true">&times;</span>
               </button>
            </div>
            <form method="post" id="addUser">
               <div class="modal-body">
                  <input type="text" id="user-id" value="" class="form-control d-none">
                  <div class="form-group">
                     <label>Name</label>
                     <input type="text" id="name" class="form-control">
                     <small id="name-validation-feedback"></small>
                  </div>
                  <div class="form-group">
                     <label>Type</label>
                     <input type="text" id="type" class="form-control">
                     <small id="type-validation-feedback"></small>
                  </div>
                  <div class="form-group">
                     <label>Email</label>
                     <input type="email" id="email" class="form-control">
                     <small id="email-validation-feedback"></small>
                  </div>
               </div>
               <div class="modal-footer">
                  <div class="loader "></div>
                  <button type="button" class="btn btn-danger" data-dismiss="modal">Close</button>
                  <button type="submit" class="btn bg-primary text-light">Submit</button>
               </div>
            </form>
         </div>
      </div>
   </div>