[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PortableZip,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$basePath = Join-Path $PSScriptRoot 'build-wix-installer.ps1'
$themePath = Join-Path $PSScriptRoot 'BridgeX.Hotfix20.Theme.xml'
$localizationPath = Join-Path $PSScriptRoot 'BridgeX.Hotfix20.Theme.wxl'
foreach ($required in @($basePath, $themePath, $localizationPath)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "HOTFIX20_REQUIRED_FILE_MISSING=$required" }
}

$text = Get-Content -LiteralPath $basePath -Raw -Encoding UTF8
$text = $text.Replace("TNSuiteBridgeX_260820_v0.5-Build12-Hotfix18-WiX", "TNSuiteBridgeX_260820_v0.5-Build12-Hotfix20-WiX")
$text = $text.Replace("`$MsiVersion = '0.5.1218'", "`$MsiVersion = '0.5.1220'")
$text = $text.Replace("`$BundleVersion = '0.5.12.18'", "`$BundleVersion = '0.5.12.20'")

$filesNeedle = @'
$files = @(Get-ChildItem -LiteralPath $PayloadRoot -File -Recurse | Sort-Object FullName)
'@
$brandingBlock = @'
# Derive installer branding from the canonical BridgeX executable so the setup,
# Add/Remove Programs and application all use the same product identity.
try {
    Add-Type -AssemblyName System.Drawing.Common -ErrorAction Stop
}
catch {
    Add-Type -AssemblyName System.Drawing -ErrorAction Stop
}
$BridgeXIcon = [System.Drawing.Icon]::ExtractAssociatedIcon($BridgeXExe)
if ($null -eq $BridgeXIcon) { throw 'BRIDGEX_ICON_EXTRACTION_FAILED' }
$IconPath = Join-Path $WixRoot 'BridgeX.ico'
$iconStream = [System.IO.File]::Create($IconPath)
try { $BridgeXIcon.Save($iconStream) } finally { $iconStream.Dispose() }

$LogoPath = Join-Path $WixRoot 'BridgeXLogo.png'
$logoBitmap = New-Object System.Drawing.Bitmap 64,64
$graphics = [System.Drawing.Graphics]::FromImage($logoBitmap)
try {
    $graphics.Clear([System.Drawing.Color]::Transparent)
    $iconRect = New-Object System.Drawing.Rectangle 0,0,64,64
    $graphics.DrawIcon($BridgeXIcon, $iconRect)
    $logoBitmap.Save($LogoPath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
    $graphics.Dispose()
    $logoBitmap.Dispose()
    $BridgeXIcon.Dispose()
}
if (-not (Test-Path -LiteralPath $IconPath) -or -not (Test-Path -LiteralPath $LogoPath)) {
    throw 'INSTALLER_BRANDING_ASSET_BUILD_FAILED'
}
$IconXml = XmlEscape $IconPath
$LogoXml = XmlEscape $LogoPath
$ThemeXml = XmlEscape $themePath
$LocalizationXml = XmlEscape $localizationPath
Write-Host 'INSTALLER_ICON_SOURCE=BRIDGEX_EXE'
Write-Host 'INSTALLER_LOGO_SOURCE=BRIDGEX_EXE'
Write-Host 'INSTALLER_THEME=HOTFIX20_BASE_FOLDER_SELECTION'

$files = @(Get-ChildItem -LiteralPath $PayloadRoot -File -Recurse | Sort-Object FullName)
'@
if (-not $text.Contains($filesNeedle.TrimStart("`r","`n"))) { throw 'PATCH_POINT_FILES_NOT_FOUND' }
$text = $text.Replace($filesNeedle.TrimStart("`r","`n"), $brandingBlock.TrimStart("`r","`n"))

$mediaNeedle = @'
[void]$product.AppendLine('    <MediaTemplate EmbedCab="yes" CompressionLevel="high" />')
'@
$mediaReplacement = @'
[void]$product.AppendLine('    <MediaTemplate EmbedCab="yes" CompressionLevel="high" />')
[void]$product.AppendLine('    <Icon Id="BridgeXIcon" SourceFile="' + $IconXml + '" />')
[void]$product.AppendLine('    <Property Id="ARPPRODUCTICON" Value="BridgeXIcon" />')
'@
if (-not $text.Contains($mediaNeedle.Trim())) { throw 'PATCH_POINT_MSI_ICON_NOT_FOUND' }
$text = $text.Replace($mediaNeedle.Trim(), $mediaReplacement.Trim())

# Introduce a public MSI directory property that represents only the selected base
# location. TNSuite\BridgeX stays as authored child directories, so selecting D:\
# resolves to D:\TNSuite\BridgeX and selecting D:\Apps resolves to
# D:\Apps\TNSuite\BridgeX without asking the user to type the product subfolder.
$directoryNeedle = @'
[void]$product.AppendLine('    <StandardDirectory Id="ProgramFiles64Folder">')
[void]$product.AppendLine('      <Directory Id="TNSuiteFolder" Name="TNSuite">')
[void]$product.AppendLine('        <Directory Id="INSTALLFOLDER" Name="BridgeX">')
EmitDirectoryTree $product '' 10
[void]$product.AppendLine('        </Directory>')
[void]$product.AppendLine('      </Directory>')
[void]$product.AppendLine('    </StandardDirectory>')
'@
$directoryReplacement = @'
[void]$product.AppendLine('    <StandardDirectory Id="ProgramFiles64Folder">')
[void]$product.AppendLine('      <Directory Id="INSTALLBASE" Name=".">')
[void]$product.AppendLine('        <Directory Id="TNSuiteFolder" Name="TNSuite">')
[void]$product.AppendLine('          <Directory Id="INSTALLFOLDER" Name="BridgeX">')
EmitDirectoryTree $product '' 12
[void]$product.AppendLine('          </Directory>')
[void]$product.AppendLine('        </Directory>')
[void]$product.AppendLine('      </Directory>')
[void]$product.AppendLine('    </StandardDirectory>')
'@
if (-not $text.Contains($directoryNeedle.Trim())) { throw 'PATCH_POINT_INSTALL_DIRECTORY_TREE_NOT_FOUND' }
$text = $text.Replace($directoryNeedle.Trim(), $directoryReplacement.Trim())

$bundleOpenNeedle = @'
  <Bundle Name="TNSuite BridgeX" Manufacturer="TNSuite" Version="$BundleVersion" UpgradeCode="$BundleUpgradeCode">
'@
$bundleOpenReplacement = @'
  <Bundle Name="TNSuite BridgeX" Manufacturer="TNSuite" Version="$BundleVersion" UpgradeCode="$BundleUpgradeCode" IconSourceFile="$IconXml">
    <Variable Name="InstallBaseFolder" Type="formatted" Value="[ProgramFiles64Folder]" Persisted="yes" bal:Overridable="yes" />
'@
if (-not $text.Contains($bundleOpenNeedle.Trim())) { throw 'PATCH_POINT_BUNDLE_OPEN_NOT_FOUND' }
$text = $text.Replace($bundleOpenNeedle.Trim(), $bundleOpenReplacement.Trim())

$baNeedle = @'
      <bal:WixStandardBootstrapperApplication Theme="hyperlinkLicense" LicenseUrl="" SuppressOptionsUI="yes" />
'@
$baReplacement = @'
      <bal:WixStandardBootstrapperApplication
          Theme="hyperlinkLargeLicense"
          ThemeFile="$ThemeXml"
          LocalizationFile="$LocalizationXml"
          LicenseUrl=""
          LogoFile="$LogoXml"
          ShowVersion="yes"
          SuppressOptionsUI="no" />
'@
if (-not $text.Contains($baNeedle.Trim())) { throw 'PATCH_POINT_BA_NOT_FOUND' }
$text = $text.Replace($baNeedle.Trim(), $baReplacement.Trim())

$msiNeedle = @'
      <MsiPackage SourceFile="$([System.Security.SecurityElement]::Escape($MsiPath))" Compressed="yes" />
'@
$msiReplacement = @'
      <MsiPackage SourceFile="$([System.Security.SecurityElement]::Escape($MsiPath))" Compressed="yes">
        <MsiProperty Name="INSTALLBASE" Value="[InstallBaseFolder]" />
      </MsiPackage>
'@
if (-not $text.Contains($msiNeedle.Trim())) { throw 'PATCH_POINT_MSI_PROPERTY_NOT_FOUND' }
$text = $text.Replace($msiNeedle.Trim(), $msiReplacement.Trim())

$finalNeedle = "Write-Host 'WIX_INSTALLER_BUILD=PASS'"
$finalReplacement = @"
Write-Host 'INSTALL_LOCATION_UI=ENABLED'
Write-Host 'INSTALL_LOCATION_UI_MODE=BASE_FOLDER'
Write-Host 'INSTALL_LOCATION_BURN_VARIABLE=InstallBaseFolder'
Write-Host 'INSTALL_LOCATION_MSI_PROPERTY=INSTALLBASE'
Write-Host 'INSTALL_LOCATION_AUTO_SUBFOLDER=TNSuite\BridgeX'
Write-Host 'INSTALLER_ICON=BRIDGEX'
Write-Host 'INSTALLER_LOGO=BRIDGEX'
Write-Host 'WIX_INSTALLER_BUILD=PASS'
"@
$text = $text.Replace($finalNeedle, $finalReplacement.Trim())

$tempBuilder = Join-Path $env:RUNNER_TEMP "BridgeX-Hotfix20-WiX-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.ps1"
[System.IO.File]::WriteAllText($tempBuilder, $text, [System.Text.UTF8Encoding]::new($false))

& pwsh.exe -NoLogo -NoProfile -File $tempBuilder -PortableZip $PortableZip -OutputDirectory $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw "HOTFIX20_WIX_BUILD_FAILED=$LASTEXITCODE" }
