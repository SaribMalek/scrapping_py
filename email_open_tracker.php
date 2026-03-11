<?php
declare(strict_types=1);

$dbHost = 'localhost';
$dbUser = 'root';
$dbPass = '';
$logDir = __DIR__ . DIRECTORY_SEPARATOR . 'output';
$logFile = $logDir . DIRECTORY_SEPARATOR . 'email_open_events.csv';

$token = isset($_GET['t']) ? trim((string) $_GET['t']) : '';
$email = isset($_GET['e']) ? trim((string) $_GET['e']) : '';
$openedAt = date('Y-m-d H:i:s');
$clientIp = isset($_SERVER['REMOTE_ADDR']) ? (string) $_SERVER['REMOTE_ADDR'] : '';
$userAgent = isset($_SERVER['HTTP_USER_AGENT']) ? (string) $_SERVER['HTTP_USER_AGENT'] : '';
$referer = isset($_SERVER['HTTP_REFERER']) ? (string) $_SERVER['HTTP_REFERER'] : '';

if (!is_dir($logDir)) {
    @mkdir($logDir, 0777, true);
}

if ($token !== '' || $email !== '') {
    $needsHeader = !file_exists($logFile) || @filesize($logFile) === 0;
    $row = [$openedAt, $email, $token, $clientIp, $userAgent, $referer];
    $stream = fopen('php://temp', 'r+');
    if ($stream !== false) {
        if ($needsHeader) {
            fputcsv($stream, ['opened_at', 'email', 'token', 'ip', 'user_agent', 'referer']);
        }
        fputcsv($stream, $row);
        rewind($stream);
        $csvContent = stream_get_contents($stream);
        fclose($stream);
        if ($csvContent !== false && $csvContent !== '') {
            @file_put_contents($logFile, $csvContent, FILE_APPEND | LOCK_EX);
        }
    }
}

header('Content-Type: image/gif');
header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0');
header('Pragma: no-cache');

echo base64_decode('R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==');
