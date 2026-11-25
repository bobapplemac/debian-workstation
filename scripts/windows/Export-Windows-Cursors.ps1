# Export original Windows cursor files for the Debian workstation playbook.
# Run in Windows PowerShell 5.1 or PowerShell 7 as a normal user.
param(
    [string]$OutputPath = (Join-Path $env:USERPROFILE 'Downloads\Windows-Cursors.zip')
)
$ErrorActionPreference = 'Stop'
$Source = Join-Path $env:WINDIR 'Cursors'
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
$Stage = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
try {
    New-Item -ItemType Directory -Path $Stage | Out-Null
    $Files = @(Get-ChildItem -LiteralPath $Source -File | Where-Object { $_.Extension -in '.cur', '.ani', '.svg' })
    if ($Files.Count -eq 0) { throw 'No cursor files found.' }
    foreach ($File in $Files) { Copy-Item -LiteralPath $File.FullName -Destination $Stage }
    New-Item -ItemType Directory -Path (Split-Path -Parent $OutputPath) -Force | Out-Null
    Compress-Archive -Path (Join-Path $Stage '*') -DestinationPath $OutputPath -Force
    Write-Host "Exported $($Files.Count) cursor files to $OutputPath"
} finally {
    if (Test-Path -LiteralPath $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force }
}
