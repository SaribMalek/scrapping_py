<?php
/**
 * Plugin Name: WordPress Email Campaign Tracker
 * Description: Manage contacts, send HTML emails, and track sent/opened status.
 * Version: 2.0.0
 * Author: Codex
 */

declare(strict_types=1);

if (!defined('ABSPATH')) {
    exit;
}

final class WECT_Plugin
{
    private const MENU = 'wect-manager';
    private const NONCE = 'wect_admin_action';
    private const TRACK = 'wect_track';
    private const LOG = 'wect_log';

    public static function init(): void
    {
        add_action('admin_menu', [self::class, 'menu']);
        add_action('admin_enqueue_scripts', [self::class, 'assets']);
        add_action('admin_post_wect_save_template', [self::class, 'save_template']);
        add_action('admin_post_wect_save_contact', [self::class, 'save_contact']);
        add_action('admin_post_wect_delete_contact', [self::class, 'delete_contact']);
        add_action('admin_post_wect_import_csv', [self::class, 'import_csv']);
        add_action('admin_post_wect_send_single', [self::class, 'send_single']);
        add_action('admin_post_wect_send_batch', [self::class, 'send_batch']);
        add_action('admin_post_wect_clear_logs', [self::class, 'clear_logs']);
        add_action('admin_init', [self::class, 'export_csv']);
        add_filter('query_vars', [self::class, 'query_vars']);
        add_action('init', [self::class, 'track_open']);
    }

    public static function activate(): void
    {
        global $wpdb;
        require_once ABSPATH . 'wp-admin/includes/upgrade.php';
        $c = $wpdb->get_charset_collate();

        dbDelta("CREATE TABLE " . self::table('templates') . " (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            template_name VARCHAR(255) NOT NULL,
            email_subject VARCHAR(255) NOT NULL,
            html_content LONGTEXT NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id)
        ) {$c};");

        dbDelta("CREATE TABLE " . self::table('contacts') . " (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            contact_name VARCHAR(255) DEFAULT NULL,
            contact_type VARCHAR(120) DEFAULT NULL,
            email VARCHAR(255) NOT NULL,
            is_verified TINYINT(1) NOT NULL DEFAULT 1,
            template_id BIGINT UNSIGNED DEFAULT NULL,
            sent_count INT NOT NULL DEFAULT 0,
            open_count INT NOT NULL DEFAULT 0,
            last_sent_at DATETIME DEFAULT NULL,
            last_opened_at DATETIME DEFAULT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            UNIQUE KEY uniq_email (email)
        ) {$c};");

        dbDelta("CREATE TABLE " . self::table('logs') . " (
            id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            contact_id BIGINT UNSIGNED NOT NULL,
            template_id BIGINT UNSIGNED DEFAULT NULL,
            email VARCHAR(255) NOT NULL,
            email_subject VARCHAR(255) NOT NULL,
            send_status VARCHAR(20) NOT NULL DEFAULT 'pending',
            sent_at DATETIME DEFAULT NULL,
            opened_at DATETIME DEFAULT NULL,
            open_count INT NOT NULL DEFAULT 0,
            tracking_token VARCHAR(64) DEFAULT NULL,
            error_message TEXT DEFAULT NULL,
            ip_address VARCHAR(64) DEFAULT NULL,
            user_agent TEXT DEFAULT NULL,
            referer TEXT DEFAULT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            PRIMARY KEY (id),
            KEY tracking_token (tracking_token)
        ) {$c};");
    }

    public static function menu(): void
    {
        add_menu_page('Email Campaigns', 'Email Campaigns', 'manage_options', self::MENU, [self::class, 'page'], 'dashicons-email-alt2', 56);
    }

    public static function assets(string $hook): void
    {
        if ($hook !== 'toplevel_page_' . self::MENU) {
            return;
        }
        $css = '.wect{max-width:1380px}.wect-cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:18px 0}.wect-card,.wect-box{background:#fff;border:1px solid #dcdcde;border-radius:8px;padding:18px}.wect-card h3{margin:0 0 8px;font-size:14px;color:#50575e;text-transform:uppercase}.wect-card strong{font-size:30px}.wect-grid{display:grid;grid-template-columns:1.15fr 1fr;gap:18px}.wect-actions,.wect-inline{display:flex;gap:12px;flex-wrap:wrap;align-items:center}.wect-actions{margin:16px 0}.wect-btn{display:inline-flex;align-items:center;padding:10px 16px;border-radius:6px;text-decoration:none;font-weight:600;border:none;cursor:pointer}.wect-blue{background:#1473e6;color:#fff}.wect-green{background:#2da44e;color:#fff}.wect-red{background:#dc3545;color:#fff}.wect-cyan{background:#17a2b8;color:#fff}.wect-outline{background:#fff;color:#dc3545;border:1px solid #dc3545}.wect-badge{display:inline-block;padding:3px 8px;border-radius:4px;color:#fff;font-size:12px;font-weight:700}.wect-g{background:#28a745}.wect-x{background:#6c757d}.wect-b{background:#1473e6}.wect-pager{display:flex;gap:6px;justify-content:flex-end;margin-top:16px}.wect-pager a,.wect-pager span{display:inline-block;padding:8px 12px;background:#fff;border:1px solid #dcdcde;text-decoration:none}.wect-pager .current{background:#1473e6;border-color:#1473e6;color:#fff}@media(max-width:1100px){.wect-cards,.wect-grid{grid-template-columns:1fr 1fr}}@media(max-width:782px){.wect-cards,.wect-grid{grid-template-columns:1fr}}';
        wp_register_style('wect-inline', false);
        wp_enqueue_style('wect-inline');
        wp_add_inline_style('wect-inline', $css);
    }

    public static function page(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }
        $stats = self::stats();
        $filters = self::filters();
        $templates = self::templates();
        $contacts = self::contacts_page($filters);
        $logs = self::logs();
        $editTemplate = isset($_GET['edit_template']) ? self::template(absint($_GET['edit_template'])) : null;
        $editContact = isset($_GET['edit_contact']) ? self::contact(absint($_GET['edit_contact'])) : null;
        ?>
        <div class="wrap wect">
            <h1>Manage Users</h1>
            <?php self::notice(); ?>
            <div class="wect-actions">
                <a class="wect-btn wect-blue" href="#wect-send">Send Mail</a>
                <a class="wect-btn wect-blue" href="#wect-import">Upload CSV</a>
                <a class="wect-btn wect-blue" href="<?php echo esc_url(self::export_url($filters)); ?>">Download CSV</a>
                <a class="wect-btn wect-cyan" href="#wect-contact">Validate Emails</a>
                <a class="wect-btn wect-green" href="#wect-contact">Add New User</a>
                <a class="wect-btn wect-red" href="#wect-template">Add Template</a>
                <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                    <?php wp_nonce_field(self::NONCE); ?>
                    <input type="hidden" name="action" value="wect_clear_logs">
                    <button class="wect-btn wect-outline" type="submit">Trash Email Log&apos;s</button>
                </form>
            </div>

            <div class="wect-cards">
                <div class="wect-card"><h3>Total Contacts</h3><strong><?php echo esc_html((string) $stats['contacts']); ?></strong></div>
                <div class="wect-card"><h3>Verified Emails</h3><strong><?php echo esc_html((string) $stats['verified']); ?></strong></div>
                <div class="wect-card"><h3>Emails Sent</h3><strong><?php echo esc_html((string) $stats['sent']); ?></strong></div>
                <div class="wect-card"><h3>Emails Opened</h3><strong><?php echo esc_html((string) $stats['opened']); ?></strong></div>
            </div>

            <div class="wect-grid">
                <div class="wect-box" id="wect-template">
                    <h2><?php echo $editTemplate ? 'Edit Template' : 'Create Template'; ?></h2>
                    <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                        <?php wp_nonce_field(self::NONCE); ?>
                        <input type="hidden" name="action" value="wect_save_template">
                        <input type="hidden" name="template_id" value="<?php echo esc_attr((string) ($editTemplate->id ?? 0)); ?>">
                        <table class="form-table">
                            <tr><th><label for="wect_template_name">Template Name</label></th><td><input class="regular-text" id="wect_template_name" name="template_name" value="<?php echo esc_attr($editTemplate->template_name ?? ''); ?>" required></td></tr>
                            <tr><th><label for="wect_email_subject">Email Subject</label></th><td><input class="regular-text" id="wect_email_subject" name="email_subject" value="<?php echo esc_attr($editTemplate->email_subject ?? ''); ?>" required></td></tr>
                            <tr><th><label for="wect_html_content">HTML Content</label></th><td><textarea class="large-text code" style="min-height:240px" id="wect_html_content" name="html_content" required><?php echo esc_textarea($editTemplate->html_content ?? ''); ?></textarea><p class="description">Use <code>{company_name}</code> and <code>{email}</code>. Tracking pixel is added automatically.</p></td></tr>
                        </table>
                        <?php submit_button($editTemplate ? 'Update Template' : 'Save Template'); ?>
                    </form>
                </div>

                <div class="wect-box" id="wect-contact">
                    <h2><?php echo $editContact ? 'Edit User' : 'Add New User'; ?></h2>
                    <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                        <?php wp_nonce_field(self::NONCE); ?>
                        <input type="hidden" name="action" value="wect_save_contact">
                        <input type="hidden" name="contact_id" value="<?php echo esc_attr((string) ($editContact->id ?? 0)); ?>">
                        <table class="form-table">
                            <tr><th><label for="wect_contact_name">Name</label></th><td><input class="regular-text" id="wect_contact_name" name="contact_name" value="<?php echo esc_attr($editContact->contact_name ?? ''); ?>" required></td></tr>
                            <tr><th><label for="wect_contact_type">Type</label></th><td><input class="regular-text" id="wect_contact_type" name="contact_type" value="<?php echo esc_attr($editContact->contact_type ?? ''); ?>"></td></tr>
                            <tr><th><label for="wect_contact_email">Email</label></th><td><input class="regular-text" type="email" id="wect_contact_email" name="email" value="<?php echo esc_attr($editContact->email ?? ''); ?>" required></td></tr>
                            <tr><th><label for="wect_is_verified">Is Verified</label></th><td><select id="wect_is_verified" name="is_verified"><option value="1" <?php selected((int) ($editContact->is_verified ?? 1), 1); ?>>Verified</option><option value="0" <?php selected((int) ($editContact->is_verified ?? 1), 0); ?>>Not Verified</option></select></td></tr>
                            <tr><th><label for="wect_template_id">Template</label></th><td><select id="wect_template_id" name="template_id"><option value="">Select Template</option><?php foreach ($templates as $template) : ?><option value="<?php echo esc_attr((string) $template->id); ?>" <?php selected((int) ($editContact->template_id ?? 0), (int) $template->id); ?>><?php echo esc_html($template->template_name); ?></option><?php endforeach; ?></select></td></tr>
                        </table>
                        <?php submit_button($editContact ? 'Update User' : 'Add User'); ?>
                    </form>

                    <hr>

                    <h2 id="wect-import">Upload CSV</h2>
                    <form method="post" enctype="multipart/form-data" action="<?php echo esc_url(admin_url('admin-post.php')); ?>">
                        <?php wp_nonce_field(self::NONCE); ?>
                        <input type="hidden" name="action" value="wect_import_csv">
                        <p><input type="file" name="csv_file" accept=".csv" required></p>
                        <p class="description">CSV columns: <code>name</code>, <code>type</code>, <code>email</code>, <code>is_verified</code>, <code>template_id</code>.</p>
                        <?php submit_button('Import CSV', 'secondary'); ?>
                    </form>
                </div>
            </div>

            <div class="wect-box" id="wect-send" style="margin-top:18px">
                <h2>Send Mail</h2>
                <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>" class="wect-inline">
                    <?php wp_nonce_field(self::NONCE); ?>
                    <input type="hidden" name="action" value="wect_send_batch">
                    <label>Batch Size <input type="number" name="batch_size" min="1" max="500" value="50" required></label>
                    <label><input type="checkbox" name="verified_only" value="1" checked> Verified only</label>
                    <button class="button button-primary" type="submit">Send Next Batch</button>
                </form>
            </div>
            <form method="get" action="<?php echo esc_url(admin_url('admin.php')); ?>">
                <input type="hidden" name="page" value="<?php echo esc_attr(self::MENU); ?>">
                <div class="wect-actions">
                    <label>Go to Page: <input type="number" min="1" name="paged" value="<?php echo esc_attr((string) $filters['paged']); ?>" style="width:90px"></label>
                    <select name="is_verified"><option value="">-- Filter is verified --</option><option value="1" <?php selected($filters['is_verified'], '1'); ?>>Verified</option><option value="0" <?php selected($filters['is_verified'], '0'); ?>>Not Verified</option></select>
                    <select name="template_id"><option value="">-- Filter Template --</option><?php foreach ($templates as $template) : ?><option value="<?php echo esc_attr((string) $template->id); ?>" <?php selected($filters['template_id'], (string) $template->id); ?>><?php echo esc_html($template->template_name); ?></option><?php endforeach; ?></select>
                    <select name="per_page"><option value="5" <?php selected($filters['per_page'], 5); ?>>Show 5 entries</option><option value="10" <?php selected($filters['per_page'], 10); ?>>Show 10 entries</option><option value="20" <?php selected($filters['per_page'], 20); ?>>Show 20 entries</option><option value="50" <?php selected($filters['per_page'], 50); ?>>Show 50 entries</option></select>
                    <label>Search: <input type="search" name="s" value="<?php echo esc_attr($filters['search']); ?>"></label>
                    <button class="button" type="submit">Apply</button>
                </div>
            </form>
            <div class="wect-box">
                <table class="widefat striped">
                    <thead><tr><th>ID</th><th>Name</th><th>Type</th><th>Email</th><th>Is verified</th><th>Template Info</th><th>Sent</th><th>Opened</th><th>Operation</th></tr></thead>
                    <tbody>
                    <?php if (!$contacts['rows']) : ?>
                        <tr><td colspan="9">No contacts found.</td></tr>
                    <?php else : foreach ($contacts['rows'] as $contact) : ?>
                        <tr>
                            <td><?php echo esc_html((string) $contact->id); ?></td>
                            <td><?php echo esc_html($contact->contact_name ?: '-'); ?></td>
                            <td><?php echo esc_html($contact->contact_type ?: '-'); ?></td>
                            <td><?php echo esc_html($contact->email); ?></td>
                            <td><span class="wect-badge <?php echo (int) $contact->is_verified === 1 ? 'wect-g' : 'wect-x'; ?>"><?php echo (int) $contact->is_verified === 1 ? 'Verified' : 'Unverified'; ?></span></td>
                            <td><?php if (!empty($contact->template_name)) : ?><span class="wect-badge wect-b"><?php echo esc_html($contact->template_name); ?></span><?php else : ?>-<?php endif; ?></td>
                            <td><?php echo esc_html((string) $contact->sent_count); ?></td>
                            <td><?php echo esc_html((string) $contact->open_count); ?></td>
                            <td>
                                <div class="wect-inline">
                                    <a class="button button-primary" href="<?php echo esc_url(admin_url('admin.php?page=' . self::MENU . '&edit_contact=' . $contact->id . '#wect-contact')); ?>">Edit</a>
                                    <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><?php wp_nonce_field(self::NONCE); ?><input type="hidden" name="action" value="wect_delete_contact"><input type="hidden" name="contact_id" value="<?php echo esc_attr((string) $contact->id); ?>"><button class="button" type="submit">Delete</button></form>
                                    <form method="post" action="<?php echo esc_url(admin_url('admin-post.php')); ?>"><?php wp_nonce_field(self::NONCE); ?><input type="hidden" name="action" value="wect_send_single"><input type="hidden" name="contact_id" value="<?php echo esc_attr((string) $contact->id); ?>"><button class="button button-secondary" type="submit">Send</button></form>
                                </div>
                            </td>
                        </tr>
                    <?php endforeach; endif; ?>
                    </tbody>
                </table>
                <p>Showing <?php echo esc_html((string) $contacts['from']); ?> to <?php echo esc_html((string) $contacts['to']); ?> of <?php echo esc_html((string) $contacts['total']); ?> entries</p>
                <?php self::pager($contacts['pages'], $filters); ?>
            </div>
            <div class="wect-box" style="margin-top:18px">
                <h2>Recent Email Logs</h2>
                <table class="widefat striped">
                    <thead><tr><th>ID</th><th>Email</th><th>Subject</th><th>Status</th><th>Sent At</th><th>Opened At</th><th>Open Count</th></tr></thead>
                    <tbody>
                    <?php if (!$logs) : ?>
                        <tr><td colspan="7">No logs yet.</td></tr>
                    <?php else : foreach ($logs as $log) : ?>
                        <tr><td><?php echo esc_html((string) $log->id); ?></td><td><?php echo esc_html($log->email); ?></td><td><?php echo esc_html($log->email_subject); ?></td><td><?php echo esc_html(ucfirst($log->send_status)); ?></td><td><?php echo esc_html($log->sent_at ?: '-'); ?></td><td><?php echo esc_html($log->opened_at ?: '-'); ?></td><td><?php echo esc_html((string) $log->open_count); ?></td></tr>
                    <?php endforeach; endif; ?>
                    </tbody>
                </table>
            </div>
        </div>
        <?php
    }

    public static function save_template(): void
    {
        self::guard();
        global $wpdb;
        $id = absint($_POST['template_id'] ?? 0);
        $data = ['template_name' => sanitize_text_field(wp_unslash($_POST['template_name'] ?? '')), 'email_subject' => sanitize_text_field(wp_unslash($_POST['email_subject'] ?? '')), 'html_content' => (string) wp_unslash($_POST['html_content'] ?? ''), 'updated_at' => current_time('mysql')];
        if ($data['template_name'] === '' || $data['email_subject'] === '' || trim($data['html_content']) === '') {
            self::redirect('error', 'Template name, subject, and HTML are required.');
        }
        if ($id > 0) {
            $wpdb->update(self::table('templates'), $data, ['id' => $id]);
        } else {
            $data['created_at'] = current_time('mysql');
            $wpdb->insert(self::table('templates'), $data);
        }
        self::redirect('success', 'Template saved.');
    }

    public static function save_contact(): void
    {
        self::guard();
        global $wpdb;
        $id = absint($_POST['contact_id'] ?? 0);
        $email = sanitize_email(wp_unslash($_POST['email'] ?? ''));
        if (!$email || !is_email($email)) {
            self::redirect('error', 'Valid email is required.');
        }
        $data = ['contact_name' => sanitize_text_field(wp_unslash($_POST['contact_name'] ?? '')), 'contact_type' => sanitize_text_field(wp_unslash($_POST['contact_type'] ?? '')), 'email' => $email, 'is_verified' => absint($_POST['is_verified'] ?? 0), 'template_id' => !empty($_POST['template_id']) ? absint($_POST['template_id']) : null, 'updated_at' => current_time('mysql')];
        if ($id > 0) {
            $wpdb->update(self::table('contacts'), $data, ['id' => $id]);
        } else {
            $data['created_at'] = current_time('mysql');
            $ok = $wpdb->insert(self::table('contacts'), $data);
            if (!$ok) {
                self::redirect('error', 'Contact could not be saved. Email may already exist.');
            }
        }
        self::redirect('success', 'Contact saved.');
    }

    public static function delete_contact(): void
    {
        self::guard();
        global $wpdb;
        $id = absint($_POST['contact_id'] ?? 0);
        if ($id > 0) {
            $wpdb->delete(self::table('contacts'), ['id' => $id]);
        }
        self::redirect('success', 'Contact deleted.');
    }

    public static function import_csv(): void
    {
        self::guard();
        global $wpdb;
        if (empty($_FILES['csv_file']['tmp_name'])) {
            self::redirect('error', 'CSV file is required.');
        }
        $h = fopen($_FILES['csv_file']['tmp_name'], 'r');
        if ($h === false) {
            self::redirect('error', 'Could not open CSV file.');
        }
        $header = fgetcsv($h);
        if (!$header) {
            fclose($h);
            self::redirect('error', 'CSV header row is missing.');
        }
        $map = [];
        foreach ($header as $i => $col) {
            $map[strtolower(trim((string) $col))] = $i;
        }
        $count = 0;
        while (($row = fgetcsv($h)) !== false) {
            $email = sanitize_email(self::csv($row, $map, ['email']));
            if (!$email || !is_email($email)) {
                continue;
            }
            $data = ['contact_name' => sanitize_text_field(self::csv($row, $map, ['name', 'contact_name'])), 'contact_type' => sanitize_text_field(self::csv($row, $map, ['type', 'contact_type'])), 'email' => $email, 'is_verified' => self::truthy(self::csv($row, $map, ['is_verified'])) ? 1 : 0, 'template_id' => ($tid = absint(self::csv($row, $map, ['template_id']))) > 0 ? $tid : null, 'updated_at' => current_time('mysql')];
            $existing = (int) $wpdb->get_var($wpdb->prepare("SELECT id FROM " . self::table('contacts') . " WHERE email = %s LIMIT 1", $email));
            if ($existing > 0) {
                $wpdb->update(self::table('contacts'), $data, ['id' => $existing]);
            } else {
                $data['created_at'] = current_time('mysql');
                $wpdb->insert(self::table('contacts'), $data);
            }
            $count++;
        }
        fclose($h);
        self::redirect('success', "CSV import complete. Imported {$count} rows.");
    }

    public static function send_single(): void
    {
        self::guard();
        $contact = self::contact_with_template(absint($_POST['contact_id'] ?? 0));
        if (!$contact || empty($contact->template_id)) {
            self::redirect('error', 'Contact or template not found.');
        }
        $ok = self::send_contact($contact);
        self::redirect($ok ? 'success' : 'error', $ok ? 'Email sent.' : 'Email failed.');
    }

    public static function send_batch(): void
    {
        self::guard();
        global $wpdb;
        $limit = max(1, min(500, absint($_POST['batch_size'] ?? 50)));
        $where = ['c.template_id IS NOT NULL'];
        if (!empty($_POST['verified_only'])) {
            $where[] = 'c.is_verified = 1';
        }
        $sql = "SELECT c.*,t.email_subject,t.html_content FROM " . self::table('contacts') . " c LEFT JOIN " . self::table('templates') . " t ON t.id=c.template_id WHERE " . implode(' AND ', $where) . " ORDER BY c.id ASC LIMIT %d";
        $rows = $wpdb->get_results($wpdb->prepare($sql, $limit));
        if (!$rows) {
            self::redirect('success', 'No contacts available to send.');
        }
        $sent = 0;
        $failed = 0;
        foreach ($rows as $row) {
            if (self::send_contact($row)) {
                $sent++;
            } else {
                $failed++;
            }
        }
        self::redirect('success', "Batch complete. Sent {$sent}, failed {$failed}.");
    }

    public static function clear_logs(): void
    {
        self::guard();
        global $wpdb;
        $wpdb->query("TRUNCATE TABLE " . self::table('logs'));
        self::redirect('success', 'Email logs cleared.');
    }

    public static function export_csv(): void
    {
        if (!is_admin() || !current_user_can('manage_options')) {
            return;
        }
        if (empty($_GET['page']) || $_GET['page'] !== self::MENU || empty($_GET['wect_export'])) {
            return;
        }
        $page = self::contacts_page(array_merge(self::filters(), ['paged' => 1, 'per_page' => 100000]));
        nocache_headers();
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename="wect-contacts.csv"');
        $out = fopen('php://output', 'w');
        if ($out === false) {
            exit;
        }
        fputcsv($out, ['id', 'name', 'type', 'email', 'is_verified', 'template', 'sent_count', 'open_count', 'last_sent_at', 'last_opened_at']);
        foreach ($page['rows'] as $row) {
            fputcsv($out, [$row->id, $row->contact_name, $row->contact_type, $row->email, $row->is_verified, $row->template_name, $row->sent_count, $row->open_count, $row->last_sent_at, $row->last_opened_at]);
        }
        fclose($out);
        exit;
    }

    public static function query_vars(array $vars): array
    {
        $vars[] = self::TRACK;
        $vars[] = self::LOG;
        return $vars;
    }

    public static function track_open(): void
    {
        if ((string) get_query_var(self::TRACK) !== '1') {
            return;
        }
        global $wpdb;
        $id = absint(get_query_var(self::LOG));
        if ($id > 0) {
            $log = $wpdb->get_row($wpdb->prepare("SELECT * FROM " . self::table('logs') . " WHERE id = %d LIMIT 1", $id));
            if ($log) {
                $now = current_time('mysql');
                $wpdb->update(self::table('logs'), ['open_count' => (int) $log->open_count + 1, 'opened_at' => $now, 'ip_address' => self::ip(), 'user_agent' => isset($_SERVER['HTTP_USER_AGENT']) ? sanitize_text_field(wp_unslash($_SERVER['HTTP_USER_AGENT'])) : '', 'referer' => isset($_SERVER['HTTP_REFERER']) ? esc_url_raw(wp_unslash($_SERVER['HTTP_REFERER'])) : '', 'updated_at' => $now], ['id' => $id]);
                $wpdb->query($wpdb->prepare("UPDATE " . self::table('contacts') . " SET open_count=open_count+1,last_opened_at=%s,updated_at=%s WHERE id=%d", $now, $now, (int) $log->contact_id));
            }
        }
        nocache_headers();
        header('Content-Type: image/gif');
        echo base64_decode('R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==');
        exit;
    }

    private static function send_contact(object $contact): bool
    {
        global $wpdb;
        if (empty($contact->html_content) || empty($contact->email_subject)) {
            return false;
        }
        $now = current_time('mysql');
        $token = wp_generate_password(32, false, false);
        $inserted = $wpdb->insert(self::table('logs'), ['contact_id' => (int) $contact->id, 'template_id' => !empty($contact->template_id) ? (int) $contact->template_id : null, 'email' => $contact->email, 'email_subject' => $contact->email_subject, 'send_status' => 'pending', 'tracking_token' => $token, 'created_at' => $now, 'updated_at' => $now]);
        if (!$inserted) {
            return false;
        }
        $logId = (int) $wpdb->insert_id;
        $url = add_query_arg([self::TRACK => '1', self::LOG => $logId], home_url('/'));
        $html = str_replace(['{company_name}', '{email}'], [esc_html($contact->contact_name ?: 'Team'), esc_html($contact->email)], (string) $contact->html_content);
        $pixel = '<img src="' . esc_url($url) . '" alt="" width="1" height="1" style="display:block;width:1px;height:1px;border:0;opacity:0;" />';
        $html = stripos($html, '</body>') !== false ? (preg_replace('/<\/body>/i', $pixel . '</body>', $html, 1) ?: ($html . $pixel)) : ($html . $pixel);
        add_filter('wp_mail_content_type', [self::class, 'mail_type']);
        $ok = wp_mail($contact->email, $contact->email_subject, $html);
        remove_filter('wp_mail_content_type', [self::class, 'mail_type']);
        if ($ok) {
            $wpdb->update(self::table('logs'), ['send_status' => 'sent', 'sent_at' => $now, 'updated_at' => $now], ['id' => $logId]);
            $wpdb->query($wpdb->prepare("UPDATE " . self::table('contacts') . " SET sent_count=sent_count+1,last_sent_at=%s,updated_at=%s WHERE id=%d", $now, $now, (int) $contact->id));
            return true;
        }
        $wpdb->update(self::table('logs'), ['send_status' => 'failed', 'error_message' => 'wp_mail returned false', 'updated_at' => $now], ['id' => $logId]);
        return false;
    }

    public static function mail_type(): string
    {
        return 'text/html';
    }

    private static function stats(): array
    {
        global $wpdb;
        return ['contacts' => (int) $wpdb->get_var("SELECT COUNT(*) FROM " . self::table('contacts')), 'verified' => (int) $wpdb->get_var("SELECT COUNT(*) FROM " . self::table('contacts') . " WHERE is_verified=1"), 'sent' => (int) $wpdb->get_var("SELECT COUNT(*) FROM " . self::table('logs') . " WHERE send_status='sent'"), 'opened' => (int) $wpdb->get_var("SELECT COUNT(*) FROM " . self::table('logs') . " WHERE open_count>0")];
    }

    private static function filters(): array
    {
        $per = absint($_GET['per_page'] ?? 10);
        if (!in_array($per, [5, 10, 20, 50, 100000], true)) {
            $per = 10;
        }
        return ['search' => sanitize_text_field(wp_unslash($_GET['s'] ?? '')), 'is_verified' => isset($_GET['is_verified']) ? sanitize_text_field(wp_unslash($_GET['is_verified'])) : '', 'template_id' => isset($_GET['template_id']) ? sanitize_text_field(wp_unslash($_GET['template_id'])) : '', 'paged' => max(1, absint($_GET['paged'] ?? 1)), 'per_page' => $per];
    }

    private static function contacts_page(array $filters): array
    {
        global $wpdb;
        $where = ['1=1'];
        $params = [];
        if ($filters['search'] !== '') {
            $like = '%' . $wpdb->esc_like($filters['search']) . '%';
            $where[] = '(c.contact_name LIKE %s OR c.contact_type LIKE %s OR c.email LIKE %s)';
            array_push($params, $like, $like, $like);
        }
        if ($filters['is_verified'] !== '') {
            $where[] = 'c.is_verified=%d';
            $params[] = (int) $filters['is_verified'];
        }
        if ($filters['template_id'] !== '') {
            $where[] = 'c.template_id=%d';
            $params[] = (int) $filters['template_id'];
        }
        $whereSql = implode(' AND ', $where);
        $countSql = "SELECT COUNT(*) FROM " . self::table('contacts') . " c WHERE {$whereSql}";
        $total = $params ? (int) $wpdb->get_var($wpdb->prepare($countSql, ...$params)) : (int) $wpdb->get_var($countSql);
        $offset = ($filters['paged'] - 1) * $filters['per_page'];
        $rowsSql = "SELECT c.*,t.template_name FROM " . self::table('contacts') . " c LEFT JOIN " . self::table('templates') . " t ON t.id=c.template_id WHERE {$whereSql} ORDER BY c.id ASC LIMIT %d OFFSET %d";
        $rows = $wpdb->get_results($wpdb->prepare($rowsSql, ...array_merge($params, [$filters['per_page'], $offset])));
        return ['rows' => $rows, 'total' => $total, 'pages' => max(1, (int) ceil($total / max(1, $filters['per_page']))), 'from' => $total ? $offset + 1 : 0, 'to' => $total ? min($total, $offset + count($rows)) : 0];
    }

    private static function logs(): array
    {
        global $wpdb;
        return $wpdb->get_results("SELECT * FROM " . self::table('logs') . " ORDER BY id DESC LIMIT 20");
    }

    private static function templates(): array
    {
        global $wpdb;
        return $wpdb->get_results("SELECT * FROM " . self::table('templates') . " ORDER BY template_name ASC");
    }

    private static function template(int $id)
    {
        global $wpdb;
        return $id > 0 ? $wpdb->get_row($wpdb->prepare("SELECT * FROM " . self::table('templates') . " WHERE id=%d LIMIT 1", $id)) : null;
    }

    private static function contact(int $id)
    {
        global $wpdb;
        return $id > 0 ? $wpdb->get_row($wpdb->prepare("SELECT * FROM " . self::table('contacts') . " WHERE id=%d LIMIT 1", $id)) : null;
    }

    private static function contact_with_template(int $id)
    {
        global $wpdb;
        return $id > 0 ? $wpdb->get_row($wpdb->prepare("SELECT c.*,t.email_subject,t.html_content FROM " . self::table('contacts') . " c LEFT JOIN " . self::table('templates') . " t ON t.id=c.template_id WHERE c.id=%d LIMIT 1", $id)) : null;
    }

    private static function pager(int $pages, array $filters): void
    {
        if ($pages <= 1) {
            return;
        }
        echo '<div class="wect-pager">';
        for ($i = 1; $i <= $pages; $i++) {
            $url = add_query_arg(['page' => self::MENU, 'paged' => $i, 's' => $filters['search'] ?: null, 'is_verified' => $filters['is_verified'] !== '' ? $filters['is_verified'] : null, 'template_id' => $filters['template_id'] !== '' ? $filters['template_id'] : null, 'per_page' => $filters['per_page']], admin_url('admin.php'));
            echo $i === $filters['paged'] ? '<span class="current">' . esc_html((string) $i) . '</span>' : '<a href="' . esc_url($url) . '">' . esc_html((string) $i) . '</a>';
        }
        echo '</div>';
    }

    private static function export_url(array $filters): string
    {
        return add_query_arg(['page' => self::MENU, 'wect_export' => '1', 's' => $filters['search'] ?: null, 'is_verified' => $filters['is_verified'] !== '' ? $filters['is_verified'] : null, 'template_id' => $filters['template_id'] !== '' ? $filters['template_id'] : null], admin_url('admin.php'));
    }

    private static function csv(array $row, array $map, array $keys): string
    {
        foreach ($keys as $key) {
            if (isset($map[$key], $row[$map[$key]])) {
                return trim((string) $row[$map[$key]]);
            }
        }
        return '';
    }

    private static function truthy(string $value): bool
    {
        return in_array(strtolower(trim($value)), ['1', 'true', 'yes', 'verified'], true);
    }

    private static function notice(): void
    {
        if (empty($_GET['wect_notice'])) {
            return;
        }
        $type = sanitize_key(wp_unslash($_GET['wect_notice_type'] ?? 'success'));
        $class = $type === 'error' ? 'notice notice-error' : 'notice notice-success';
        echo '<div class="' . esc_attr($class) . '"><p>' . esc_html(wp_unslash($_GET['wect_notice'])) . '</p></div>';
    }

    private static function redirect(string $type, string $message): void
    {
        $url = add_query_arg(['page' => self::MENU, 'wect_notice' => rawurlencode($message), 'wect_notice_type' => $type], admin_url('admin.php'));
        wp_safe_redirect($url);
        exit;
    }

    private static function guard(): void
    {
        if (!current_user_can('manage_options')) {
            wp_die('Unauthorized');
        }
        check_admin_referer(self::NONCE);
    }

    private static function ip(): string
    {
        foreach (['HTTP_CF_CONNECTING_IP', 'HTTP_X_FORWARDED_FOR', 'REMOTE_ADDR'] as $key) {
            if (empty($_SERVER[$key])) {
                continue;
            }
            $raw = wp_unslash($_SERVER[$key]);
            foreach (array_map('trim', explode(',', $raw)) as $part) {
                if (filter_var($part, FILTER_VALIDATE_IP)) {
                    return $part;
                }
            }
        }
        return '';
    }

    private static function table(string $suffix): string
    {
        global $wpdb;
        return $wpdb->prefix . 'wect_' . $suffix;
    }
}

register_activation_hook(__FILE__, ['WECT_Plugin', 'activate']);
WECT_Plugin::init();
