<#
Loads .env into the current PowerShell session.
Usage: . .\scripts\set-env.ps1
#>
if (Test-Path -Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -and ($_ -notmatch '^\s*#')) {
            $parts = $_ -split '=', 2
            if ($parts.Length -eq 2) {
                $name = $parts[0].Trim()
                $value = $parts[1].Trim()
                Set-Item -Path "Env:$name" -Value $value
            }
        }
    }
    Write-Host "Loaded .env into session."
} else {
    Write-Host ".env not found. Copy .env.example to .env and edit it first." -ForegroundColor Yellow
}
