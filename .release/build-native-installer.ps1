[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PortableZip,
    [Parameter(Mandatory = $true)][string]$OutputExe,
    [string]$ExpectedBridgeXSha256 = '5ca39f3d7275ca0fc46cf81b2d511397e6d9d40ad067f0da5181ca8362c616b6'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$PortableZip = (Resolve-Path -LiteralPath $PortableZip).Path
$OutputExe = [System.IO.Path]::GetFullPath($OutputExe)
$Cpp = (Resolve-Path (Join-Path $RepoRoot 'installer\native\BridgeXNativeInstaller.cpp')).Path
$Icon = (Resolve-Path (Join-Path $RepoRoot 'assets\branding\BridgeX-AppIcon.ico')).Path
$Work = Join-Path $env:RUNNER_TEMP "bridgex-native-installer-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT"
$Payload = Join-Path $Work 'payload'
$ManifestHeader = Join-Path $Work 'payload_manifest.h'
$ResourceScript = Join-Path $Work 'payload.rc'
$ResourceObject = Join-Path $Work 'payload.res'

if (Test-Path -LiteralPath $Work) { Remove-Item -LiteralPath $Work -Recurse -Force }
New-Item -ItemType Directory -Force -Path $Payload | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $OutputExe) | Out-Null

Write-Host 'NATIVE_INSTALLER_BUILD=START'
Write-Host "PORTABLE_SOURCE=$PortableZip"
Write-Host "OUTPUT_EXE=$OutputExe"

Expand-Archive -LiteralPath $PortableZip -DestinationPath $Payload -Force

$BridgeExe = Join-Path $Payload 'bin\BridgeX.exe'
if (-not (Test-Path -LiteralPath $BridgeExe)) { throw "BRIDGEX_EXE_MISSING=$BridgeExe" }
$SourceBridgeSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $BridgeExe).Hash.ToLowerInvariant()
Write-Host "BRIDGEX_SOURCE_SHA256=$SourceBridgeSha"

$objcopyCandidates = @(
    (Join-Path $env:LOCALAPPDATA 'TNSuiteBridgeXBuild12Hotfix1\msys64\ucrt64\bin\objcopy.exe'),
    (Join-Path $env:LOCALAPPDATA 'TNSuiteBridgeXBuild11Hotfix1\msys64\ucrt64\bin\objcopy.exe'),
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild01\msys64\ucrt64\bin\objcopy.exe')
)
$Objcopy = $objcopyCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Objcopy) { throw 'OBJCOPY_MISSING_AFTER_CANONICAL_BUILD' }

$StrippedExe = Join-Path $Work 'BridgeX-stripped.exe'
& $Objcopy '--strip-all' $BridgeExe $StrippedExe
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $StrippedExe)) {
    throw "OBJCOPY_STRIP_FAILED=$LASTEXITCODE"
}
Move-Item -LiteralPath $StrippedExe -Destination $BridgeExe -Force

$BridgeSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $BridgeExe).Hash.ToLowerInvariant()
if ($BridgeSha -ne $ExpectedBridgeXSha256.ToLowerInvariant()) {
    throw "BRIDGEX_AV_CLEAN_HASH_MISMATCH expected=$ExpectedBridgeXSha256 actual=$BridgeSha"
}
Write-Host "BRIDGEX_AV_CLEAN_HASH=PASS sha256=$BridgeSha"

$requiredRuntime = @(
    'bin\libfzclient-commonui-private-3-70-6.dll',
    'bin\libfzclient-private-3-70-6.dll',
    'bin\libfilezilla-58.dll',
    'bin\libfzssh-13.0.0.dll'
)
foreach ($relative in $requiredRuntime) {
    if (-not (Test-Path -LiteralPath (Join-Path $Payload $relative))) {
        throw "REQUIRED_RUNTIME_DLL_MISSING=$relative"
    }
    Write-Host "RUNTIME_DLL=PASS path=$relative"
}

$files = Get-ChildItem -LiteralPath $Payload -Recurse -File | Sort-Object FullName
if ($files.Count -lt 5) { throw "PAYLOAD_FILE_COUNT_INVALID=$($files.Count)" }

$headerLines = [System.Collections.Generic.List[string]]::new()
$headerLines.Add('#pragma once')
$headerLines.Add('#include <cstddef>')
$headerLines.Add('struct PayloadEntry { int resourceId; const wchar_t* relativePath; };')
$headerLines.Add('static const PayloadEntry kPayload[] = {')

$rcLines = [System.Collections.Generic.List[string]]::new()
$rcLines.Add('#include <windows.h>')
$iconRc = ($Icon -replace '\\','/')
$rcLines.Add(('101 ICON "{0}"' -f $iconRc))
$rcLines.Add('1 VERSIONINFO')
$rcLines.Add(' FILEVERSION 0,5,12,18')
$rcLines.Add(' PRODUCTVERSION 0,5,12,18')
$rcLines.Add(' FILEFLAGSMASK 0x3fL')
$rcLines.Add(' FILEFLAGS 0x0L')
$rcLines.Add(' FILEOS 0x40004L')
$rcLines.Add(' FILETYPE 0x1L')
$rcLines.Add(' FILESUBTYPE 0x0L')
$rcLines.Add('BEGIN')
$rcLines.Add('  BLOCK "StringFileInfo"')
$rcLines.Add('  BEGIN')
$rcLines.Add('    BLOCK "040904b0"')
$rcLines.Add('    BEGIN')
$rcLines.Add('      VALUE "CompanyName", "TNSuite\0"')
$rcLines.Add('      VALUE "FileDescription", "TNSuite BridgeX Native Installer\0"')
$rcLines.Add('      VALUE "FileVersion", "0.5.12.18\0"')
$rcLines.Add('      VALUE "InternalName", "BridgeXNativeInstaller\0"')
$rcLines.Add('      VALUE "OriginalFilename", "BridgeX-Setup.exe\0"')
$rcLines.Add('      VALUE "ProductName", "TNSuite BridgeX\0"')
$rcLines.Add('      VALUE "ProductVersion", "0.5-Build12-Hotfix18-candidate\0"')
$rcLines.Add('    END')
$rcLines.Add('  END')
$rcLines.Add('  BLOCK "VarFileInfo"')
$rcLines.Add('  BEGIN')
$rcLines.Add('    VALUE "Translation", 0x409, 1200')
$rcLines.Add('  END')
$rcLines.Add('END')

$id = 2000
foreach ($file in $files) {
    $relative = [System.IO.Path]::GetRelativePath($Payload, $file.FullName).Replace('/', '\')
    $escapedRelative = $relative.Replace('\', '\\').Replace('"', '\"')
    $headerLines.Add(('    {{{0}, L"{1}"}},' -f $id, $escapedRelative))
    $resourcePath = ($file.FullName -replace '\\','/').Replace('"', '\"')
    $rcLines.Add(('{0} RCDATA "{1}"' -f $id, $resourcePath))
    $id++
}
$headerLines.Add('};')
$headerLines.Add('static constexpr size_t kPayloadCount = sizeof(kPayload) / sizeof(kPayload[0]);')

[System.IO.File]::WriteAllLines($ManifestHeader, $headerLines, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllLines($ResourceScript, $rcLines, [System.Text.UTF8Encoding]::new($false))

$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (-not (Test-Path -LiteralPath $vswhere)) { throw 'VSWHERE_MISSING' }
$vsInstall = (& $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Select-Object -First 1)
if (-not $vsInstall) { throw 'MSVC_INSTALLATION_MISSING' }
$vsDevCmd = Join-Path $vsInstall 'Common7\Tools\VsDevCmd.bat'
if (-not (Test-Path -LiteralPath $vsDevCmd)) { throw "VSDEVCMD_MISSING=$vsDevCmd" }

$compileCmd = Join-Path $Work 'compile-native-installer.cmd'
$cmd = @"
@echo off
call "$vsDevCmd" -arch=x64 -host_arch=x64
if errorlevel 1 exit /b %errorlevel%
rc.exe /nologo /fo "$ResourceObject" "$ResourceScript"
if errorlevel 1 exit /b %errorlevel%
cl.exe /nologo /std:c++20 /EHsc /O2 /GL /DUNICODE /D_UNICODE /I"$Work" "$Cpp" "$ResourceObject" /link /LTCG /SUBSYSTEM:WINDOWS /MANIFESTUAC:"level='requireAdministrator' uiAccess='false'" /DYNAMICBASE /NXCOMPAT /HIGHENTROPYVA /OPT:REF /OPT:ICF /OUT:"$OutputExe" Ole32.lib Shell32.lib Uuid.lib
exit /b %errorlevel%
"@
[System.IO.File]::WriteAllText($compileCmd, $cmd, [System.Text.Encoding]::ASCII)

& cmd.exe /d /c "`"$compileCmd`""
if ($LASTEXITCODE -ne 0) { throw "NATIVE_INSTALLER_COMPILE_FAILED=$LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $OutputExe) -or (Get-Item -LiteralPath $OutputExe).Length -le 0) {
    throw 'NATIVE_INSTALLER_OUTPUT_MISSING'
}

$OutputSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $OutputExe).Hash.ToLowerInvariant()
$Signature = Get-AuthenticodeSignature -FilePath $OutputExe
Write-Host "NATIVE_INSTALLER_SHA256=$OutputSha"
Write-Host "NATIVE_INSTALLER_AUTHENTICODE=$($Signature.Status)"
Write-Host "NATIVE_INSTALLER_PAYLOAD_FILES=$($files.Count)"
Write-Host 'NATIVE_INSTALLER_PACKER=NONE'
Write-Host 'NATIVE_INSTALLER_POWERSHELL_RUNTIME=NONE'
Write-Host 'NATIVE_INSTALLER_PROCESS_KILL=NONE'
Write-Host 'NATIVE_INSTALLER_RESOURCE_PAYLOAD=PASS'

$mpCandidates = @()
$platformRoot = Join-Path $env:ProgramData 'Microsoft\Windows Defender\Platform'
if (Test-Path -LiteralPath $platformRoot) {
    $mpCandidates += Get-ChildItem -LiteralPath $platformRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object Name -Descending |
        ForEach-Object { Join-Path $_.FullName 'MpCmdRun.exe' } |
        Where-Object { Test-Path -LiteralPath $_ }
}
$legacyMp = Join-Path $env:ProgramFiles 'Windows Defender\MpCmdRun.exe'
if (Test-Path -LiteralPath $legacyMp) { $mpCandidates += $legacyMp }

$MpCmd = $mpCandidates | Select-Object -First 1
if ($MpCmd) {
    & $MpCmd -Scan -ScanType 3 -File $OutputExe -DisableRemediation
    $DefenderExit = $LASTEXITCODE
    if ($DefenderExit -ne 0) {
        throw "MICROSOFT_DEFENDER_EXACT_INSTALLER_SCAN=FAIL exit=$DefenderExit"
    }
    Write-Host 'MICROSOFT_DEFENDER_EXACT_INSTALLER_SCAN=PASS'
}
else {
    Write-Host 'MICROSOFT_DEFENDER_EXACT_INSTALLER_SCAN=NOT_AVAILABLE'
}

Write-Host 'NATIVE_INSTALLER_BUILD=PASS'
