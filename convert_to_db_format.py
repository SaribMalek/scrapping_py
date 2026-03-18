import csv
import os

input_file = os.path.join(os.path.dirname(__file__), 'output', 'companies_emails.csv')
output_file = os.path.join(os.path.dirname(__file__), 'output', 'companies_db_import.csv')

with open(input_file, newline='', encoding='utf-8') as infile:
    reader = csv.DictReader(infile)
    rows = list(reader)

with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
    fieldnames = ['name', 'email', 'company', 'status']
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        name = row.get('Name', '').strip()
        email = row.get('Mail', '').strip()
        company = name  # Company name is the same as Name in source

        # Skip rows with empty email or obviously invalid emails
        if not email or '@' not in email:
            continue

        writer.writerow({
            'name': name,
            'email': email,
            'company': company,
            'status': 'pending'
        })

print(f"Done! Output saved to: {output_file}")

# Count rows
with open(output_file, newline='', encoding='utf-8') as f:
    count = sum(1 for _ in f) - 1  # subtract header
print(f"Total records exported: {count}")
