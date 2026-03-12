# WordPress Email Campaign Tracker

Drop this folder into `wp-content/plugins/` and activate the plugin.

What it does:

- create campaigns with HTML email content
- import recipients in `Company Name|email@example.com` format
- send batches with `wp_mail()`
- track sent status per recipient
- track opens through a WordPress pixel endpoint

Notes:

- the plugin uses WordPress `wp_mail()`
- for reliable delivery, use a proper SMTP plugin/config in WordPress
- open tracking only works if the site is publicly reachable and the recipient loads images
- the plugin injects the tracking pixel automatically before `</body>`
