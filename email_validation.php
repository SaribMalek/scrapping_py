<?php

declare(strict_types=1);

/**
 * Normalize an email by trimming spaces and lowercasing.
 */
function normalize_email(string $email): string
{
    return strtolower(trim($email));
}

/**
 * Validate email format and reject obvious non-email asset paths.
 */
function is_valid_email(string $email): bool
{
    $email = normalize_email($email);
    if ($email === '') {
        return false;
    }

    $pattern = '/^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$/i';
    if (!preg_match($pattern, $email)) {
        return false;
    }

    $blockedSuffixes = ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css'];
    foreach ($blockedSuffixes as $suffix) {
        if (str_ends_with($email, $suffix)) {
            return false;
        }
    }

    return true;
}

/**
 * Extract domain part from email.
 */
function extract_email_domain(string $email): string
{
    $email = normalize_email($email);
    $parts = explode('@', $email);

    if (count($parts) !== 2) {
        return '';
    }

    return trim($parts[1]);
}

/**
 * Check whether a domain has MX records.
 *
 * @return array{0: bool, 1: string}
 */
function has_mx_record(string $email, array &$domainCache = []): array
{
    $domain = extract_email_domain($email);
    if ($domain === '') {
        return [false, 'Missing email domain'];
    }

    if (array_key_exists($domain, $domainCache)) {
        return $domainCache[$domain];
    }

    try {
        if (function_exists('getmxrr')) {
            $mxHosts = [];
            if (@getmxrr($domain, $mxHosts) && count($mxHosts) > 0) {
                $result = [true, 'Format OK + domain has MX records'];
                $domainCache[$domain] = $result;
                return $result;
            }
        }

        if (function_exists('dns_get_record')) {
            $records = @dns_get_record($domain, DNS_MX);
            if (is_array($records) && count($records) > 0) {
                $result = [true, 'Format OK + domain has MX records'];
                $domainCache[$domain] = $result;
                return $result;
            }
        }

        if (function_exists('checkdnsrr') && @checkdnsrr($domain, 'MX')) {
            $result = [true, 'Format OK + domain has MX records'];
            $domainCache[$domain] = $result;
            return $result;
        }

        $result = [false, 'Domain has no MX records'];
        $domainCache[$domain] = $result;
        return $result;
    } catch (Throwable $e) {
        $result = [false, 'MX lookup failed: ' . $e::class];
        $domainCache[$domain] = $result;
        return $result;
    }
}

/**
 * Final verification result, aligned with Python structure.
 *
 * @return array{valid: bool, reason: string}
 */
function verify_email(string $email, array &$domainCache = []): array
{
    $normalized = normalize_email($email);
    if (!is_valid_email($normalized)) {
        return ['valid' => false, 'reason' => 'Invalid email format'];
    }

    [$hasMx, $reason] = has_mx_record($normalized, $domainCache);
    if (!$hasMx) {
        return ['valid' => false, 'reason' => $reason];
    }

    return ['valid' => true, 'reason' => $reason];
}

/**
 * Extract and de-duplicate valid emails from free text.
 *
 * @return list<string>
 */
function extract_emails(string $raw): array
{
    if (trim($raw) === '') {
        return [];
    }

    $matches = [];
    preg_match_all('/[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}/i', $raw, $matches);

    $clean = [];
    $seen = [];
    foreach ($matches[0] ?? [] as $item) {
        $email = normalize_email($item);
        if (!is_valid_email($email) || isset($seen[$email])) {
            continue;
        }
        $seen[$email] = true;
        $clean[] = $email;
    }

    return $clean;
}

