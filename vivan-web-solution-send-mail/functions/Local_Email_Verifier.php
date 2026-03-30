<?php

if (!defined('ABSPATH')) {
    exit;
}

class Vivan_Local_Email_Verifier
{
    public static function normalize_email(string $email): string
    {
        $email = str_replace(["\xc2\xa0", 'Â', ' '], '', trim($email));
        $email = str_replace(['(at)', '[at]', '(a)', '#'], '@', $email);
        $email = str_replace(['(dot)'], '.', $email);

        return strtolower(trim($email));
    }

    public static function is_valid_format(string $email): bool
    {
        $normalized = self::normalize_email($email);

        if ($normalized === '') {
            return false;
        }

        if (!filter_var($normalized, FILTER_VALIDATE_EMAIL)) {
            return false;
        }

        $blocked_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css'];
        foreach ($blocked_extensions as $extension) {
            if (str_ends_with($normalized, $extension)) {
                return false;
            }
        }

        return true;
    }

    public static function has_mx_record(string $email): array
    {
        $normalized = self::normalize_email($email);
        $parts = explode('@', $normalized);
        $domain = isset($parts[1]) ? trim($parts[1]) : '';

        if ($domain === '') {
            return [false, 'Missing email domain'];
        }

        if (function_exists('checkdnsrr') && checkdnsrr($domain, 'MX')) {
            return [true, 'Format OK + domain has MX records'];
        }

        if (function_exists('checkdnsrr') && checkdnsrr($domain, 'A')) {
            return [true, 'Format OK + domain has DNS records'];
        }

        return [false, 'Domain has no MX records'];
    }

    public static function verify_email(string $email): array
    {
        $normalized = self::normalize_email($email);

        if (!self::is_valid_format($normalized)) {
            return [
                'email' => $normalized,
                'valid' => false,
                'reason' => 'Invalid email format',
            ];
        }

        [$has_mx_record, $reason] = self::has_mx_record($normalized);

        return [
            'email' => $normalized,
            'valid' => $has_mx_record,
            'reason' => $reason,
        ];
    }

    public static function verify_many(array $emails): array
    {
        $results = [];
        $seen = [];

        foreach ($emails as $email) {
            $normalized = self::normalize_email((string) $email);

            if ($normalized === '' || isset($seen[$normalized])) {
                continue;
            }

            $seen[$normalized] = true;
            $results[] = self::verify_email($normalized);
        }

        return $results;
    }
}

function vivan_local_email_verifier_log_invalid(array $failed_emails): void
{
    if (empty($failed_emails)) {
        return;
    }

    $log_file_path = dirname(plugin_dir_path(__FILE__)) . '/failed_emails.json';
    $date = current_time('Y-m-d');
    $existing_data = [];

    if (file_exists($log_file_path)) {
        $decoded = json_decode((string) file_get_contents($log_file_path), true);
        if (is_array($decoded)) {
            $existing_data = $decoded;
        }
    }

    $found = false;
    foreach ($existing_data as &$item) {
        if (($item['date'] ?? '') === $date) {
            $item['failed_emails'] = array_values(array_unique(array_merge(
                $item['failed_emails'] ?? [],
                $failed_emails
            )));
            $found = true;
            break;
        }
    }
    unset($item);

    if (!$found) {
        $existing_data[] = [
            'date' => $date,
            'failed_emails' => array_values(array_unique($failed_emails)),
        ];
    }

    file_put_contents($log_file_path, wp_json_encode($existing_data, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
}

add_action('wp_ajax_validateEmailsLocal', 'vivan_validate_emails_local_ajax_handler');
add_action('wp_ajax_nopriv_validateEmailsLocal', 'vivan_validate_emails_local_ajax_handler');

function vivan_validate_emails_local_ajax_handler(): void
{
    if (($_POST['action'] ?? '') !== 'validateEmailsLocal') {
        wp_send_json_error(['message' => 'Invalid action.']);
    }

    $raw_emails = (string) ($_POST['data']['emails'] ?? '');
    $emails = array_filter(array_map('trim', explode(',', $raw_emails)));
    $results = Vivan_Local_Email_Verifier::verify_many($emails);

    global $wpdb;
    $failed_emails = [];

    foreach ($results as $result) {
        if (!empty($result['valid'])) {
            $wpdb->update(
                $wpdb->prefix . 'send_email',
                ['is_verified' => 1],
                ['email' => $result['email']]
            );
            continue;
        }

        $failed_emails[] = $result['email'];
        $wpdb->update(
            $wpdb->prefix . 'send_email',
            ['is_verified' => 0],
            ['email' => $result['email']]
        );
    }

    vivan_local_email_verifier_log_invalid($failed_emails);

    wp_send_json_success([
        'message' => 'Local email validation completed.',
        'results' => $results,
        'invalid_emails' => $failed_emails,
    ]);
}
