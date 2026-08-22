[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PortableZip,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [Parameter(Mandatory = $true)][ValidatePattern('^[0-9A-Fa-f]{64}$')][string]$ExpectedBridgeXSha256
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$hotfix24 = Join-Path $PSScriptRoot 'build-wix-installer-hotfix24.ps1'
if (-not (Test-Path -LiteralPath $hotfix24)) { throw "HOTFIX25_BASE_BUILDER_MISSING=$hotfix24" }
foreach ($asset in @('BridgeX.Hotfix25.Theme.xml','BridgeX.Hotfix25.Theme.wxl')) {
    $path = Join-Path $PSScriptRoot $asset
    if (-not (Test-Path -LiteralPath $path)) { throw "HOTFIX25_THEME_ASSET_MISSING=$path" }
}

# Preserve the proven Hotfix24 WiX maintenance implementation while giving
# Hotfix25 its own dark installer theme. Product detection, location recovery,
# Repair/Uninstall, process close and Restart Manager behavior remain unchanged.
$driver = Get-Content -LiteralPath $hotfix24 -Raw -Encoding UTF8
$driver = $driver.Replace('Hotfix24', 'Hotfix25')
$driver = $driver.Replace('HOTFIX24', 'HOTFIX25')
$driver = $driver.Replace('0.5.1224', '0.5.1225')
$driver = $driver.Replace('0.5.12.24', '0.5.12.25')
$driver = $driver.Replace('260821', '260822')
$driver = $driver.Replace(
    'INSTALLER_THEME=HOTFIX25_CLASSIC_BRANDING_STATE_AWARE_MAINTENANCE',
    'INSTALLER_THEME=HOTFIX25_DARK_CLASSIC_FULL_HEIGHT_STATE_AWARE_MAINTENANCE'
)

$temp = Join-Path $PSScriptRoot ".BridgeX-Hotfix25-Adapter-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.ps1"
try {
    [IO.File]::WriteAllText($temp, $driver, [Text.UTF8Encoding]::new($false))
    & pwsh.exe -NoLogo -NoProfile -File $temp `
        -PortableZip $PortableZip `
        -OutputDirectory $OutputDirectory `
        -ExpectedBridgeXSha256 $ExpectedBridgeXSha256
    if ($LASTEXITCODE -ne 0) { throw "HOTFIX25_WIX_BUILD_FAILED=$LASTEXITCODE" }
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
