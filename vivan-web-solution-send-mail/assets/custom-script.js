   jQuery.noConflict();
   (function ($) {
      $(document).ready(function () {
          
        window.addEventListener('load', function () {
            // Hide the preloader when the page is fully loaded
             document.getElementById('preloader').style.display = 'none';
        });


         $('#User-Tbl').on('preXhr.dt', function (e, settings, data) {
        $('#datatbl-loading').removeClass("d-none");
    });
    // Hide the loading spinner when DataTable finishes processing data
    $('#User-Tbl').on('xhr.dt', function (e, settings, json, xhr) {
         $('#datatbl-loading').addClass("d-none");
    });
      var dataTable = $('#User-Tbl').DataTable({
           responsive: true,
           "serverSide": true,
           "ajax": {
              "url": serverProcessingUrl,
              "type": "POST"
           },
           "columns": [{
                 "data": null,
                 "orderable": false,
                 "render": function (data, type, row) {
                    return '<input type="checkbox" id="selectCheckbox-' + row.id + '" data-toggle="switch" data-on-text="Active" data-off-text="Inactive" data-on-color="success" data-off-color="danger">';
                 }
              }, // Checkbox column
              {
                 "data": "name",
                 "render": function (data, type, row) {
                    var maxLetters = 5; // Set the maximum number of letters to display
                    if (data.length > maxLetters) {
                       // If the text has more letters than the maximum, truncate it and add a data attribute with the full text
                       var truncatedText = data.slice(0, maxLetters) + '...';
                       return '<span class="truncated-text" data-full-text="' + data + '">' + truncatedText + '</span>';
                    } else {
                       // If the text has fewer letters or is empty, display it as is
                       return data;
                    }
                 },
              },
              {
                 "data": "type",
                 "render": function (data, type, row) {
                    var maxLetters = 5; // Set the maximum number of letters to display
                    if (data.length > maxLetters) {
                       // If the text has more letters than the maximum, truncate it and add a data attribute with the full text
                       var truncatedText = data.slice(0, maxLetters) + '...';
                       return '<span class="truncated-text" data-full-text="' + data + '">' + truncatedText + '</span>';
                    } else {
                       // If the text has fewer letters or is empty, display it as is
                       return data;
                    }
                 },
              },
              {
                 "data": "email",
                 "orderable": true,
                 "render": function (data, type, row) {
                    var maxWidth = "300px"; // Set the maximum width for the email column
                    var emailContent = '<div style="max-width:' + maxWidth + ';">' + data + '</div>';
                    return emailContent;
                 },
              },
              {
                 "data": "is_verified",
                 "render": function (data, type, row) {
                    var badgeClass, badgeText;
                    if (data == 1) {
                       badgeClass = "badge badge-success";
                       badgeText = "Verified";
                    } else if (data == 0) {
                       badgeClass = "badge badge-danger";
                       badgeText = "Unverified";
                    } else {
                       // Handle other cases if needed
                       badgeClass = "badge badge-warning";
                       badgeText = "Unknown"; // Or any other appropriate text
                    }
                    return `<span class="${badgeClass}">${badgeText}</span>`;
                 }
              },
              {
                 "data": "template_data",
                 "orderable": true,
                 "render": function (data, type, row) {
                    var templateDataArray = JSON.parse(data);
                    var templateInfo = "";
                    if (templateDataArray && templateDataArray.length > 0) {
                       for (var i = 0; i < templateDataArray.length; i++) {
                          var template = templateDataArray[i];
                          var templateId = template.template_id;
                          var templateCount = template.template_count;
                          var parts = templateId.split("|");
                          var result = parts[1];
                          // Format and append each template's information
                          var templateBadge = `
                                        <span class="badge badge-primary">
                                            ${result}
                                            <span class="badge badge-light"> ${templateCount}</span>
                                        </span>
                                    `;
                          // Append the badge to templateInfo
                          templateInfo += templateBadge;
                          // Add a separator if there are more templates
                          if (i < templateDataArray.length - 1) {
                             templateInfo += "<br>"; // Line break between templates
                          }
                       }
                    } else {
                       // Display a message when no templates are found
                       templateInfo = "<span class='badge badge-danger'>Records not found</span>";
                    }
                    // Return the formatted templateInfo
                    return templateInfo;
                 }
              },
              {
                 "data": "id",
                 "visible": false
              }, // Id column (d-none)
              {
                 "data": null,
                 "orderable": true,
                 "render": function (data, type, row) {
                    return `
                                <button class="btn btn-success" data-toggle="modal" data-target="#add-new-user" data-id="${row.id}" data-name="${row.name}" data-type="${row.type}" data-email="${row.email}"><i class="fa-solid fa-pen-to-square"></i></button>
                                <a class="btn btn-danger text-light" data-id="${row.id}" id="dlt-user"><i class="fa-solid fa-trash"></i></a>
                                <button class="btn btn-info" type="button" data-toggle="modal" data-target="#Send-Mail-Modal-single" data-email="${row.email}" data-id="${row.id}" data-name="${row.name}"><i class="fa-solid fa-envelope"></i></button>
                            `;
                 }
              }
           ],
           "lengthMenu": [
              [5, 10, 25, 50, 100, 500, -1],
              [5, 10, 25, 50, 100, 500, "All"]
           ],
           "pageLength": 5,
           "columnDefs": [{
              "targets": [0],
              "orderable": false
           }],
           "drawCallback": function (settings) {
              $('#page-input').val(settings._iDisplayStart / settings._iDisplayLength + 1);
           }
        });

    $('#is-verified-filter').on('change', function () {
        var filterValue = $(this).val();
        dataTable.column(5).search(filterValue).draw();
    });
    $('#template-filter').on('change', function () {
        var filterValue = $(this).val();
        // Apply the filter
        dataTable.column(6).search(filterValue).draw();
    });

      $('#emailTemplatesTable').DataTable({
           "processing": true, // Show loading indicator
           "serverSide": true, // Server-side processing
           "ajax": {
               "url": getTemplateDataUrl, // URL to your PHP script
               "type": "POST" // HTTP method
           },
           "columns": [
               { "data": "id" },
               { "data": "name" },
               { "data": null,
                  "render": function (data, type, row) {
                       console.log(row.id);  
                       return '<a class="btn btn-success" href="?page=edit-email-templates&&id=' + row.id + '"><i class="fa-solid fa-pen-to-square"></i></a>' +
                            '<a class="btn btn-danger ml-2" href="?page=manage-email-templates&&id=' + data.id + '"><i class="fa-solid fa-trash"></i></a>';
                  }
                 
               }
               // Add other columns as needed
           ]
       });


         var keyupTimeout;

         $('#page-input').on('keyup', function () {
            // Clear any previous timeouts to prevent multiple delayed executions
            clearTimeout(keyupTimeout);
            $('#msg-error').text('Please wait while the page loads...');
            $('#error-alert').removeClass("d-none");
            // Set a new timeout for 5 seconds
            keyupTimeout = setTimeout(function () {
                var targetPage = parseInt($('#page-input').val(), 10);
                var maxPage = dataTable.page.info().pages;
                if (!isNaN(targetPage) && targetPage >= 1 && targetPage <= maxPage) {
                    dataTable.page(targetPage - 1).draw(false);
                }
                $('#error-alert').addClass("d-none");
                $('#msg-error').text(''); // Reset text
            }, 3000); // 5000 milliseconds (5 seconds)
        });
        
        
        $(document).on('click', 'input[type="checkbox"][data-toggle="switch"]', function () {
            // Count selected checkboxes
            var selectedCheckboxes = $('input[type="checkbox"][data-toggle="switch"]:checked');
            var selectedCount = selectedCheckboxes.length;
            // Update the count display
            $('#selected-count').text(selectedCount);
            // Get the Select All checkbox
            var selectAllCheckbox = $('#selectAllCheckbox');
            // Check if the "Select All" checkbox is checked
            var isSelectAllChecked = selectAllCheckbox.is(':checked');
            // Conditionally add or remove the "d-none" class based on whether any checkboxes are selected
            if (selectedCount > 0 && !isSelectAllChecked) {
                selectAllCheckbox.addClass('d-none');
                $("#count-selected-checkbox").removeClass('d-none');
                $("#count-selected-checkbox").text(selectedCount);
            } else {
              $("#count-selected-checkbox").addClass('d-none');
                $("#count-selected-checkbox").text("");
                selectAllCheckbox.removeClass('d-none');
            }
        });


        
         /* Code for selecting multiple users */
         $(document).on("click", "#selectAllCheckbox", function () {
            $('input:checkbox').not(this).prop('checked', this.checked);
            $("#count-selected-checkbox").addClass('d-none');
            $("#selectAllCheckbox").removeClass('d-none');
         });


         /* Code for uploading CSV file */
         $(document).on("click", ".upload-csv", function () {
            $('#upload-csv-file').modal('show');
         });

         /* Code for deleting a single user */
         $(document).on("click", "#dlt-user", function () {
            var del_id = $(this).attr("data-id");
            deleteUser({
               id: del_id
            });
         });

         /* Code for deleting selected users */
         $(document).on("click", "#delete-selected-user", function () {
            var selectedIDS = [];

            $('td input:checkbox:checked').not('#selectAllCheckbox').each(function () {
               var row = dataTable.row($(this).closest('tr')).data(); // Get the DataTables row data
               if (row) {
                  selectedIDS.push(row.id);
               }
            });

            const data = {
               id: selectedIDS.join(',')
            };

            if (selectedIDS.length > 0) {
               deleteUser(data).then(function () {
                  // Reload the DataTable after deleting
                  dataTable.ajax.reload();
               });
            } else {
               $('#No-user-checkbox-selected-modal').modal('show');
            }
         });


         function deleteUser(data) {
            $("#delete_user_model").modal('show');

            $(document).on("click", "#approve-user-delete", function (e) {
               e.preventDefault();

               $("#error-alert").removeClass('d-none');
               $.ajax({
                  type: "POST",
                  url: ajaxurl,
                  data: {
                     data,
                     action: 'delete_user',
                  },
                  success: function (response) {
                     $("#error-alert").addClass('d-none');

                     console.log(response);
                     var json_msg = JSON.parse(response);
                     var msg = json_msg.msg;

                     $("#delete_user_model").modal('hide');
                     $("#error-alert").removeClass('d-none');
                     $("#msg-error").text("User are successfully Deleted");
                     dataTable.ajax.reload();
                     $("#error-alert").addClass('d-none');
                     
                  }
               });
            });
         }

         /* Email validation function */
         function validateEmail(email) {
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailPattern.test(email);
         }

         $('#email').keyup(function () {
            const emailInput = $(this).val().trim();
            const isValidEmail = validateEmail(emailInput);

            const feedbackDiv = $('#email-validation-feedback');
            feedbackDiv.text(isValidEmail ? 'Valid email address' : 'Invalid email address');
            feedbackDiv.css('color', isValidEmail ? 'green' : 'red');
         });

         /* Code for adding a new user using AJAX */
         $(document).on("submit", "#addUser", function (e) {
            e.preventDefault();
            const name = $('#name').val().trim();
            const type = $('#type').val().trim();
            const email = $('#email').val().trim();
            const id = $('#user-id').val().trim();

            

            // Validation code for name, type, and email fields

            $.ajax({
               url: ajaxurl,
               type: 'POST',
               data: {
                  action: 'add_user',
                  name: name,
                  type: type,
                  email: email,
                  id: id,
               },
               success: function (response) {
                  
                    
                  if (response.message === "User data inserted successfully" || response.message === "User data updated successfully") {
                    
                     setTimeout(function () {
                       $("#progress-send-mail-single").addClass("d-none"); // Hide the progress bar after a delay
                       $("#add-new-user").modal('hide');
                       $("#error-alert").removeClass("d-none");
                       $("#msg-error").text(response.message);
                       dataTable.ajax.reload();
                     }, 1000);  
 
                  } else {
                     $("#email-validation-feedback").text(response.message).addClass('text-danger');
                     console.log('Error:', response.message);
                  }
               },
               error: function (jqXHR, textStatus, errorThrown) {
                  console.log('AJAX Error:', errorThrown);
               },
            });
         });

         /* Code for getting email */


         $('#add-new-user').on('show.bs.modal', function (event) {
            var button = $(event.relatedTarget);
            var id = button.data('id');
            var name = button.data('name');
            var type = button.data('type');
            var email = button.data('email');

            var modal = $(this);
            $("#user-id").val(id);
            $("#name").val(name);
            $("#type").val(type);
            $("#email").val(email);
         });

         $('#selected-email-template').on('change', function () {
            var selectedId = $(this).val(); // Get the selected ID from the dropdown
            if (selectedId !== '') {
               // Send Ajax request
               $.ajax({
                  url: ajaxurl, // WordPress Ajax URL (available in the global scope)
                  type: 'GET',
                  data: {
                     action: 'get_email_template_content',
                     template_id: selectedId,
                  },
                  success: function (response) {

                     // Update the template content container with the received data
                     $('#email-template-content').val(response);
                  },
                  error: function (xhr, status, error) {
                     console.log('Ajax request failed:', error);
                  },
               });
            }
         });

         $('#selected-email-template-single').on('change', function () {
            var selectedId = $(this).val(); // Get the selected ID from the dropdown
            if (selectedId !== '') {
               // Send Ajax request
               $.ajax({
                  url: ajaxurl, // WordPress Ajax URL (available in the global scope)
                  type: 'GET',
                  data: {
                     action: 'get_email_template_content',
                     template_id: selectedId,
                  },
                  success: function (response) {

                     // Update the template content container with the received data
                     $('#email-template-content-single').val(response);
                  },
                  error: function (xhr, status, error) {
                     console.log('Ajax request failed:', error);
                  },
               });
            }
         });


         $(document).on("click", "#sendMailBtn", function () {
            var selectedItems = [];
            $('td input:checkbox:checked').not('#selectAllCheckbox').each(function () {
               var row = dataTable.row($(this).closest('tr')).data(); // Get the DataTables row data
               if (row) {
                  var email = row.email; // Assuming the email column is at index 3
                  var id = row.id; // Assuming the id column is at index 4
                  //var name = row.name; // Assuming the name column is at index 1
                  var name = row.name.replace(/,/g, '');
                  selectedItems.push({
                     email: email,
                     id: id,
                     name: name
                  });
               }
            });
            if (selectedItems.length === 1) {
               // Open a different modal for a single user
               $('#required-minimum-two-email-modal').modal('show');
            } else if (selectedItems.length > 1) {
               var emailList = selectedItems.map(item => item.email).join(', ');
               var idList = selectedItems.map(item => item.id).join(', ');
               var nameList = selectedItems.map(item => item.name).join(', ');
               console.log(emailList);
               $('#Send-Mail-Modal').modal('show');
               $("#get_send_mail_value").val(emailList); // Update the input field with selected emails
               $("#user-id-multiple").val(idList);
               $("#user-name-multiple").val(nameList);
               const emailTagsContainer = document.querySelector('.email-tags');
               emailTagsContainer.innerHTML = ''; // Clear the existing tags before adding the selected emails
               selectedItems.forEach((item) => {
                  addTag(item.email, item.id, item.name);
               });

               function addTag(email, id, name) {
                  const newTag = document.createElement('div');
                  newTag.classList.add('email-tag');
                  newTag.innerHTML = `<span class="email">${email}</span><span class="cross">x</span>`;
                  emailTagsContainer.appendChild(newTag);
                  // Attach click event to the new cross button
                  const newCross = newTag.querySelector('.cross');
                  newCross.addEventListener('click', () => {
                     newTag.remove();
                     removeItem(email); // Remove the email and its corresponding id and name from the selectedItems array
                     updateInputValue(); // Update the input values when the tag is removed
                  });
                  updateInputValue(); // Update the input values when a new tag is added
               }

               function updateInputValue() {
                  const emailTags = emailTagsContainer.querySelectorAll('.email');
                  const emails = [];
                  const ids = [];
                  const names = [];
                  emailTags.forEach(tag => {
                     emails.push(tag.textContent);
                     selectedItems.forEach(item => {
                        if (item.email === tag.textContent) {
                           ids.push(item.id);
                           names.push(item.name);
                        }
                     });
                  });
                  // Remove empty values from arrays
                  const filteredEmails = emails.filter(email => email !== '');
                  const filteredIds = ids.filter(id => id !== '');
                  const filteredNames = names.filter(name => name !== '');
                  const emailList = filteredEmails.join(', ');
                  const idList = filteredIds.join(', ');
                  const nameList = filteredNames.join(', ');
                  $("#get_send_mail_value").val(emailList);
                  $("#user-id-multiple").val(idList);
                  $("#user-name-multiple").val(nameList);
               }
               emailTagsContainer.addEventListener('keypress', (event) => {
                  if (event.key === 'Enter' || event.key === ',' || event.key === ';') {
                     event.preventDefault();
                     const input = event.target.innerText.trim();
                     if (input !== '') {
                        addTag(input);
                        event.target.innerText = '';
                     }
                  }
               });

               function removeItem(email) {
                  selectedItems = selectedItems.filter(item => item.email !== email);
               }
            } else {
               $('#No-emails-selected-modal').modal('show');
            }
         });


         $('#Send-Mail-Modal-single').on('show.bs.modal', function (event) {

            var button = $(event.relatedTarget);
            var email = button.data('email');
            var id = button.data('id');
            var name = button.data('name');
            var modal = $(this);

            console.log(id);
            $("#To").val(email);
            $("#user-id-single").val(id);
            $("#user-name-single").val(name);
         });


         
         

         $(document).on("click","#valid-email-btn",function(){
            $("#error-alert").removeClass('d-none');
            $("#msg-error").text("Please Wait.....");
            var selectedEmails = [];

            $('td input:checkbox:checked').not('#selectAllCheckbox').each(function () {
               var row = dataTable.row($(this).closest('tr')).data(); // Get the DataTables row data
               if (row) {
                  selectedEmails.push(row.email);
               }

            });

            const data = {
               emails: selectedEmails.join(',')
            };
            
            
            if (selectedEmails.length > 0) {
               $.ajax({
                  type: "POST",
                  url: ajaxurl,
                  data: {
                     data,
                     action: 'validateEmails',
                  },
                  success: function (response) {
                      $("#error-alert").addClass('d-none');
                      dataTable.ajax.reload(null, false);
                      if (response.data.api_not_found) {
                            $("#error-alert").removeClass('d-none');
                            $("#msg-error").text(response.data.api_not_found);
                      }else if(response.data.api_rate_limit){
                            $("#error-alert").removeClass('d-none');
                            $("#msg-error").text(response.data.api_rate_limit);
                      }else {
                            // Handle other error cases if needed
                            alert('An error occurred.');
                      }
                      
                  }
               });
               console.log(data);
            }else {
               $("#error-alert").addClass('d-none');
               $('#No-user-checkbox-selected-modal').modal('show');
            }
         }) 


         // Upload csv using ajax
       $(document).on("submit", "#csv-upload-form", function (e) {
          e.preventDefault();
         $("#progress").removeClass("d-none");
         $("#progress-bar").addClass("bg-success"); // Remove any previous coloring
         $("#loader").text("Please wait...");
         $("#submit-csv-upload").hide();
          // Create a FormData object to collect form data, including the CSV file
          var formData = new FormData($('#csv-upload-form')[0]);
          
          // Append the CSV file input to the FormData object
          var csvFile = $('#csv-file-input')[0].files[0]; // Assuming your file input has an ID of 'csv-file-input'
          formData.append('csv_file', csvFile); // 'csv_file' is the name you can use to access the file on the server
          
          // Add the 'action' parameter to specify the WordPress AJAX action
          formData.append('action', 'upload_csv_file'); // 'upload_csv_file' is the WordPress AJAX action name
          

          $.ajax({
              url: ajaxurl,
              type: 'POST',
              data: formData,
              contentType: false, // Set content type to false, FormData will take care of it
              processData: false, // Prevent jQuery from processing the data
              success: function (response) {
               $("#progress-bar").removeClass("bg-success");
               $("#progress-bar").addClass("bg-success");
               $("#loader").text("Upload completed successfully!");
               setTimeout(function () {
                   $("#progress").addClass("d-none"); // Hide the progress bar after a delay
                   $("#upload-csv-file").modal('hide');
                   $("#submit-csv-upload").show();
                     dataTable.ajax.reload();
               }, 2000); // Delay in milliseconds (2 seconds in this case)
              },
              error: function (jqXHR, textStatus, errorThrown) {
                  console.log('AJAX Error:', errorThrown);
              },
          });
      });
         
       
        $(document).on("click","#dlt-Email-logs",function(){
           $('#Failed-Email_logs_modal').modal('show');

           $('#dlt-email-date').on('change', function() {
           var selectedDate = $(this).val(); // Get the selected date
           console.log(selectedDate);
           // AJAX request
           $.ajax({
               type: 'POST',
               url: ajaxurl, // WordPress AJAX URL
               data: {
                   action: 'process_date_selection',
                   selected_date: selectedDate
               },
               success: function(response) {
                   // Handle the AJAX response here
                   // Assuming the response is an array of filtered data
                   var filteredData = JSON.parse(response);

                   // Display the filtered data in the <p> tag
                   var $filteredData = $('#filtered-data');
                   $filteredData.empty(); // Clear any previous content
                   if (filteredData.length > 0) {
                       // Create an unordered list to display email addresses
                       var $ul = $('<ul></ul>');

                       // Loop through the filtered data and add email addresses to the list
                       for (var i = 0; i < filteredData.length; i++) {
                           var failedEmails = filteredData[i].failed_emails;

                           // Loop through the failed email addresses for the current date
                           for (var j = 0; j < failedEmails.length; j++) {
                               var $li = $('<li></li>');
                               $li.text(failedEmails[j]);
                               $ul.append($li);
                           }
                       }

                       $filteredData.append($ul);
                   } else {
                       $filteredData.text('No data found for the selected date.');
                   }
               }

             });
           });
        });


        $('#Mail-Sent').on('submit', function(event) {
          event.preventDefault();
          $("#progress-send-mail").removeClass("d-none");
          $("#loader-send-mail").text("Please wait...");
          // Serialize form data
          var formData = new FormData(this);

          // Add the custom action parameter
          formData.append('action', 'custom_send_mail_action');

          // Perform AJAX request
          $.ajax({
              type: 'POST',
              url: ajaxurl, // Use WordPress AJAX URL
              data: formData,
              processData: false,
              contentType: false,
              success: function(response) {
                 console.log(response);
                 
                 $("#progress-send-mail").addClass("d-none");
                 setTimeout(function () {
                     $("#progress-send-mail").addClass("d-none"); // Hide the progress bar after a delay
                     $("#Send-Mail-Modal").modal('hide');
                     $("#error-alert").removeClass("d-none");
                     $("#msg-error").text(response.data.message);
                     dataTable.ajax.reload();
                  }, 2000);

              },
              error: function(xhr, textStatus, errorThrown) {
                  // Handle any errors that occur during the AJAX request
                  console.error(errorThrown);
              }
          });
      });



        $('#Mail-Sent-single').on('submit', function(event) {
          event.preventDefault();
          $("#progress-send-mail-single").removeClass("d-none");
          $("#loader-send-mail-single").text("Please wait...");
          // Serialize form data
          var formData = new FormData(this);

          // Add the custom action parameter
          formData.append('action', 'custom_send_mail_action');

          // Perform AJAX request
          $.ajax({
              type: 'POST',
              url: ajaxurl, // Use WordPress AJAX URL
              data: formData,
              processData: false,
              contentType: false,
              success: function(response) {
                 console.log(response);
                 
                 $("#progress-send-mail-single").addClass("d-none");
                 setTimeout(function () {
                     $("#progress-send-mail-single").addClass("d-none"); // Hide the progress bar after a delay
                     $("#Send-Mail-Modal-single").modal('hide');
                     $("#error-alert").removeClass("d-none");
                     $("#msg-error").text(response.data.message);
                     dataTable.ajax.reload();
                  }, 2000);

              },
              error: function(xhr, textStatus, errorThrown) {
                  // Handle any errors that occur during the AJAX request
                  console.error(errorThrown);
              }
          });
      });



      });
   })(jQuery);