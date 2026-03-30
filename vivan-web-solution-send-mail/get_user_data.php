<?php
   define('WP_USE_THEMES', false);
   $wp_load_path = dirname(dirname(dirname(dirname(__FILE__)))) . '/wp-load.php';
   require_once($wp_load_path);
   global $wpdb;
   $table_name_send_email = $wpdb->prefix . 'send_email';
   $draw = $_POST['draw'];
   $start = $_POST['start'];
   $length = $_POST['length'];
   $searchValue = $_POST['search']['value'];
   $selectedOption_is_verified = $_POST['columns'][5]['search']['value'];
   $selectedOption_template_info = $_POST['columns'][6]['search']['value'];
   // Define the name of the second table you want to join with
   $table_name_template_tracking = $wpdb->prefix . 'email_template_tracking';
   // Modified SQL query with LEFT JOIN
   $query = "SELECT
       send.id,
       send.name,
       send.type,
       send.email,
       send.is_verified,
       tracking.template_data
   FROM
       $table_name_send_email AS send
   LEFT JOIN
       $table_name_template_tracking AS tracking
   ON
       send.id = tracking.user_id";
   if ($selectedOption_is_verified == "1") {
       $query .= " WHERE send.is_verified = '1'";
   } elseif ($selectedOption_is_verified == "3") {
       $query .= " WHERE send.is_verified = '0'";
   } elseif ($selectedOption_is_verified == "2") {
       $query .= " WHERE send.is_verified = '2'";
   }if($selectedOption_template_info == "not_send"){
       $query .= " WHERE tracking.template_data IS NULL";
   }
   if ($searchValue !== '') {
       $query .= " WHERE send.is_verified = '$searchValue'";
   }
   $query .= " ORDER BY send.id ASC";
   // Check if length is -1 (All), and adjust the query accordingly
   if ($length != -1) {
       $query .= " LIMIT $start, $length";
   }
   $data = $wpdb->get_results($query);
   // Create an incremental counter starting from 1
   $counter = 1;
   foreach ($data as $row) {
       $row->formatted_id = "Show ID " . $counter++;
   }
   // Total records in the wp_send_email table
   $totalRecords = $wpdb->get_var("SELECT COUNT(*) FROM $table_name_send_email");
   if (!empty($searchValue)) {
       // Total filtered records based on the search criteria
       $totalFiltered = $wpdb->get_var("SELECT COUNT(*) FROM $table_name_send_email WHERE name LIKE '%$searchValue%'");
   } else {
       $totalFiltered = $totalRecords;
   }
   $response = array(
       "draw" => intval($draw),
       "recordsTotal" => intval($totalRecords),
       "recordsFiltered" => intval($totalFiltered),
       "data" => $data
   );
   echo json_encode($response);
   ?>