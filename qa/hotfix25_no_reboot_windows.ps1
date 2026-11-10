[CmdletBinding()]
param(
 [Parameter(Mandatory=$true)][string]$PortableZip,
 [Parameter(Mandatory=$true)][string]$Hotfix25Setup,
 [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedBridgeXSha256
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=Join-Path $env:RUNNER_TEMP 'BridgeX-NoReboot-QA'
$base=Join-Path $root 'selected-parent'
$install=Join-Path $base 'TNSuite\BridgeX'
$exe=Join-Path $install 'bin\BridgeX.exe'
$active=$null
if (!(Test-Path -LiteralPath $PortableZip)) { throw 'MISSING_PORTABLE' }
if (!(Test-Path -LiteralPath $Hotfix25Setup)) { throw 'MISSING_SETUP' }
if (Test-Path $root) { Remove-Item $root -Recurse -Force }
New-Item $root -ItemType Directory -Force | Out-Null

# The Burn exit code alone cannot distinguish MSI custom-action, file-lock,
# reboot or registration failures. Keep exact GitHub-hosted MSI/Burn diagnostics
# for every failed case; do not downgrade 1603 or 3010 into PASS.
function Write-FailureEvidence([string]$case,[string]$reason) {
 $summary=Join-Path $root 'windows-qa-failure-summary.txt'
 "CASE=$case REASON=$reason" | Out-File -LiteralPath $summary -Encoding utf8 -Append
 $logs=@(Get-ChildItem -LiteralPath $root -Filter '*.log' -File -Recurse -ErrorAction SilentlyContinue)
 foreach ($file in $logs) {
  "DIAGNOSTIC_LOG=$($file.FullName)" | Out-File -LiteralPath $summary -Encoding utf8 -Append
  Write-Host "HF25_DIAGNOSTIC_LOG=$($file.Name)"
  $matches=@(Select-String -LiteralPath $file.FullName -Pattern @(
   'Return value 3', '1603', '3010', '0x80070643', '0x80070020',
   'Error 1[0-9]{3}', 'Info 1903', 'ReplacedInUseFiles',
   'restart: Required', 'ForceCloseBridgeX', 'WixQuietExec',
   'MSIRESTARTMANAGERCONTROL', 'Failed to execute', 'failed to install'
  ) -ErrorAction SilentlyContinue | Select-Object -Last 45)
  foreach ($match in $matches) {
   $item="$($file.Name):$($match.LineNumber): $($match.Line)"
   $item | Out-File -LiteralPath $summary -Encoding utf8 -Append
   Write-Host "HF25_DIAGNOSTIC=$item"
  }
 }
 if ($logs.Count -eq 0) {
  'DIAGNOSTIC_LOGS=MISSING' | Out-File -LiteralPath $summary -Encoding utf8 -Append
  Write-Host 'HF25_DIAGNOSTIC_LOGS=MISSING'
 }
}
function Run-Setup([string]$case,[string]$setup,[string[]]$arguments) {
 $log=Join-Path $root "$case-burn.log"
 $argsToRun=@($arguments)+@('/log',$log)
 $p=Start-Process -FilePath $setup -ArgumentList $argsToRun -PassThru -Wait
 if ($p.ExitCode -ne 0) {
  try { Write-FailureEvidence $case "INSTALLER_EXIT_$($p.ExitCode)" }
  catch { Write-Warning "HF25_DIAGNOSTIC_COLLECTION_FAILED=$($_.Exception.Message)" }
  throw "$($case)=FAIL exit=$($p.ExitCode) log=$log (3010 not accepted)"
 }
 $logs=@(Get-ChildItem -LiteralPath $root -Filter "$case-burn*.log" -File)
 foreach($f in $logs) {
  $reboot=Select-String -LiteralPath $f.FullName -Pattern 'Info 1903.Scheduling reboot operation','MainEngineThread is returning 3010','ReplacedInUseFiles property. Its value is .1.','i319:.*restart: Required','i399:.*restart: Required'
  if($reboot){
   try { Write-FailureEvidence $case "REBOOT_MARKER_$($f.Name)" }
   catch { Write-Warning "HF25_DIAGNOSTIC_COLLECTION_FAILED=$($_.Exception.Message)" }
   throw "$($case)=FAIL reboot log=$($f.Name): $($reboot[0].Line)"
  }
 }
 Write-Host "$($case)=PASS exit=0"
}
function Start-App([string]$case) {
 if (!(Test-Path $exe)) { throw "$($case)=FAIL EXE_MISSING" }
 $script:active=Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) -PassThru
 Start-Sleep -Seconds 5
 $script:active.Refresh()
 if($script:active.HasExited){ throw "$($case)=FAIL GUI_NOT_RUNNING exit=$($script:active.ExitCode)" }
 Write-Host "$($case)_RUNNING_APP=PASS"
}
function Assert-Closed([string]$case) {
 if($null -eq $script:active){throw "$($case)=FAIL NO_PRECONDITION"}
 $script:active.WaitForExit(10000)|Out-Null
 $script:active.Refresh()
 if(!$script:active.HasExited){throw "$($case)=FAIL GUI_NOT_CLOSED pid=$($script:active.Id)"}
 $script:active=$null
 Write-Host "$($case)_PROCESS_CLOSED=PASS"
}
function Assert-Hash([string]$case) {
 if(!(Test-Path $exe)){ throw "$($case)=FAIL EXE_MISSING_AFTER_INSTALL" }
 $sha=(Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash.ToLowerInvariant()
 if($sha -ne $ExpectedBridgeXSha256.ToLowerInvariant()){throw "$($case)=FAIL RUNTIME_HASH=$sha"}
}
try {
 # First-ever MSI registration while previous/portable BridgeX holds target DLLs.
 New-Item -ItemType Directory -Path $install -Force|Out-Null
 Expand-Archive -LiteralPath $PortableZip -DestinationPath $install -Force
 Start-App 'FRESH_LOCKED_PRECONDITION'
 Run-Setup 'FRESH_INSTALL' $Hotfix25Setup @('/quiet','/norestart',("InstallFolder={0}" -f $base),'CreateDesktopShortcut=0','LaunchAfterInstall=0')
 Assert-Closed 'FRESH_INSTALL'
 Assert-Hash 'FRESH_INSTALL'
 Run-Setup 'FRESH_UNINSTALL' $Hotfix25Setup @('/uninstall','/quiet','/norestart')
 if(Test-Path $exe){throw 'FRESH_UNINSTALL=FAIL MANAGED_EXE_REMAINS'}

 # Registered WiX Hotfix24 -> Hotfix25 while GUI running.
 if(Test-Path $base){Remove-Item $base -Recurse -Force}
 $prevOut=Join-Path $root 'hotfix24'
 New-Item $prevOut -ItemType Directory -Force|Out-Null
 & pwsh.exe -NoLogo -NoProfile -File '.\.release\build-wix-installer-hotfix24.ps1' -PortableZip $PortableZip -OutputDirectory $prevOut -ExpectedBridgeXSha256 $ExpectedBridgeXSha256
 if($LASTEXITCODE -ne 0){throw "PREVIOUS_BUILDER=FAIL exit=$LASTEXITCODE"}
 $prevSetup=Join-Path $prevOut 'TNSuiteBridgeX_260821_v0.5-Build12-Hotfix24-WiX-Setup.exe'
 if(!(Test-Path $prevSetup)){throw 'PREVIOUS_SETUP_NOT_FOUND'}
 Run-Setup 'PREVIOUS_INSTALL' $prevSetup @('/quiet','/norestart',("InstallFolder={0}" -f $base),'CreateDesktopShortcut=0','LaunchAfterInstall=0')
 Start-App 'UPGRADE_PRECONDITION'
 Run-Setup 'UPGRADE' $Hotfix25Setup @('/quiet','/norestart','LaunchAfterInstall=0')
 Assert-Closed 'UPGRADE'
 Assert-Hash 'UPGRADE'
 Start-App 'REPAIR_PRECONDITION'
 Run-Setup 'REPAIR' $Hotfix25Setup @('/repair','/quiet','/norestart','LaunchAfterInstall=0')
 Assert-Closed 'REPAIR'
 Assert-Hash 'REPAIR'
 Start-App 'UNINSTALL_PRECONDITION'
 Run-Setup 'UNINSTALL' $Hotfix25Setup @('/uninstall','/quiet','/norestart')
 Assert-Closed 'UNINSTALL'
 if(Test-Path $exe){throw 'UNINSTALL=FAIL MANAGED_EXE_REMAINS'}
 Write-Host 'HF25_NO_REBOOT_WINDOWS_QA=PASS'
}
finally {
 if($null -ne $script:active){
  try{ $script:active.Refresh();if(!$script:active.HasExited){Stop-Process -Id $script:active.Id -Force -ErrorAction SilentlyContinue}}catch{}
 }
}
