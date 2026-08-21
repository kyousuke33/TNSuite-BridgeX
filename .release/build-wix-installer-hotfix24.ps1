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
$repoRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($repoRoot) -or -not (Test-Path -LiteralPath $repoRoot -PathType Container)) { throw "HOTFIX24_REPO_ROOT_RESOLUTION_FAILED=$repoRoot" }
$canonicalIcon = Join-Path $repoRoot 'assets\branding\BridgeX-AppIcon.ico'
$classicSidebar = Join-Path $repoRoot 'installer\BridgeX-Setup-Sidebar.bmp'
$expectedIconSha256 = '06266307acb6a92aca9742dac59dd053029075256a30eec50a37a71e08296328'
if (-not (Test-Path -LiteralPath $canonicalIcon)) { throw "HOTFIX24_CANONICAL_ICON_MISSING=$canonicalIcon" }
if (-not (Test-Path -LiteralPath $classicSidebar)) { throw "HOTFIX24_CLASSIC_SIDEBAR_MISSING=$classicSidebar" }
$actualIconSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $canonicalIcon).Hash.ToLowerInvariant()
if ($actualIconSha256 -ne $expectedIconSha256) { throw "HOTFIX24_CANONICAL_ICON_HASH_FAIL=$actualIconSha256" }

# Hotfix24 intentionally changes BridgeX.exe by applying the real HWND icon
# patch. Keep the base WiX integrity gate fail-closed, but pin it to the exact
# Hotfix24 runtime hash proven by the full-source build instead of Hotfix16's
# pre-patch executable hash. Do not weaken or remove the payload hash check.
$baseLoadNeedle = '$text = Get-Content -LiteralPath $basePath -Raw -Encoding UTF8'
$runtimeHashOverride = '$text = $text.Replace(''9d528d211950f3df0609c05a8c1e01725927ae76b70bed2ad0fe9b97c53504d6'', ''3fb8b43400050c435500e3122167f85ec25bef0f30602321aca81f073ab360b6'')'
if (-not $source.Contains($baseLoadNeedle)) { throw 'HOTFIX24_RUNTIME_HASH_OVERRIDE_ANCHOR_MISSING' }
$source = $source.Replace($baseLoadNeedle, $baseLoadNeedle + "`r`n" + $runtimeHashOverride)

# Emit valid PowerShell single-quoted path literals into the nested Hotfix21
# builder. PowerShell does not use backslash to escape quotes; the previous
# \"...\" authoring caused the generated builder to fail before WiX ran.
$iconLiteral = "'" + $canonicalIcon.Replace("'", "''") + "'"
$iconXmlNeedle = '$IconXml = XmlEscape $IconPath'
$iconXmlReplacement = '$IconPath = ' + $iconLiteral + "`r`n" + '$IconXml = XmlEscape $IconPath'
if (-not $source.Contains($iconXmlNeedle)) { throw 'HOTFIX24_ICON_OVERRIDE_ANCHOR_MISSING' }
$source = $source.Replace($iconXmlNeedle, $iconXmlReplacement)

$sidebarLiteral = "'" + $classicSidebar.Replace("'", "''") + "'"
$logoXmlNeedle = '$LogoXml = XmlEscape $LogoPath'
$logoXmlReplacement = '$LogoPath = ' + $sidebarLiteral + "`r`n" + '$LogoXml = XmlEscape $LogoPath'
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
