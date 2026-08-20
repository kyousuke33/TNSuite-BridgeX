[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PayloadZip,
    [Parameter(Mandatory = $true)][string]$OutputMsi,
    [string]$ProductVersion = '0.5.12.18',
    [string]$ProductDisplayName = 'TNSuite BridgeX',
    [string]$Manufacturer = 'TNSuite'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

function Resolve-WixTool([string]$Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $roots = @(
        (Join-Path ${env:ProgramFiles(x86)} 'WiX Toolset v3.14\bin'),
        (Join-Path ${env:ProgramFiles(x86)} 'WiX Toolset v3.11\bin')
    )
    foreach ($root in $roots) {
        $candidate = Join-Path $root $Name
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    throw "WIX_TOOL_MISSING=$Name"
}

$Heat = Resolve-WixTool 'heat.exe'
$Candle = Resolve-WixTool 'candle.exe'
$Light = Resolve-WixTool 'light.exe'

if (-not (Test-Path -LiteralPath $PayloadZip)) {
    throw "MSI_PAYLOAD_ZIP_MISSING=$PayloadZip"
}

$OutputMsi = [System.IO.Path]::GetFullPath($OutputMsi)
$OutputDir = Split-Path -Parent $OutputMsi
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$WorkRoot = Join-Path $env:RUNNER_TEMP "bridgex-msi-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT"
$PayloadDir = Join-Path $WorkRoot 'payload'
$ObjDir = Join-Path $WorkRoot 'obj'
$ProductWxs = Join-Path $WorkRoot 'product.wxs'
$PayloadWxs = Join-Path $WorkRoot 'payload.wxs'
$ProductObj = Join-Path $ObjDir 'product.wixobj'
$PayloadObj = Join-Path $ObjDir 'payload.wixobj'

if (Test-Path -LiteralPath $WorkRoot) {
    Remove-Item -LiteralPath $WorkRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $PayloadDir, $ObjDir | Out-Null
Expand-Archive -LiteralPath $PayloadZip -DestinationPath $PayloadDir -Force

$BridgeXExe = Join-Path $PayloadDir 'bin\BridgeX.exe'
$BridgeXCli = Join-Path $PayloadDir 'bin\BridgeX-CLI.exe'
if (-not (Test-Path -LiteralPath $BridgeXExe)) { throw "MSI_PAYLOAD_GUI_MISSING=$BridgeXExe" }
if (-not (Test-Path -LiteralPath $BridgeXCli)) { throw "MSI_PAYLOAD_CLI_MISSING=$BridgeXCli" }

# Use native Windows Installer packaging instead of a self-extracting executable.
# The MSI is deliberately per-user and limited-privilege:
# - install root is %LOCALAPPDATA%\Programs\TNSuite\BridgeX;
# - no HKLM writes;
# - no process termination;
# - no PowerShell/custom-action execution;
# - no embedded bootstrapper EXE / SFX overlay.
& $Heat dir $PayloadDir -nologo -cg BridgeXPayload -dr INSTALLFOLDER -srd -sreg -sfrag -ag -var var.PayloadDir -out $PayloadWxs
if ($LASTEXITCODE -ne 0) { throw "WIX_HEAT_FAILED=$LASTEXITCODE" }

$ProductXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*"
           Name="$ProductDisplayName"
           Language="1033"
           Version="$ProductVersion"
           Manufacturer="$Manufacturer"
           UpgradeCode="{54CAEDFB-8DD4-4187-B98A-7399F94765D7}">
    <Package InstallerVersion="500"
             Compressed="yes"
             InstallScope="perUser"
             InstallPrivileges="limited"
             Description="TNSuite BridgeX Windows installer" />

    <MajorUpgrade DowngradeErrorMessage="A newer version of TNSuite BridgeX is already installed." />
    <MediaTemplate EmbedCab="yes" CompressionLevel="medium" />

    <Property Id="ARPNOREPAIR" Value="1" />
    <Property Id="ARPHELPLINK" Value="https://github.com/kyousuke33/TNSuite-BridgeX" />
    <Property Id="ARPCONTACT" Value="TNSuite" />

    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="LocalAppDataFolder">
        <Directory Id="LocalProgramsFolder" Name="Programs">
          <Directory Id="TNSuiteFolder" Name="TNSuite">
            <Directory Id="INSTALLFOLDER" Name="BridgeX" />
          </Directory>
        </Directory>
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="BridgeXProgramsFolder" Name="TNSuite BridgeX" />
      </Directory>
    </Directory>

    <DirectoryRef Id="BridgeXProgramsFolder">
      <Component Id="BridgeXStartMenuShortcuts" Guid="*">
        <Shortcut Id="BridgeXGuiShortcut"
                  Name="TNSuite BridgeX"
                  Description="TNSuite BridgeX secure transfer client"
                  Target="[INSTALLFOLDER]bin\BridgeX.exe"
                  WorkingDirectory="INSTALLFOLDER" />
        <Shortcut Id="BridgeXCliShortcut"
                  Name="BridgeX CLI"
                  Description="TNSuite BridgeX command line client"
                  Target="[INSTALLFOLDER]bin\BridgeX-CLI.exe"
                  WorkingDirectory="INSTALLFOLDER" />
        <RemoveFolder Id="RemoveBridgeXProgramsFolder" On="uninstall" />
        <RegistryValue Root="HKCU"
                       Key="Software\TNSuite\BridgeX"
                       Name="MsiInstalled"
                       Type="integer"
                       Value="1"
                       KeyPath="yes" />
      </Component>
    </DirectoryRef>

    <Feature Id="Complete" Title="TNSuite BridgeX" Level="1" Display="expand">
      <ComponentGroupRef Id="BridgeXPayload" />
      <ComponentRef Id="BridgeXStartMenuShortcuts" />
    </Feature>
  </Product>
</Wix>
"@
[System.IO.File]::WriteAllText($ProductWxs, $ProductXml, [System.Text.UTF8Encoding]::new($false))

$productText = [System.IO.File]::ReadAllText($ProductWxs)
$forbidden = @(
    'CustomAction',
    'InstallScope="perMachine"',
    'InstallPrivileges="elevated"',
    'Root="HKLM"',
    'powershell',
    'cmd.exe',
    'Exec',
    'TerminateProcess'
)
foreach ($needle in $forbidden) {
    if ($productText.IndexOf($needle, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
        throw "MSI_SECURITY_PROFILE_FORBIDDEN=$needle"
    }
}
if ($productText -notmatch 'InstallScope="perUser"') { throw 'MSI_PER_USER_SCOPE_MISSING' }
if ($productText -notmatch 'InstallPrivileges="limited"') { throw 'MSI_LIMITED_PRIVILEGES_MISSING' }
if ($productText -notmatch 'Root="HKCU"') { throw 'MSI_HKCU_KEYPATH_MISSING' }
Write-Host 'MSI_SECURITY_PROFILE_QA=PASS'

& $Candle -nologo -arch x64 "-dPayloadDir=$PayloadDir" -out $ProductObj $ProductWxs
if ($LASTEXITCODE -ne 0) { throw "WIX_CANDLE_PRODUCT_FAILED=$LASTEXITCODE" }
& $Candle -nologo -arch x64 "-dPayloadDir=$PayloadDir" -out $PayloadObj $PayloadWxs
if ($LASTEXITCODE -ne 0) { throw "WIX_CANDLE_PAYLOAD_FAILED=$LASTEXITCODE" }
& $Light -nologo -out $OutputMsi $ProductObj $PayloadObj
if ($LASTEXITCODE -ne 0) { throw "WIX_LIGHT_FAILED=$LASTEXITCODE" }

if (-not (Test-Path -LiteralPath $OutputMsi) -or (Get-Item -LiteralPath $OutputMsi).Length -le 0) {
    throw "MSI_OUTPUT_MISSING=$OutputMsi"
}

$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $OutputMsi).Hash.ToLowerInvariant()
$signature = Get-AuthenticodeSignature -LiteralPath $OutputMsi
Write-Host "MSI_OUTPUT=$OutputMsi"
Write-Host "MSI_SHA256=$hash"
Write-Host "MSI_AUTHENTICODE_STATUS=$($signature.Status)"
Write-Host 'MSI_PACKAGING_QA=PASS'
