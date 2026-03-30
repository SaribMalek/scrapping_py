<?php
define('WP_USE_THEMES', false);
$wp_load_path = dirname(dirname(dirname(dirname(__FILE__)))) . '/wp-load.php';
require_once($wp_load_path);

global $wpdb;
$table_name = $wpdb->prefix . 'email_templates';

$draw = $_POST['draw'];
$start = $_POST['start'];
$length = $_POST['length'];
$searchValue = $_POST['search']['value'];

$query = "SELECT id, name FROM $table_name"; // Include the 'id' column

if (!empty($searchValue)) {
    // Use prepared statement to prevent SQL injection
    $query .= $wpdb->prepare(" WHERE name LIKE %s", '%' . $wpdb->esc_like($searchValue) . '%');
}

// Check if length is -1 (All), and adjust the query accordingly
if ($length != -1) {
    $query .= $wpdb->prepare(" LIMIT %d, %d", $start, $length);
}

$data = $wpdb->get_results($query);

$totalRecords = $wpdb->get_var("SELECT COUNT(*) FROM $table_name");

if (!empty($searchValue)) {
    $totalFiltered = $wpdb->get_var($wpdb->prepare("SELECT COUNT(*) FROM $table_name WHERE name LIKE %s", '%' . $wpdb->esc_like($searchValue) . '%'));
} else {
    $totalFiltered = $totalRecords;
}

$response = array(
    "draw" => intval($draw),
    "recordsTotal" => intval($totalRecords),
    "recordsFiltered" => intval($totalFiltered),
    "data" => $data
);

// Set appropriate JSON headers
header('Content-Type: application/json');

echo json_encode($response);
