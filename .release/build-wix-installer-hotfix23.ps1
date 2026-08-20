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
# - standard same-version WixStdBA Modify page (Repair/Uninstall);
# - Burn-level CloseApplication before MSI execution;
# - MSI-level CloseApplication as a fallback;
# - persisted install-base registry values for subsequent upgrades.
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
# Product MSI fallback close. Burn-level close below is intentionally earlier so
# Windows Installer should never need to show Restart Manager / Files In Use for
# BridgeX-owned processes during update/repair/uninstall.
$wixRootNeedle = "[void]`$product.AppendLine('<Wix xmlns=`"http://wixtoolset.org/schemas/v4/wxs`">')"
$wixRootReplacement = "[void]`$product.AppendLine('<Wix xmlns=`"http://wixtoolset.org/schemas/v4/wxs`" xmlns:util=`"http://wixtoolset.org/schemas/v4/wxs/util`">')"
if (-not $text.Contains($wixRootNeedle)) { throw 'HOTFIX23_MSI_UTIL_NAMESPACE_PATCH_POINT_MISSING' }
$text = $text.Replace($wixRootNeedle, $wixRootReplacement)

$upgradeNeedle = "[void]`$product.AppendLine('    <MajorUpgrade DowngradeErrorMessage=`"A newer version of TNSuite BridgeX is already installed.`" />')"
$upgradeReplacement = $upgradeNeedle + "`r`n" +
    "[void]`$product.AppendLine('    <Property Id=`"MSIDISABLERMRESTART`" Value=`"1`" />')" + "`r`n" +
    "[void]`$product.AppendLine('    <util:CloseApplication Id=`"MsiCloseBridgeXGui`" Target=`"BridgeX.exe`" CloseMessage=`"yes`" ElevatedCloseMessage=`"yes`" Timeout=`"3`" TerminateProcess=`"0`" RebootPrompt=`"no`" PromptToContinue=`"no`" />')" + "`r`n" +
    "[void]`$product.AppendLine('    <util:CloseApplication Id=`"MsiCloseBridgeXCli`" Target=`"BridgeX-CLI.exe`" CloseMessage=`"yes`" ElevatedCloseMessage=`"yes`" Timeout=`"3`" TerminateProcess=`"0`" RebootPrompt=`"no`" PromptToContinue=`"no`" />')"
if (-not $text.Contains($upgradeNeedle)) { throw 'HOTFIX23_MSI_CLOSE_PATCH_POINT_MISSING' }
$text = $text.Replace($upgradeNeedle, $upgradeReplacement)

# Persist the base/final installation paths for future upgrade generations.
$registryNeedle = "[void]`$product.AppendLine('      <RegistryValue Root=`"HKLM`" Key=`"Software\\TNSuite\\BridgeX`" Name=`"InstallerGeneration`" Type=`"string`" Value=`"WiX-' + `$BundleVersion + '`" KeyPath=`"yes`" />')"
$registryReplacement = $registryNeedle + "`r`n" +
    "[void]`$product.AppendLine('      <RegistryValue Root=`"HKLM`" Key=`"Software\\TNSuite\\BridgeX`" Name=`"InstallBase`" Type=`"string`" Value=`"[INSTALLBASE]`" />')" + "`r`n" +
    "[void]`$product.AppendLine('      <RegistryValue Root=`"HKLM`" Key=`"Software\\TNSuite\\BridgeX`" Name=`"InstallLocation`" Type=`"string`" Value=`"[INSTALLFOLDER]`" />')" + "`r`n" +
    "[void]`$product.AppendLine('      <RegistryValue Root=`"HKLM`" Key=`"Software\\TNSuite\\BridgeX`" Name=`"InstalledMsiVersion`" Type=`"string`" Value=`"0.5.1223`" />')"
if (-not $text.Contains($registryNeedle)) { throw 'HOTFIX23_INSTALL_LOCATION_REGISTRY_PATCH_POINT_MISSING' }
$text = $text.Replace($registryNeedle, $registryReplacement)

$msiBuildNeedle = '& wix build -arch x64 -o $MsiPath $ProductWxs'
$msiBuildReplacement = '& wix build -arch x64 -ext WixToolset.Util.wixext -o $MsiPath $ProductWxs'
if (-not $text.Contains($msiBuildNeedle)) { throw 'HOTFIX23_MSI_UTIL_BUILD_PATCH_POINT_MISSING' }
$text = $text.Replace($msiBuildNeedle, $msiBuildReplacement)

# Bundle-level detection/close runs before MSI file replacement. ProductSearch
# finds the highest installed MSI sharing the BridgeX product UpgradeCode.
$bundleRootNeedle = '<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs" xmlns:bal="http://wixtoolset.org/schemas/v4/wxs/bal">'
$bundleRootReplacement = '<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs" xmlns:bal="http://wixtoolset.org/schemas/v4/wxs/bal" xmlns:util="http://wixtoolset.org/schemas/v4/wxs/util">'
if (-not $text.Contains($bundleRootNeedle)) { throw 'HOTFIX23_BUNDLE_UTIL_NAMESPACE_PATCH_POINT_MISSING' }
$text = $text.Replace($bundleRootNeedle, $bundleRootReplacement)

$launchVarNeedle = '    <Variable Name="LaunchAfterInstall" Type="numeric" Value="1" Persisted="no" bal:Overridable="yes" />'
$stateBlock = $launchVarNeedle + "`r`n" +
    '    <Variable Name="TargetBridgeXMsiVersion" Type="version" Value="0.5.1223" />' + "`r`n" +
    '    <util:ProductSearch Id="DetectBridgeXProductVersion" UpgradeCode="{B8BF51DD-E1B4-4A6E-B543-1661EF5EA8EA}" Variable="DetectedBridgeXMsiVersion" Result="version" />' + "`r`n" +
    '    <util:RegistrySearch Id="DetectBridgeXInstallBase" Root="HKLM" Key="Software\TNSuite\BridgeX" Value="InstallBase" Variable="InstallFolder" Result="value" Bitness="always64" />' + "`r`n" +
    '    <util:CloseApplication Id="BundleCloseBridgeXCli" Target="BridgeX-CLI.exe" Condition="WixBundleInstalled OR DetectedBridgeXMsiVersion > v0.0.0.0" CloseMessage="yes" Timeout="3" TerminateProcess="0" RebootPrompt="no" PromptToContinue="no" Sequence="1" />' + "`r`n" +
    '    <util:CloseApplication Id="BundleCloseBridgeXGui" Target="BridgeX.exe" Condition="WixBundleInstalled OR DetectedBridgeXMsiVersion > v0.0.0.0" CloseMessage="yes" Timeout="3" TerminateProcess="0" RebootPrompt="no" PromptToContinue="no" Sequence="2" />'
if (-not $text.Contains($launchVarNeedle)) { throw 'HOTFIX23_BUNDLE_STATE_PATCH_POINT_MISSING' }
$text = $text.Replace($launchVarNeedle, $stateBlock)

$bundleBuildNeedle = '& wix build -arch x64 -ext WixToolset.BootstrapperApplications.wixext -o $ExePath $BundleWxs'
$bundleBuildReplacement = '& wix build -arch x64 -ext WixToolset.BootstrapperApplications.wixext -ext WixToolset.Util.wixext -o $ExePath $BundleWxs'
if (-not $text.Contains($bundleBuildNeedle)) { throw 'HOTFIX23_BUNDLE_UTIL_BUILD_PATCH_POINT_MISSING' }
$text = $text.Replace($bundleBuildNeedle, $bundleBuildReplacement)

$text = $text.Replace("Write-Host 'INSTALLER_PROCESS_KILL=NONE'", "Write-Host 'INSTALLER_PROCESS_CLOSE=BURN_PRE_MSI_PLUS_MSI_FALLBACK_BRIDGEX_ONLY'")
$text = $text.Replace("Write-Host 'WIX_INSTALLER_BUILD=PASS'", "Write-Host 'MAINTENANCE_STATE_DETECTION=PRODUCT_SEARCH'`r`nWrite-Host 'NEWER_SETUP_ACTION=UPDATE'`r`nWrite-Host 'SAME_VERSION_ACTIONS=REPAIR_UNINSTALL'`r`nWrite-Host 'PRE_MSI_AUTO_CLOSE_BRIDGEX=ENABLED'`r`nWrite-Host 'AUTO_CLOSE_FORCE_TERMINATE_FALLBACK=BRIDGEX_ONLY'`r`nWrite-Host 'AUTO_CLOSE_REBOOT_PROMPT=DISABLED'`r`nWrite-Host 'INSTALL_BASE_PERSISTENCE=HKLM_SOFTWARE_TNSUITE_BRIDGEX'`r`nWrite-Host 'WIX_INSTALLER_BUILD=PASS'")
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
