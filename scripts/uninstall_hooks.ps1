param(
    [switch]$CurrentHostOnly
)

$ErrorActionPreference = "Stop"

$profilePath = if ($CurrentHostOnly) { $PROFILE.CurrentUserCurrentHost } else { $PROFILE.CurrentUserAllHosts }
$startMarker = "# >>> project-memory-rules >>>"
$endMarker = "# <<< project-memory-rules <<<"

if (-not (Test-Path $profilePath)) {
    Write-Host "Profile not found: $profilePath"
    exit 0
}

$existing = Get-Content -Path $profilePath -Raw
$pattern = "(?s)$([regex]::Escape($startMarker)).*?$([regex]::Escape($endMarker))"
$cleaned = [regex]::Replace($existing, $pattern, "").TrimEnd()
Set-Content -Path $profilePath -Value $cleaned -Encoding utf8

Write-Host "Removed project-memory-rules hooks from: $profilePath"
Write-Host "Restart PowerShell (or dot-source profile) to clear function bindings."
