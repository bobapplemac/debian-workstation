# Export selected supplemental Windows fonts for browser/document compatibility.
# Only export fonts you are licensed to use on the destination system.
# Run in Windows PowerShell 5.1 or PowerShell 7 as a normal user.
param(
    [string]$OutputPath = (Join-Path $env:USERPROFILE 'Downloads\Windows-Fonts.zip')
)
$ErrorActionPreference = 'Stop'
$OutputPath = [IO.Path]::GetFullPath($OutputPath)
# Match known Windows font filenames, including weight/style variants.
# Debian's ttf-mscorefonts-installer supplies the classic web fonts separately.
$Patterns = @(
    'segoeui*', 'segui*', 'seguivar*', 'tahoma*', 'calibri*', 'cambria*',
    'candara*', 'consola*', 'constan*', 'corbel*', 'aptos*',
    'cascadiacode*', 'cascadiamono*', 'cascadia code*', 'cascadia mono*',
    'lucon*', 'pala*', 'framd*', 'bahnschrift*', 'micross*'
)
# Preserve Debian's emoji, symbol and icon font fallback behavior.
$Excluded = @('seguiemj*', 'seguisym*', 'seguihis*', 'segmdl2*', 'segoeuiemoji*', 'segoeuisymbol*', 'segoeuihistoric*', 'segoefl*')
$Sources = @((Join-Path $env:WINDIR 'Fonts'), (Join-Path $env:LOCALAPPDATA 'Microsoft\Windows\Fonts'))
$Stage = Join-Path ([IO.Path]::GetTempPath()) ([guid]::NewGuid().ToString())
try {
    New-Item -ItemType Directory -Path $Stage | Out-Null
    foreach ($Source in $Sources) {
        if (-not (Test-Path -LiteralPath $Source -PathType Container)) { continue }
        foreach ($File in (Get-ChildItem -LiteralPath $Source -File)) {
            if ($File.Extension -notin '.ttf', '.otf', '.ttc', '.otc') { continue }
            $Name = $File.Name
            if (-not ($Patterns | Where-Object { $Name -like $_ })) { continue }
            if ($Excluded | Where-Object { $Name -like $_ }) { continue }
            $Target = Join-Path $Stage $Name
            if (Test-Path -LiteralPath $Target) {
                if ((Get-FileHash -LiteralPath $Target).Hash -ne (Get-FileHash -LiteralPath $File.FullName).Hash) {
                    Write-Warning "Conflicting filename $Name; keeping the first (system font takes precedence)."
                }
                continue
            }
            Copy-Item -LiteralPath $File.FullName -Destination $Target
            Write-Host "Selected: $Name"
        }
    }
    $Count = @(Get-ChildItem -LiteralPath $Stage -File).Count
    if ($Count -eq 0) { throw 'No eligible supplemental font files found.' }
    New-Item -ItemType Directory -Path (Split-Path -Parent $OutputPath) -Force | Out-Null
    Compress-Archive -Path (Join-Path $Stage '*') -DestinationPath $OutputPath -Force
    Write-Host "Exported $Count font files to $OutputPath"
} finally {
    if (Test-Path -LiteralPath $Stage) { Remove-Item -LiteralPath $Stage -Recurse -Force }
}
