[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$BuildName = 'TNSuiteBridgeX_260818_v0.5-Build12-Hotfix16-Full'
$KitRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$FreshBuildBase = Join-Path $env:LOCALAPPDATA 'TNSuiteBridgeXBuild12Hotfix1'
$BridgeXBuild11Base = Join-Path $env:LOCALAPPDATA 'TNSuiteBridgeXBuild11Hotfix1'
$LegacyBuildBase = Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild01'

# Prefer an already-proven isolated environment. Build11-Hotfix1 is checked
# first because the user's current machine already compiled BridgeX successfully
# there and it contains the exact UCRT64 gettext/NSIS dependencies we need.
$BuildBase = $null
foreach ($candidate in @($BridgeXBuild11Base, $LegacyBuildBase, $FreshBuildBase)) {
    if (Test-Path (Join-Path $candidate 'msys64\usr\bin\bash.exe')) {
        $BuildBase = $candidate
        Write-Host "Reusing isolated MSYS2: $BuildBase" -ForegroundColor DarkGray
        break
    }
}
if (-not $BuildBase) {
    $BuildBase = $FreshBuildBase
}

$MsysRoot = Join-Path $BuildBase 'msys64'
$Installer = Join-Path $BuildBase 'msys2-x86_64-20260611.exe'
$InstallerUrl = 'https://github.com/msys2/msys2-installer/releases/download/2026-06-11/msys2-x86_64-20260611.exe'
$InstallerSha256 = '3150D7D9AA5DEDD900A7F52300D4D918271E3A8FC47DE94848818FD5A430E6B0'
$ExpectedZip = Join-Path $KitRoot "dist\$BuildName.zip"
$ExpectedSetup = Join-Path $KitRoot "dist\$BuildName-Setup.exe"

function Write-Step([string]$Text) {
    Write-Host "`n=== $Text ===" -ForegroundColor Cyan
}

if (-not [Environment]::Is64BitOperatingSystem) {
    throw 'TNSuite BridgeX Build12-Hotfix16 requires 64-bit Windows.'
}

New-Item -ItemType Directory -Force -Path $BuildBase | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $KitRoot 'dist') | Out-Null

Write-Step 'Prepare isolated MSYS2 build environment'
$FreshInstall = -not (Test-Path (Join-Path $MsysRoot 'usr\bin\bash.exe'))
if ($FreshInstall) {
    if (-not (Test-Path $Installer)) {
        Write-Host 'Downloading official MSYS2 2026-06-11 installer...'
        Invoke-WebRequest -Uri $InstallerUrl -OutFile $Installer
    }

    $actual = (Get-FileHash -Algorithm SHA256 -Path $Installer).Hash.ToUpperInvariant()
    if ($actual -ne $InstallerSha256) {
        Remove-Item -Force $Installer -ErrorAction SilentlyContinue
        throw "MSYS2 installer SHA-256 mismatch. Expected $InstallerSha256, got $actual"
    }

    & $Installer in --confirm-command --accept-messages --root ($MsysRoot -replace '\\','/')
    $exit = $LASTEXITCODE
    if ($exit -notin @(0,2)) {
        throw "MSYS2 installer exited with code $exit"
    }

    $bash = Join-Path $MsysRoot 'usr\bin\bash.exe'
    $deadline = (Get-Date).AddMinutes(5)
    while (-not (Test-Path $bash)) {
        if ((Get-Date) -gt $deadline) { throw 'Timed out waiting for MSYS2 installation.' }
        Start-Sleep -Seconds 2
    }
}

$BashExe = Join-Path $MsysRoot 'usr\bin\bash.exe'
if (-not (Test-Path $BashExe)) { throw "MSYS2 bash not found: $BashExe" }

# The bootstrap EXE is no longer needed once the isolated environment exists.
if (Test-Path $Installer) { Remove-Item -Force $Installer -ErrorAction SilentlyContinue }

$env:CHERE_INVOKING = 'yes'
$env:MSYSTEM = 'UCRT64'
$env:FZDARK_KIT_WIN = $KitRoot

Write-Step 'Check isolated MSYS2 readiness'
# Build12 does not perform a rolling MSYS2 full-upgrade on an existing isolated
# environment. The build script installs only missing packages with --needed.
# This avoids mirror churn, runtime downgrade/upgrade loops and unnecessary disk writes.
if (-not $FreshInstall) {
    Write-Host 'BUILD_ENV=REUSED; full MSYS2 upgrade skipped.' -ForegroundColor Green
}
else {
    Write-Step 'Initialize fresh isolated MSYS2'
    # A brand-new MSYS2 root needs its core runtime synchronized before current
    # UCRT64 packages can be installed. Run in separate processes because the
    # runtime may replace itself during pass 1.
    & $BashExe -lc 'pacman --noconfirm -Syu'
    if ($LASTEXITCODE -ne 0) { throw "Initial MSYS2 core update failed: $LASTEXITCODE" }
    & $BashExe -lc 'pacman --noconfirm -Syu'
    if ($LASTEXITCODE -ne 0) { throw "Second MSYS2 update pass failed: $LASTEXITCODE" }
}

Write-Step 'Build TNSuite BridgeX'
# Build01 used a nested `bash -lc 'KIT="$(...)" ...'` command. Windows PowerShell
# can mangle nested quotes before they reach MSYS2. Build12 uses a real launcher
# script instead, eliminating that quoting boundary entirely.
$RunnerWin = Join-Path $MsysRoot 'tmp\tnsuite-bridgex-build12-hotfix16-runner.sh'
$runner = @'
#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${FZDARK_KIT_WIN:-}" ]]; then
  echo "ERROR: FZDARK_KIT_WIN is not set." >&2
  exit 90
fi
KIT="$(cygpath -u "$FZDARK_KIT_WIN")"
exec bash "$KIT/scripts/build-filezilla-dark.sh"
'@
$runner = $runner -replace "`r`n", "`n"
[System.IO.File]::WriteAllText($RunnerWin, $runner, [System.Text.UTF8Encoding]::new($false))

& $BashExe --login '/tmp/tnsuite-bridgex-build12-hotfix16-runner.sh'
if ($LASTEXITCODE -ne 0) { throw "TNSuite BridgeX Build12-Hotfix16 build failed: $LASTEXITCODE" }

if (-not (Test-Path $ExpectedZip)) {
    throw "Build reported success but artifact is missing: $ExpectedZip"
}
if (-not (Test-Path $ExpectedSetup)) {
    throw "Build reported success but installer is missing: $ExpectedSetup"
}

Write-Step 'Windows runtime QA for automation CLI'
$RuntimeQa = Join-Path $env:TEMP 'TNSuiteBridgeXBuild12Hotfix11-RuntimeQA'
if (Test-Path $RuntimeQa) { Remove-Item -LiteralPath $RuntimeQa -Recurse -Force }
New-Item -ItemType Directory -Force -Path $RuntimeQa | Out-Null
try {
    Expand-Archive -LiteralPath $ExpectedZip -DestinationPath $RuntimeQa -Force
    $CliExe = Join-Path $RuntimeQa 'bin\BridgeX-CLI.exe'
    if (-not (Test-Path $CliExe)) { throw "CLI executable missing from artifact: $CliExe" }

    $selfJson = (& $CliExe --selftest --json | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "CLI selftest failed with exit code $LASTEXITCODE. Output: $selfJson" }
    $self = $selfJson | ConvertFrom-Json
    if (-not $self.ok -or $self.selftest -ne 'PASS') { throw "CLI selftest did not report PASS: $selfJson" }
    Write-Host 'CLI_WINDOWS_RUNTIME_SELFTEST=PASS' -ForegroundColor Green

    $doctorJson = (& $CliExe doctor --json | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) { throw "CLI doctor failed. Windows OpenSSH client is required. Output: $doctorJson" }
    $doctor = $doctorJson | ConvertFrom-Json
    if (-not $doctor.ok -or -not $doctor.sftp_found) { throw "CLI doctor did not find Windows OpenSSH sftp.exe: $doctorJson" }
    Write-Host 'CLI_WINDOWS_OPENSSH_DOCTOR=PASS' -ForegroundColor Green
}
finally {
    Remove-Item -LiteralPath $RuntimeQa -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Step 'Artifact verification'
$hash = (Get-FileHash -Algorithm SHA256 -Path $ExpectedZip).Hash
Write-Host 'BUILD=PASS' -ForegroundColor Green
Write-Host "ARTIFACT=$ExpectedZip"
Write-Host "SHA256=$hash"
$setupHash = (Get-FileHash -Algorithm SHA256 -Path $ExpectedSetup).Hash
Write-Host "INSTALLER=$ExpectedSetup"
Write-Host "INSTALLER_SHA256=$setupHash"
Write-Host 'INSTALLER_BUILD_QA=PASS' -ForegroundColor Green
Write-Host "`nInstaller: $ExpectedSetup" -ForegroundColor Green
Write-Host "Installed Start Menu entry: TNSuite BridgeX > TNSuite BridgeX" -ForegroundColor Green
Write-Host "GUI portable: bin\BridgeX.exe" -ForegroundColor Green
Write-Host "CLI: bin\BridgeX-CLI.exe --help" -ForegroundColor Green
Write-Host 'Windows Contrast Theme was not changed.' -ForegroundColor Green
Write-Host 'Transient source/object/package caches were cleaned after packaging.' -ForegroundColor Green
Write-Host 'To remove the remaining isolated compiler/MSYS2 environment, run Cleanup.cmd.' -ForegroundColor Yellow
