param(
    [string]$Country = "India",
    [int]$FromPage = 1,
    [int]$ToPage = 5
)

if ($FromPage -lt 1 -or $ToPage -lt $FromPage) {
    Write-Error "Invalid page range. Use FromPage >= 1 and ToPage >= FromPage."
    exit 1
}

for ($page = $FromPage; $page -le $ToPage; $page++) {
    Write-Host "Running GoodFirms scrape for $Country page $page..."
    python main.py --source goodfirms --country $Country --start-page $page --max-pages 1
}

