[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PortableZip,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$hotfix21 = Join-Path $PSScriptRoot 'build-wix-installer-hotfix21.ps1'
if (-not (Test-Path -LiteralPath $hotfix21)) { throw "HOTFIX23_BASE_MISSING=$hotfix21" }
foreach ($asset in @('BridgeX.Hotfix23.Theme.xml','BridgeX.Hotfix23.Theme.wxl')) {
    $path = Join-Path $PSScriptRoot $asset
    if (-not (Test-Path -LiteralPath $path)) { throw "HOTFIX23_ASSET_MISSING=$path" }
}

# Start from the accepted Hotfix21 location/shortcut/finish UX, then add:
# - state-aware product detection for Install vs Update;
# - exact installed-folder recovery from Windows Installer component registration;
# - standard same-version WixStdBA Modify page (Repair/Uninstall);
# - force-close of BridgeX-owned processes before InstallValidate;
# - Restart Manager suppression so normal BridgeX locks do not trigger Files In Use/reboot UX.
$source = Get-Content -LiteralPath $hotfix21 -Raw -Encoding UTF8
$source = $source.Replace('TNSuiteBridgeX_260820_v0.5-Build12-Hotfix21-WiX', 'TNSuiteBridgeX_260820_v0.5-Build12-Hotfix23-WiX')
$source = $source.Replace("0.5.1221", "0.5.1223")
$source = $source.Replace("0.5.12.21", "0.5.12.23")
$source = $source.Replace('BridgeX.Hotfix21.Theme.xml', 'BridgeX.Hotfix23.Theme.xml')
$source = $source.Replace('BridgeX.Hotfix21.Theme.wxl', 'BridgeX.Hotfix23.Theme.wxl')
$source = $source.Replace('HOTFIX21_WIX_BUILD_FAILED', 'HOTFIX23_WIX_BUILD_FAILED')
$source = $source.Replace('BridgeX-Hotfix21-WiX-', 'BridgeX-Hotfix23-WiX-')
$source = $source.Replace('INSTALLER_THEME=HOTFIX21_LOCATION_AND_FINISH_OPTIONS', 'INSTALLER_THEME=HOTFIX23_STATE_AWARE_MAINTENANCE')

$anchor = '$tempBuilder = Join-Path $env:RUNNER_TEMP "BridgeX-Hotfix23-WiX-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.ps1"'
if (-not $source.Contains($anchor)) { throw 'HOTFIX23_INJECTION_ANCHOR_MISSING' }

$injection = @'
# P0 maintenance behavior:
# 1) Disable Windows Installer Restart Manager for this MSI.
# 2) Before InstallValidate, force-close only the two BridgeX executable names.
#    WixQuietExec keeps the console hidden and uses Windows' own taskkill.exe;
#    no helper executable/script is shipped in the installer.
# 3) Recover the exact existing INSTALLFOLDER via the stable root-file component
#    registered by Hotfix18+ MSI generations, so Update/Repair never falls back to C:.

$wixRootNeedle = "[void]`$product.AppendLine('<Wix xmlns=`"http://wixtoolset.org/schemas/v4/wxs`">')"
$wixRootReplacement = "[void]`$product.AppendLine('<Wix xmlns=`"http://wixtoolset.org/schemas/v4/wxs`" xmlns:util=`"http://wixtoolset.org/schemas/v4/wxs/util`">')"
if (-not $text.Contains($wixRootNeedle)) { throw 'HOTFIX23_MSI_UTIL_NAMESPACE_PATCH_POINT_MISSING' }
$text = $text.Replace($wixRootNeedle, $wixRootReplacement)

$upgradeNeedle = "[void]`$product.AppendLine('    <MajorUpgrade DowngradeErrorMessage=`"A newer version of TNSuite BridgeX is already installed.`" />')"
$upgradeReplacement = $upgradeNeedle + "`r`n" +
    "[void]`$product.AppendLine('    <Property Id=`"MSIDISABLERMRESTART`" Value=`"1`" />')" + "`r`n" +
    "[void]`$product.AppendLine('    <Property Id=`"MSIRESTARTMANAGERCONTROL`" Value=`"Disable`" />')" + "`r`n" +
    "[void]`$product.AppendLine('    <SetProperty Id=`"WixQuietExecCmdLine`" Value=`"&amp;quot;[System64Folder]cmd.exe&amp;quot; /d /s /c &amp;quot;&amp;quot;[System64Folder]taskkill.exe&amp;quot; /F /T /IM BridgeX.exe &amp;gt;nul 2&amp;gt;&amp;amp;1 &amp;amp; &amp;quot;[System64Folder]taskkill.exe&amp;quot; /F /T /IM BridgeX-CLI.exe &amp;gt;nul 2&amp;gt;&amp;amp;1 &amp;amp; exit /b 0&amp;quot;`" Before=`"ForceCloseBridgeX`" Sequence=`"execute`" />')" + "`r`n" +
    "[void]`$product.AppendLine('    <CustomAction Id=`"ForceCloseBridgeX`" BinaryRef=`"Wix4UtilCA_X64`" DllEntry=`"WixQuietExec`" Execute=`"immediate`" Return=`"ignore`" />')" + "`r`n" +
    "[void]`$product.AppendLine('    <InstallExecuteSequence>')" + "`r`n" +
    "[void]`$product.AppendLine('      <Custom Action=`"ForceCloseBridgeX`" Before=`"InstallValidate`" Condition=`"Installed OR WIX_UPGRADE_DETECTED`" />')" + "`r`n" +
    "[void]`$product.AppendLine('    </InstallExecuteSequence>')"
if (-not $text.Contains($upgradeNeedle)) { throw 'HOTFIX23_PREVALIDATE_CLOSE_PATCH_POINT_MISSING' }
$text = $text.Replace($upgradeNeedle, $upgradeReplacement)

$msiBuildNeedle = '& wix build -arch x64 -o $MsiPath $ProductWxs'
$msiBuildReplacement = '& wix build -arch x64 -ext WixToolset.Util.wixext -o $MsiPath $ProductWxs'
if (-not $text.Contains($msiBuildNeedle)) { throw 'HOTFIX23_MSI_UTIL_BUILD_PATCH_POINT_MISSING' }
$text = $text.Replace($msiBuildNeedle, $msiBuildReplacement)

# Bundle detection uses supported Util bundle searches only. Do not place
# util:CloseApplication in Bundle: WiX 6 emits WIX1150 binder warnings for that
# authoring and it cannot be treated as a reliable pre-MSI close mechanism.
$bundleRootNeedle = '<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs" xmlns:bal="http://wixtoolset.org/schemas/v4/wxs/bal">'
$bundleRootReplacement = '<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs" xmlns:bal="http://wixtoolset.org/schemas/v4/wxs/bal" xmlns:util="http://wixtoolset.org/schemas/v4/wxs/util">'
if (-not $text.Contains($bundleRootNeedle)) { throw 'HOTFIX23_BUNDLE_UTIL_NAMESPACE_PATCH_POINT_MISSING' }
$text = $text.Replace($bundleRootNeedle, $bundleRootReplacement)

$launchVarNeedle = '    <Variable Name="LaunchAfterInstall" Type="numeric" Value="1" Persisted="no" bal:Overridable="yes" />'
$stateBlock = $launchVarNeedle + "`r`n" +
    '    <Variable Name="TargetBridgeXMsiVersion" Type="version" Value="0.5.1223" />' + "`r`n" +
    '    <Variable Name="BridgeXLaunchTarget" Type="formatted" Value="[InstallFolder]TNSuite\BridgeX\bin\BridgeX.exe" />' + "`r`n" +
    '    <Variable Name="BridgeXLaunchWorkingFolder" Type="formatted" Value="[InstallFolder]TNSuite\BridgeX\bin" />' + "`r`n" +
    '    <util:ProductSearch Id="DetectBridgeXProductVersion" UpgradeCode="{B8BF51DD-E1B4-4A6E-B543-1661EF5EA8EA}" Variable="DetectedBridgeXMsiVersion" Result="version" />' + "`r`n" +
    '    <util:ComponentSearch Id="DetectBridgeXExistingInstallFolder" Guid="{492A8EAC-6707-51E3-9723-967A6E4A94D9}" Variable="ExistingBridgeXInstallFolder" Result="directory" After="DetectBridgeXProductVersion" Condition="DetectedBridgeXMsiVersion &gt; v0.0.0.0" />' + "`r`n" +
    '    <SetVariable Id="ResolveBridgeXLaunchTarget" Variable="BridgeXLaunchTarget" Value="[ExistingBridgeXInstallFolder]bin\BridgeX.exe" Type="formatted" After="DetectBridgeXExistingInstallFolder" Condition="ExistingBridgeXInstallFolder" />' + "`r`n" +
    '    <SetVariable Id="ResolveBridgeXLaunchWorkingFolder" Variable="BridgeXLaunchWorkingFolder" Value="[ExistingBridgeXInstallFolder]bin" Type="formatted" After="DetectBridgeXExistingInstallFolder" Condition="ExistingBridgeXInstallFolder" />'
if (-not $text.Contains($launchVarNeedle)) { throw 'HOTFIX23_BUNDLE_STATE_PATCH_POINT_MISSING' }
$text = $text.Replace($launchVarNeedle, $stateBlock)

# Preserve existing custom location during Update/Repair by directly setting the
# child MSI directory property. Fresh install keeps Hotfix21 base-folder behavior.
$msiPropertyNeedle = @'
        <MsiProperty Name="INSTALLBASE" Value="[InstallFolder]" />
        <MsiProperty Name="CREATE_DESKTOP_SHORTCUT" Value="[CreateDesktopShortcut]" />
'@
$msiPropertyReplacement = @'
        <MsiProperty Name="INSTALLBASE" Value="[InstallFolder]" Condition="NOT ExistingBridgeXInstallFolder" />
        <MsiProperty Name="INSTALLFOLDER" Value="[ExistingBridgeXInstallFolder]" Condition="ExistingBridgeXInstallFolder" />
        <MsiProperty Name="CREATE_DESKTOP_SHORTCUT" Value="[CreateDesktopShortcut]" />
'@
if (-not $text.Contains($msiPropertyNeedle.Trim())) { throw 'HOTFIX23_MSI_LOCATION_PROPERTY_PATCH_POINT_MISSING' }
$text = $text.Replace($msiPropertyNeedle.Trim(), $msiPropertyReplacement.Trim())

# Finish-launch must also use the detected existing path on Update/Repair rather
# than reconstructing it from the default C: base variable.
$launchTargetOld = '[InstallFolder]TNSuite\BridgeX\bin\BridgeX.exe'
$launchWorkingOld = '[InstallFolder]TNSuite\BridgeX\bin'
if (-not $text.Contains($launchTargetOld) -or -not $text.Contains($launchWorkingOld)) { throw 'HOTFIX23_LAUNCH_PATH_PATCH_POINT_MISSING' }
$text = $text.Replace($launchTargetOld, '[BridgeXLaunchTarget]')
$text = $text.Replace($launchWorkingOld, '[BridgeXLaunchWorkingFolder]')

$bundleBuildNeedle = '& wix build -arch x64 -ext WixToolset.BootstrapperApplications.wixext -o $ExePath $BundleWxs'
$bundleBuildReplacement = '& wix build -arch x64 -ext WixToolset.BootstrapperApplications.wixext -ext WixToolset.Util.wixext -o $ExePath $BundleWxs'
if (-not $text.Contains($bundleBuildNeedle)) { throw 'HOTFIX23_BUNDLE_UTIL_BUILD_PATCH_POINT_MISSING' }
$text = $text.Replace($bundleBuildNeedle, $bundleBuildReplacement)

$text = $text.Replace("Write-Host 'INSTALLER_PROCESS_KILL=NONE'", "Write-Host 'INSTALLER_PROCESS_CLOSE=PRE_INSTALLVALIDATE_TASKKILL_BRIDGEX_ONLY'")
$text = $text.Replace("Write-Host 'WIX_INSTALLER_BUILD=PASS'", "Write-Host 'MAINTENANCE_STATE_DETECTION=PRODUCT_SEARCH'`r`nWrite-Host 'EXISTING_INSTALL_PATH_DETECTION=MSI_COMPONENT_SEARCH'`r`nWrite-Host 'EXISTING_INSTALL_PATH_COMPONENT={492A8EAC-6707-51E3-9723-967A6E4A94D9}'`r`nWrite-Host 'NEWER_SETUP_ACTION=UPDATE'`r`nWrite-Host 'SAME_VERSION_ACTIONS=REPAIR_UNINSTALL'`r`nWrite-Host 'PRE_INSTALLVALIDATE_AUTO_CLOSE_BRIDGEX=ENABLED'`r`nWrite-Host 'AUTO_CLOSE_TARGETS=BridgeX.exe,BridgeX-CLI.exe'`r`nWrite-Host 'AUTO_CLOSE_FORCE=YES'`r`nWrite-Host 'RESTART_MANAGER=DISABLED'`r`nWrite-Host 'AUTO_CLOSE_REBOOT_PROMPT=DISABLED'`r`nWrite-Host 'INSTALL_BASE_MIGRATION=MSI_COMPONENT_DIRECTORY'`r`nWrite-Host 'WIX_INSTALLER_BUILD=PASS'")
'@

$source = $source.Replace($anchor, $injection + "`r`n`r`n" + $anchor)

# Keep generated wrapper beside release scripts so PSScriptRoot resolves the
# base builder and Hotfix23 theme/localization assets.
$tempWrapper = Join-Path $PSScriptRoot ".BridgeX-Hotfix23-Wrapper-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.ps1"
try {
    [System.IO.File]::WriteAllText($tempWrapper, $source, [System.Text.UTF8Encoding]::new($false))
    & pwsh.exe -NoLogo -NoProfile -File $tempWrapper -PortableZip $PortableZip -OutputDirectory $OutputDirectory
    if ($LASTEXITCODE -ne 0) { throw "HOTFIX23_WIX_BUILD_FAILED=$LASTEXITCODE" }
}
finally {
    if (Test-Path -LiteralPath $tempWrapper) { Remove-Item -LiteralPath $tempWrapper -Force -ErrorAction SilentlyContinue }
}
