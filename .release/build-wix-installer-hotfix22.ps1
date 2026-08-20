[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PortableZip,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$hotfix21 = Join-Path $PSScriptRoot 'build-wix-installer-hotfix21.ps1'
if (-not (Test-Path -LiteralPath $hotfix21)) { throw "HOTFIX22_BASE_MISSING=$hotfix21" }

# Reuse the accepted Hotfix21 location/shortcut/launch UX and inject only the
# standard WiX Util CloseApplication behavior needed for clean upgrade/uninstall.
$source = Get-Content -LiteralPath $hotfix21 -Raw -Encoding UTF8
$source = $source.Replace('TNSuiteBridgeX_260820_v0.5-Build12-Hotfix21-WiX', 'TNSuiteBridgeX_260820_v0.5-Build12-Hotfix22-WiX')
$source = $source.Replace("0.5.1221", "0.5.1222")
$source = $source.Replace("0.5.12.21", "0.5.12.22")
$source = $source.Replace('HOTFIX21_WIX_BUILD_FAILED', 'HOTFIX22_WIX_BUILD_FAILED')
$source = $source.Replace('BridgeX-Hotfix21-WiX-', 'BridgeX-Hotfix22-WiX-')
$source = $source.Replace('INSTALLER_THEME=HOTFIX21_LOCATION_AND_FINISH_OPTIONS', 'INSTALLER_THEME=HOTFIX22_AUTO_CLOSE_AND_CLEAN_UNINSTALL')

$anchor = '$tempBuilder = Join-Path $env:RUNNER_TEMP "BridgeX-Hotfix22-WiX-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.ps1"'
if (-not $source.Contains($anchor)) { throw 'HOTFIX22_INJECTION_ANCHOR_MISSING' }

$injection = @'
# Hotfix22: use WiX Util CloseApplication instead of taskkill/process helper.
# Send WM_CLOSE first, wait 4 seconds, then terminate only the exact BridgeX
# executable if it still owns files. RebootPrompt=no avoids the Files In Use
# reboot path for this product-owned process. The same rule applies to CLI.
$wixRootNeedle = "[void]`$product.AppendLine('<Wix xmlns=`"http://wixtoolset.org/schemas/v4/wxs`">')"
$wixRootReplacement = "[void]`$product.AppendLine('<Wix xmlns=`"http://wixtoolset.org/schemas/v4/wxs`" xmlns:util=`"http://wixtoolset.org/schemas/v4/wxs/util`">')"
if (-not $text.Contains($wixRootNeedle)) { throw 'HOTFIX22_WIX_UTIL_NAMESPACE_PATCH_POINT_MISSING' }
$text = $text.Replace($wixRootNeedle, $wixRootReplacement)

$upgradeNeedle = "[void]`$product.AppendLine('    <MajorUpgrade DowngradeErrorMessage=`"A newer version of TNSuite BridgeX is already installed.`" />')"
$upgradeReplacement = $upgradeNeedle + "`r`n" +
    "[void]`$product.AppendLine('    <Property Id=`"MSIDISABLERMRESTART`" Value=`"1`" />')" + "`r`n" +
    "[void]`$product.AppendLine('    <util:CloseApplication Id=`"CloseBridgeXGui`" Target=`"BridgeX.exe`" CloseMessage=`"yes`" ElevatedCloseMessage=`"yes`" Timeout=`"4`" TerminateProcess=`"0`" RebootPrompt=`"no`" PromptToContinue=`"no`" />')" + "`r`n" +
    "[void]`$product.AppendLine('    <util:CloseApplication Id=`"CloseBridgeXCli`" Target=`"BridgeX-CLI.exe`" CloseMessage=`"yes`" ElevatedCloseMessage=`"yes`" Timeout=`"4`" TerminateProcess=`"0`" RebootPrompt=`"no`" PromptToContinue=`"no`" />')"
if (-not $text.Contains($upgradeNeedle)) { throw 'HOTFIX22_CLOSE_APPLICATION_PATCH_POINT_MISSING' }
$text = $text.Replace($upgradeNeedle, $upgradeReplacement)

$msiBuildNeedle = '& wix build -arch x64 -o $MsiPath $ProductWxs'
$msiBuildReplacement = '& wix build -arch x64 -ext WixToolset.Util.wixext -o $MsiPath $ProductWxs'
if (-not $text.Contains($msiBuildNeedle)) { throw 'HOTFIX22_UTIL_EXTENSION_BUILD_PATCH_POINT_MISSING' }
$text = $text.Replace($msiBuildNeedle, $msiBuildReplacement)

$text = $text.Replace("Write-Host 'INSTALLER_PROCESS_KILL=NONE'", "Write-Host 'INSTALLER_PROCESS_CLOSE=STANDARD_WIX_UTIL_CLOSEAPPLICATION_BRIDGEX_ONLY'")
$text = $text.Replace("Write-Host 'WIX_INSTALLER_BUILD=PASS'", "Write-Host 'AUTO_CLOSE_BRIDGEX_ON_UPGRADE_UNINSTALL=ENABLED'`r`nWrite-Host 'AUTO_CLOSE_GRACEFUL_TIMEOUT_SECONDS=4'`r`nWrite-Host 'AUTO_CLOSE_FORCE_TERMINATE_FALLBACK=BRIDGEX_ONLY'`r`nWrite-Host 'AUTO_CLOSE_REBOOT_PROMPT=DISABLED'`r`nWrite-Host 'WIX_INSTALLER_BUILD=PASS'")
'@

$source = $source.Replace($anchor, $injection + "`r`n`r`n" + $anchor)
$tempWrapper = Join-Path $env:RUNNER_TEMP "BridgeX-Hotfix22-Wrapper-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT.ps1"
[System.IO.File]::WriteAllText($tempWrapper, $source, [System.Text.UTF8Encoding]::new($false))

& pwsh.exe -NoLogo -NoProfile -File $tempWrapper -PortableZip $PortableZip -OutputDirectory $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw "HOTFIX22_WIX_BUILD_FAILED=$LASTEXITCODE" }
