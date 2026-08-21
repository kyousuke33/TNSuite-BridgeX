[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PortableZip,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$hotfix23 = Join-Path $PSScriptRoot 'build-wix-installer-hotfix23.ps1'
foreach ($required in @(
    $hotfix23,
    (Join-Path $PSScriptRoot 'BridgeX.Hotfix24.Theme.xml'),
    (Join-Path $PSScriptRoot 'BridgeX.Hotfix24.Theme.wxl'),
    (Join-Path (Split-Path -Parent $PSScriptRoot) 'assets\branding\BridgeX-AppIcon.ico'),
    (Join-Path (Split-Path -Parent $PSScriptRoot) 'installer\BridgeX-Setup-Sidebar.bmp')
)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "HOTFIX24_REQUIRED_FILE_MISSING=$required" }
}

# Reuse the green Hotfix23 maintenance implementation, changing only identity,
# theme/localization and branding-source selection. This keeps the proven
# Update/Repair/Uninstall/path-preservation behavior intact.
$script = Get-Content -LiteralPath $hotfix23 -Raw -Encoding UTF8
$script = $script.Replace('Hotfix23', 'Hotfix24')
$script = $script.Replace('HOTFIX23', 'HOTFIX24')
$script = $script.Replace('0.5.1223', '0.5.1224')
$script = $script.Replace('0.5.12.23', '0.5.12.24')
$script = $script.Replace('TNSuiteBridgeX_260820_v0.5-Build12-Hotfix24-WiX', 'TNSuiteBridgeX_260821_v0.5-Build12-Hotfix24-WiX')
$script = $script.Replace('INSTALLER_THEME=HOTFIX24_STATE_AWARE_MAINTENANCE', 'INSTALLER_THEME=HOTFIX24_CLASSIC_BRANDING_STATE_AWARE_MAINTENANCE')

# Hotfix21 historically regenerated an ICO via ExtractAssociatedIcon, which
# collapses the original multi-resolution icon to a single representation on
# many Windows builds. Override the generated builder after the legacy helper
# code runs so WiX consumes the exact canonical ICO and the original sidebar BMP.
$loadNeedle = '$source = Get-Content -LiteralPath $hotfix21 -Raw -Encoding UTF8'
if (-not $script.Contains($loadNeedle)) { throw 'HOTFIX24_SOURCE_LOAD_ANCHOR_MISSING' }
$override = @'
$canonicalIcon = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'assets\branding\BridgeX-AppIcon.ico'
$classicSidebar = Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'installer\BridgeX-Setup-Sidebar.bmp'
$expectedIconSha256 = '06266307acb6a92aca9742dac59dd053029075256a30eec50a37a71e08296328'
if (-not (Test-Path -LiteralPath $canonicalIcon)) { throw "HOTFIX24_CANONICAL_ICON_MISSING=$canonicalIcon" }
if (-not (Test-Path -LiteralPath $classicSidebar)) { throw "HOTFIX24_CLASSIC_SIDEBAR_MISSING=$classicSidebar" }
$actualIconSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $canonicalIcon).Hash.ToLowerInvariant()
if ($actualIconSha256 -ne $expectedIconSha256) { throw "HOTFIX24_CANONICAL_ICON_HASH_FAIL=$actualIconSha256" }

$iconXmlNeedle = '$IconXml = XmlEscape $IconPath'
$iconXmlReplacement = '$IconPath = "__HF24_ICON__"' + "`r`n" + '$IconXml = XmlEscape $IconPath'
$iconXmlReplacement = $iconXmlReplacement.Replace('__HF24_ICON__', $canonicalIcon.Replace("'", "''"))
if (-not $source.Contains($iconXmlNeedle)) { throw 'HOTFIX24_ICON_OVERRIDE_ANCHOR_MISSING' }
$source = $source.Replace($iconXmlNeedle, $iconXmlReplacement)

$logoXmlNeedle = '$LogoXml = XmlEscape $LogoPath'
$logoXmlReplacement = '$LogoPath = "__HF24_SIDEBAR__"' + "`r`n" + '$LogoXml = XmlEscape $LogoPath'
$logoXmlReplacement = $logoXmlReplacement.Replace('__HF24_SIDEBAR__', $classicSidebar.Replace("'", "''"))
if (-not $source.Contains($logoXmlNeedle)) { throw 'HOTFIX24_LOGO_OVERRIDE_ANCHOR_MISSING' }
$source = $source.Replace($logoXmlNeedle, $logoXmlReplacement)

$source = $source.Replace("Write-Host 'INSTALLER_ICON_SOURCE=BRIDGEX_EXE'", "Write-Host 'INSTALLER_ICON_SOURCE=CANONICAL_MULTIRES_ICO'")
$source = $source.Replace("Write-Host 'INSTALLER_LOGO_SOURCE=BRIDGEX_EXE'", "Write-Host 'INSTALLER_LOGO_SOURCE=HOTFIX16_CLASSIC_SIDEBAR'")
'@
$script = $script.Replace($loadNeedle, $loadNeedle + "`r`n" + $override)

$temp = Join-Path $PSScriptRoot ".BridgeX-Hotfix24-Driver-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.ps1"
try {
    [System.IO.File]::WriteAllText($temp, $script, [System.Text.UTF8Encoding]::new($false))
    & pwsh.exe -NoLogo -NoProfile -File $temp -PortableZip $PortableZip -OutputDirectory $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw "HOTFIX24_WIX_BUILD_FAILED=$LASTEXITCODE" }
}
finally {
    Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
