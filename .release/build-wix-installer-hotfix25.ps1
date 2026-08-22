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
$repoRoot = Split-Path -Parent $PSScriptRoot
$classicSidebar = Join-Path $repoRoot 'installer\BridgeX-Setup-Sidebar.bmp'
if (-not (Test-Path -LiteralPath $classicSidebar -PathType Leaf)) { throw "HOTFIX25_BASE_SIDEBAR_MISSING=$classicSidebar" }

# Build a Hotfix25-only full-height sidebar in the isolated runner temp directory.
# Preserve the original artwork, remove the 6 px cyan edge stripe, and extend the
# bottom background to 390 px. The governed Hotfix16/Hotfix24 asset stays untouched.
$generatedSidebar = Join-Path $env:RUNNER_TEMP "BridgeX-Setup-Sidebar-Hotfix25-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.bmp"
Add-Type -AssemblyName System.Drawing
$sourceBitmap = [System.Drawing.Bitmap]::new($classicSidebar)
try {
    if ($sourceBitmap.Width -ne 164 -or $sourceBitmap.Height -ne 314) {
        throw "HOTFIX25_BASE_SIDEBAR_DIMENSIONS_FAIL=$($sourceBitmap.Width)x$($sourceBitmap.Height)"
    }
    $targetBitmap = [System.Drawing.Bitmap]::new(164, 390, [System.Drawing.Imaging.PixelFormat]::Format24bppRgb)
    try {
        for ($y = 0; $y -lt 314; $y++) {
            for ($x = 6; $x -lt 164; $x++) {
                $targetBitmap.SetPixel($x, $y, $sourceBitmap.GetPixel($x, $y))
            }
            $edge = $sourceBitmap.GetPixel(6, $y)
            for ($x = 0; $x -lt 6; $x++) { $targetBitmap.SetPixel($x, $y, $edge) }
        }
        for ($y = 314; $y -lt 390; $y++) {
            for ($x = 0; $x -lt 164; $x++) {
                $targetBitmap.SetPixel($x, $y, $targetBitmap.GetPixel($x, 313))
            }
        }
        $targetBitmap.Save($generatedSidebar, [System.Drawing.Imaging.ImageFormat]::Bmp)
    }
    finally {
        $targetBitmap.Dispose()
    }
}
finally {
    $sourceBitmap.Dispose()
}
if (-not (Test-Path -LiteralPath $generatedSidebar -PathType Leaf)) { throw "HOTFIX25_GENERATED_SIDEBAR_MISSING=$generatedSidebar" }
$generatedSidebarSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $generatedSidebar).Hash.ToLowerInvariant()
Write-Host "HOTFIX25_SIDEBAR_SHA256=$generatedSidebarSha256"
Write-Host 'HOTFIX25_SIDEBAR_ACCENT_STRIP=NONE'
Write-Host 'HOTFIX25_SIDEBAR_DIMENSIONS=164x390'

# Preserve the proven Hotfix24 WiX maintenance implementation while giving
# Hotfix25 its own dark installer theme. Product detection, location recovery,
# Repair/Uninstall, process close and Restart Manager behavior remain unchanged.
$driver = Get-Content -LiteralPath $hotfix24 -Raw -Encoding UTF8
$driver = $driver.Replace('Hotfix24', 'Hotfix25')
$driver = $driver.Replace('HOTFIX24', 'HOTFIX25')
$driver = $driver.Replace('0.5.1224', '0.5.1225')
$driver = $driver.Replace('0.5.12.24', '0.5.12.25')
$driver = $driver.Replace('260821', '260822')
$sidebarLiteral = "'" + $generatedSidebar.Replace("'", "''") + "'"
$sidebarNeedle = "`$classicSidebar = Join-Path `$repoRoot 'installer\BridgeX-Setup-Sidebar.bmp'"
$sidebarReplacement = '$classicSidebar = ' + $sidebarLiteral
if (-not $driver.Contains($sidebarNeedle)) { throw 'HOTFIX25_SIDEBAR_OVERRIDE_ANCHOR_MISSING' }
$driver = $driver.Replace($sidebarNeedle, $sidebarReplacement)
$driver = $driver.Replace('INSTALLER_LOGO_SOURCE=HOTFIX16_CLASSIC_SIDEBAR', 'INSTALLER_LOGO_SOURCE=HOTFIX25_DARK_FULL_HEIGHT_SIDEBAR')
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
    Remove-Item -LiteralPath $generatedSidebar -Force -ErrorAction SilentlyContinue
}
