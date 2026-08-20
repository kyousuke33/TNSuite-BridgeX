[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PortableZip,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$basePath = Join-Path $PSScriptRoot 'build-wix-installer.ps1'
$themePath = Join-Path $PSScriptRoot 'BridgeX.Hotfix21.Theme.xml'
$localizationPath = Join-Path $PSScriptRoot 'BridgeX.Hotfix21.Theme.wxl'
foreach ($required in @($basePath, $themePath, $localizationPath)) {
    if (-not (Test-Path -LiteralPath $required)) { throw "HOTFIX21_REQUIRED_FILE_MISSING=$required" }
}

$themeXmlLiteral = [System.Security.SecurityElement]::Escape((Resolve-Path -LiteralPath $themePath).Path)
$localizationXmlLiteral = [System.Security.SecurityElement]::Escape((Resolve-Path -LiteralPath $localizationPath).Path)

$text = Get-Content -LiteralPath $basePath -Raw -Encoding UTF8
$text = $text.Replace("TNSuiteBridgeX_260820_v0.5-Build12-Hotfix18-WiX", "TNSuiteBridgeX_260820_v0.5-Build12-Hotfix21-WiX")
$text = $text.Replace("`$MsiVersion = '0.5.1218'", "`$MsiVersion = '0.5.1221'")
$text = $text.Replace("`$BundleVersion = '0.5.12.18'", "`$BundleVersion = '0.5.12.21'")

$filesNeedle = @'
$files = @(Get-ChildItem -LiteralPath $PayloadRoot -File -Recurse | Sort-Object FullName)
'@
$brandingBlock = @'
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
$ThemeXml = '__HOTFIX21_THEME_XML__'
$LocalizationXml = '__HOTFIX21_LOCALIZATION_XML__'
Write-Host 'INSTALLER_ICON_SOURCE=BRIDGEX_EXE'
Write-Host 'INSTALLER_LOGO_SOURCE=BRIDGEX_EXE'
Write-Host 'INSTALLER_THEME=HOTFIX21_LOCATION_AND_FINISH_OPTIONS'

$files = @(Get-ChildItem -LiteralPath $PayloadRoot -File -Recurse | Sort-Object FullName)
'@
$brandingBlock = $brandingBlock.Replace('__HOTFIX21_THEME_XML__', $themeXmlLiteral)
$brandingBlock = $brandingBlock.Replace('__HOTFIX21_LOCALIZATION_XML__', $localizationXmlLiteral)
if (-not $text.Contains($filesNeedle.TrimStart("`r","`n"))) { throw 'PATCH_POINT_FILES_NOT_FOUND' }
$text = $text.Replace($filesNeedle.TrimStart("`r","`n"), $brandingBlock.TrimStart("`r","`n"))

$mediaNeedle = @'
[void]$product.AppendLine('    <MediaTemplate EmbedCab="yes" CompressionLevel="high" />')
'@
$mediaReplacement = @'
[void]$product.AppendLine('    <MediaTemplate EmbedCab="yes" CompressionLevel="high" />')
[void]$product.AppendLine('    <Icon Id="BridgeXIcon" SourceFile="' + $IconXml + '" />')
[void]$product.AppendLine('    <Property Id="ARPPRODUCTICON" Value="BridgeXIcon" />')
[void]$product.AppendLine('    <Property Id="CREATE_DESKTOP_SHORTCUT" Value="1" Secure="yes" />')
'@
if (-not $text.Contains($mediaNeedle.Trim())) { throw 'PATCH_POINT_MSI_PROPERTIES_NOT_FOUND' }
$text = $text.Replace($mediaNeedle.Trim(), $mediaReplacement.Trim())

$featureNeedle = @'
[void]$product.AppendLine('      <ComponentRef Id="StartMenuShortcutComponent" />')
'@
$featureReplacement = @'
[void]$product.AppendLine('      <ComponentRef Id="StartMenuShortcutComponent" />')
[void]$product.AppendLine('      <ComponentRef Id="DesktopShortcutComponent" />')
'@
if (-not $text.Contains($featureNeedle.Trim())) { throw 'PATCH_POINT_FEATURE_SHORTCUTS_NOT_FOUND' }
$text = $text.Replace($featureNeedle.Trim(), $featureReplacement.Trim())

# INSTALLBASE is a public MSI directory property above the authored TNSuite\BridgeX
# children. The UI-facing Burn variable is intentionally named InstallFolder because
# WixStdBA/ThmUtil has first-class two-way handling for a control with that name.
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

$programMenuNeedle = @'
[void]$product.AppendLine('    <StandardDirectory Id="ProgramMenuFolder">')
[void]$product.AppendLine('      <Directory Id="ApplicationProgramsFolder" Name="TNSuite BridgeX" />')
[void]$product.AppendLine('    </StandardDirectory>')
'@
$programMenuReplacement = @'
[void]$product.AppendLine('    <StandardDirectory Id="ProgramMenuFolder">')
[void]$product.AppendLine('      <Directory Id="ApplicationProgramsFolder" Name="TNSuite BridgeX" />')
[void]$product.AppendLine('    </StandardDirectory>')
[void]$product.AppendLine('    <StandardDirectory Id="DesktopFolder" />')
'@
if (-not $text.Contains($programMenuNeedle.Trim())) { throw 'PATCH_POINT_DESKTOP_STANDARD_DIRECTORY_NOT_FOUND' }
$text = $text.Replace($programMenuNeedle.Trim(), $programMenuReplacement.Trim())

$startMenuNeedle = @'
[void]$product.AppendLine('    <Component Id="StartMenuShortcutComponent" Directory="ApplicationProgramsFolder" Guid="{33CC5719-43A4-4D98-B676-8A7358E79F73}">')
[void]$product.AppendLine('      <Shortcut Id="StartMenuShortcut" Name="TNSuite BridgeX" Description="TNSuite BridgeX" Target="[INSTALLFOLDER]bin\BridgeX.exe" WorkingDirectory="' + (StableId 'DIR' 'bin') + '" />')
[void]$product.AppendLine('      <RemoveFolder Id="ApplicationProgramsFolderCleanup" On="uninstall" />')
[void]$product.AppendLine('      <RegistryValue Root="HKLM" Key="Software\TNSuite\BridgeX" Name="InstallerGeneration" Type="string" Value="WiX-' + $BundleVersion + '" KeyPath="yes" />')
[void]$product.AppendLine('    </Component>')
'@
$startMenuReplacement = @'
[void]$product.AppendLine('    <Component Id="StartMenuShortcutComponent" Directory="ApplicationProgramsFolder" Guid="{33CC5719-43A4-4D98-B676-8A7358E79F73}">')
[void]$product.AppendLine('      <Shortcut Id="StartMenuShortcut" Name="TNSuite BridgeX" Description="TNSuite BridgeX" Target="[INSTALLFOLDER]bin\BridgeX.exe" WorkingDirectory="' + (StableId 'DIR' 'bin') + '" />')
[void]$product.AppendLine('      <RemoveFolder Id="ApplicationProgramsFolderCleanup" On="uninstall" />')
[void]$product.AppendLine('      <RegistryValue Root="HKLM" Key="Software\TNSuite\BridgeX" Name="InstallerGeneration" Type="string" Value="WiX-' + $BundleVersion + '" KeyPath="yes" />')
[void]$product.AppendLine('    </Component>')
[void]$product.AppendLine('    <Component Id="DesktopShortcutComponent" Directory="DesktopFolder" Guid="{B6C3C6A0-AD31-4BF7-B30F-5BE94E5467B4}" Condition="CREATE_DESKTOP_SHORTCUT = 1" Transitive="yes">')
[void]$product.AppendLine('      <Shortcut Id="DesktopShortcut" Name="TNSuite BridgeX" Description="TNSuite BridgeX" Target="[INSTALLFOLDER]bin\BridgeX.exe" WorkingDirectory="' + (StableId 'DIR' 'bin') + '" />')
[void]$product.AppendLine('      <RegistryValue Root="HKLM" Key="Software\TNSuite\BridgeX" Name="DesktopShortcut" Type="integer" Value="1" KeyPath="yes" />')
[void]$product.AppendLine('    </Component>')
'@
if (-not $text.Contains($startMenuNeedle.Trim())) { throw 'PATCH_POINT_DESKTOP_SHORTCUT_COMPONENT_NOT_FOUND' }
$text = $text.Replace($startMenuNeedle.Trim(), $startMenuReplacement.Trim())

$bundleOpenNeedle = @'
  <Bundle Name="TNSuite BridgeX" Manufacturer="TNSuite" Version="$BundleVersion" UpgradeCode="$BundleUpgradeCode">
'@
$bundleOpenReplacement = @'
  <Bundle Name="TNSuite BridgeX" Manufacturer="TNSuite" Version="$BundleVersion" UpgradeCode="$BundleUpgradeCode" IconSourceFile="$IconXml">
    <Variable Name="InstallFolder" Type="formatted" Value="[ProgramFiles64Folder]" Persisted="yes" bal:Overridable="yes" />
    <Variable Name="CreateDesktopShortcut" Type="numeric" Value="1" Persisted="yes" bal:Overridable="yes" />
    <Variable Name="LaunchAfterInstall" Type="numeric" Value="1" Persisted="no" bal:Overridable="yes" />
'@
if (-not $text.Contains($bundleOpenNeedle.Trim())) { throw 'PATCH_POINT_BUNDLE_VARIABLES_NOT_FOUND' }
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
          SuppressOptionsUI="no"
          LaunchTarget="[InstallFolder]TNSuite\BridgeX\bin\BridgeX.exe"
          LaunchWorkingFolder="[InstallFolder]TNSuite\BridgeX\bin" />
'@
if (-not $text.Contains($baNeedle.Trim())) { throw 'PATCH_POINT_BA_NOT_FOUND' }
$text = $text.Replace($baNeedle.Trim(), $baReplacement.Trim())

$msiNeedle = @'
      <MsiPackage SourceFile="$([System.Security.SecurityElement]::Escape($MsiPath))" Compressed="yes" />
'@
$msiReplacement = @'
      <MsiPackage SourceFile="$([System.Security.SecurityElement]::Escape($MsiPath))" Compressed="yes">
        <MsiProperty Name="INSTALLBASE" Value="[InstallFolder]" />
        <MsiProperty Name="CREATE_DESKTOP_SHORTCUT" Value="[CreateDesktopShortcut]" />
      </MsiPackage>
'@
if (-not $text.Contains($msiNeedle.Trim())) { throw 'PATCH_POINT_MSI_PROPERTY_NOT_FOUND' }
$text = $text.Replace($msiNeedle.Trim(), $msiReplacement.Trim())

$finalNeedle = "Write-Host 'WIX_INSTALLER_BUILD=PASS'"
$finalReplacement = @"
Write-Host 'INSTALL_LOCATION_UI=ENABLED'
Write-Host 'INSTALL_LOCATION_UI_MODE=BASE_FOLDER'
Write-Host 'INSTALL_LOCATION_BURN_VARIABLE=InstallFolder'
Write-Host 'INSTALL_LOCATION_MSI_PROPERTY=INSTALLBASE'
Write-Host 'INSTALL_LOCATION_AUTO_SUBFOLDER=TNSuite\BridgeX'
Write-Host 'DESKTOP_SHORTCUT_OPTION=ENABLED'
Write-Host 'DESKTOP_SHORTCUT_DEFAULT=1'
Write-Host 'LAUNCH_AFTER_INSTALL_OPTION=ENABLED'
Write-Host 'LAUNCH_AFTER_INSTALL_DEFAULT=1'
Write-Host 'INSTALLER_ICON=BRIDGEX'
Write-Host 'INSTALLER_LOGO=BRIDGEX'
Write-Host 'WIX_INSTALLER_BUILD=PASS'
"@
$text = $text.Replace($finalNeedle, $finalReplacement.Trim())

$tempBuilder = Join-Path $env:RUNNER_TEMP "BridgeX-Hotfix21-WiX-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.ps1"
[System.IO.File]::WriteAllText($tempBuilder, $text, [System.Text.UTF8Encoding]::new($false))

& pwsh.exe -NoLogo -NoProfile -File $tempBuilder -PortableZip $PortableZip -OutputDirectory $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw "HOTFIX21_WIX_BUILD_FAILED=$LASTEXITCODE" }
