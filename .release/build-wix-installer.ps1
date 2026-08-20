[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$PortableZip,
    [Parameter(Mandatory = $true)][string]$OutputDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$PortableZip = (Resolve-Path -LiteralPath $PortableZip).Path
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null

$BuildName = 'TNSuiteBridgeX_260820_v0.5-Build12-Hotfix18-WiX'
$ProductVersion = '0.5.12.18'
$ProductUpgradeCode = '{B8BF51DD-E1B4-4A6E-B543-1661EF5EA8EA}'
$BundleUpgradeCode = '{7E03045D-320D-4AB5-8DD0-02BFF00F058B}'
$ExpectedBridgeXHash = '9d528d211950f3df0609c05a8c1e01725927ae76b70bed2ad0fe9b97c53504d6'
$RequiredDlls = @(
    'bin\libfzclient-commonui-private-3-70-6.dll',
    'bin\libfzclient-private-3-70-6.dll',
    'bin\libfilezilla-58.dll',
    'bin\libfzssh-13.0.0.dll'
)

function XmlEscape([string]$value) {
    return [System.Security.SecurityElement]::Escape($value)
}

function StableId([string]$prefix, [string]$value) {
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($value.ToLowerInvariant())
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { $hash = $sha.ComputeHash($bytes) } finally { $sha.Dispose() }
    $hex = -join ($hash[0..11] | ForEach-Object { $_.ToString('x2') })
    return "${prefix}_${hex}"
}

Write-Host 'WIX_INSTALLER_BUILD=START'
Write-Host "PORTABLE_SOURCE=$PortableZip"

$TempRoot = Join-Path $env:RUNNER_TEMP "bridgex-wix-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT"
if (Test-Path -LiteralPath $TempRoot) { Remove-Item -LiteralPath $TempRoot -Recurse -Force }
$PayloadRoot = Join-Path $TempRoot 'payload'
$WixRoot = Join-Path $TempRoot 'wix'
New-Item -ItemType Directory -Force -Path $PayloadRoot, $WixRoot | Out-Null
Expand-Archive -LiteralPath $PortableZip -DestinationPath $PayloadRoot -Force

$BridgeXExe = Join-Path $PayloadRoot 'bin\BridgeX.exe'
if (-not (Test-Path -LiteralPath $BridgeXExe)) { throw 'BRIDGEX_EXE_MISSING' }
$BridgeXHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $BridgeXExe).Hash.ToLowerInvariant()
if ($BridgeXHash -ne $ExpectedBridgeXHash) {
    throw "BRIDGEX_CANONICAL_HASH=FAIL expected=$ExpectedBridgeXHash actual=$BridgeXHash"
}
Write-Host "BRIDGEX_CANONICAL_HASH=PASS sha256=$BridgeXHash"
foreach ($relative in $RequiredDlls) {
    $full = Join-Path $PayloadRoot $relative
    if (-not (Test-Path -LiteralPath $full)) { throw "RUNTIME_DLL=FAIL path=$relative" }
    Write-Host "RUNTIME_DLL=PASS path=$relative"
}

$files = @(Get-ChildItem -LiteralPath $PayloadRoot -File -Recurse | Sort-Object FullName)
if ($files.Count -lt 10) { throw "PAYLOAD_FILE_COUNT_UNEXPECTED=$($files.Count)" }

# Build a directory map. The MSI deliberately installs into the existing
# Program Files\TNSuite\BridgeX tree without deleting unknown content first.
# Windows Installer owns only files/components in this package. This allows
# safe migration from prior NSIS/native candidates without a proprietary
# marker gate and without recursive deletion of an unverified directory.
$dirPaths = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
foreach ($file in $files) {
    $relative = [System.IO.Path]::GetRelativePath($PayloadRoot, $file.FullName).Replace('/', '\')
    $parent = [System.IO.Path]::GetDirectoryName($relative)
    while ($parent) {
        [void]$dirPaths.Add($parent)
        $parent = [System.IO.Path]::GetDirectoryName($parent)
    }
}

$children = @{}
foreach ($path in $dirPaths) {
    $parent = [System.IO.Path]::GetDirectoryName($path)
    if ($null -eq $parent) { $parent = '' }
    if (-not $children.ContainsKey($parent)) { $children[$parent] = New-Object System.Collections.Generic.List[string] }
    $children[$parent].Add($path)
}
foreach ($key in @($children.Keys)) { $children[$key].Sort([System.StringComparer]::OrdinalIgnoreCase) }

function EmitDirectoryTree([System.Text.StringBuilder]$sb, [string]$parentPath, [int]$indent) {
    if (-not $children.ContainsKey($parentPath)) { return }
    foreach ($path in $children[$parentPath]) {
        $name = [System.IO.Path]::GetFileName($path)
        $id = StableId 'DIR' $path
        [void]$sb.AppendLine((' ' * $indent) + '<Directory Id="' + $id + '" Name="' + (XmlEscape $name) + '">')
        EmitDirectoryTree $sb $path ($indent + 2)
        [void]$sb.AppendLine((' ' * $indent) + '</Directory>')
    }
}

$product = [System.Text.StringBuilder]::new()
[void]$product.AppendLine('<?xml version="1.0" encoding="utf-8"?>')
[void]$product.AppendLine('<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">')
[void]$product.AppendLine('  <Package Name="TNSuite BridgeX" Manufacturer="TNSuite" Version="' + $ProductVersion + '" UpgradeCode="' + $ProductUpgradeCode + '" Scope="perMachine">')
[void]$product.AppendLine('    <MajorUpgrade DowngradeErrorMessage="A newer version of TNSuite BridgeX is already installed." />')
[void]$product.AppendLine('    <MediaTemplate EmbedCab="yes" CompressionLevel="high" />')
[void]$product.AppendLine('    <Feature Id="MainFeature" Title="TNSuite BridgeX" Level="1">')
[void]$product.AppendLine('      <ComponentGroupRef Id="PayloadComponents" />')
[void]$product.AppendLine('      <ComponentRef Id="StartMenuShortcutComponent" />')
[void]$product.AppendLine('    </Feature>')
[void]$product.AppendLine('  </Package>')
[void]$product.AppendLine('  <Fragment>')
[void]$product.AppendLine('    <StandardDirectory Id="ProgramFiles64Folder">')
[void]$product.AppendLine('      <Directory Id="TNSuiteFolder" Name="TNSuite">')
[void]$product.AppendLine('        <Directory Id="INSTALLFOLDER" Name="BridgeX">')
EmitDirectoryTree $product '' 10
[void]$product.AppendLine('        </Directory>')
[void]$product.AppendLine('      </Directory>')
[void]$product.AppendLine('    </StandardDirectory>')
[void]$product.AppendLine('    <StandardDirectory Id="ProgramMenuFolder">')
[void]$product.AppendLine('      <Directory Id="ApplicationProgramsFolder" Name="TNSuite BridgeX" />')
[void]$product.AppendLine('    </StandardDirectory>')
[void]$product.AppendLine('  </Fragment>')
[void]$product.AppendLine('  <Fragment>')
[void]$product.AppendLine('    <ComponentGroup Id="PayloadComponents">')
foreach ($file in $files) {
    $relative = [System.IO.Path]::GetRelativePath($PayloadRoot, $file.FullName).Replace('/', '\')
    $parent = [System.IO.Path]::GetDirectoryName($relative)
    $directoryId = if ($parent) { StableId 'DIR' $parent } else { 'INSTALLFOLDER' }
    $componentId = StableId 'CMP' $relative
    $fileId = StableId 'FIL' $relative
    $source = XmlEscape $file.FullName
    [void]$product.AppendLine('      <Component Id="' + $componentId + '" Directory="' + $directoryId + '" Guid="*">')
    [void]$product.AppendLine('        <File Id="' + $fileId + '" Source="' + $source + '" KeyPath="yes" />')
    [void]$product.AppendLine('      </Component>')
}
[void]$product.AppendLine('    </ComponentGroup>')
[void]$product.AppendLine('  </Fragment>')
[void]$product.AppendLine('  <Fragment>')
[void]$product.AppendLine('    <Component Id="StartMenuShortcutComponent" Directory="ApplicationProgramsFolder" Guid="{33CC5719-43A4-4D98-B676-8A7358E79F73}">')
[void]$product.AppendLine('      <Shortcut Id="StartMenuShortcut" Name="TNSuite BridgeX" Description="TNSuite BridgeX" Target="[INSTALLFOLDER]bin\BridgeX.exe" WorkingDirectory="' + (StableId 'DIR' 'bin') + '" />')
[void]$product.AppendLine('      <RemoveFolder Id="ApplicationProgramsFolderCleanup" On="uninstall" />')
[void]$product.AppendLine('      <RegistryValue Root="HKLM" Key="Software\TNSuite\BridgeX" Name="InstallerGeneration" Type="string" Value="WiX-' + $ProductVersion + '" KeyPath="yes" />')
[void]$product.AppendLine('    </Component>')
[void]$product.AppendLine('  </Fragment>')
[void]$product.AppendLine('</Wix>')

$ProductWxs = Join-Path $WixRoot 'BridgeX.Product.wxs'
[System.IO.File]::WriteAllText($ProductWxs, $product.ToString(), [System.Text.UTF8Encoding]::new($false))

$MsiPath = Join-Path $OutputDirectory "$BuildName.msi"
& wix build -arch x64 -o $MsiPath $ProductWxs
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $MsiPath)) { throw "WIX_MSI_BUILD_FAILED=$LASTEXITCODE" }
Write-Host 'WIX_MSI_BUILD=PASS'

$bundle = @"
<?xml version="1.0" encoding="utf-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs" xmlns:bal="http://wixtoolset.org/schemas/v4/wxs/bal">
  <Bundle Name="TNSuite BridgeX" Manufacturer="TNSuite" Version="$ProductVersion" UpgradeCode="$BundleUpgradeCode">
    <BootstrapperApplication>
      <bal:WixStandardBootstrapperApplication Theme="hyperlinkLicense" LicenseUrl="" SuppressOptionsUI="yes" />
    </BootstrapperApplication>
    <Chain>
      <MsiPackage SourceFile="$([System.Security.SecurityElement]::Escape($MsiPath))" Compressed="yes" />
    </Chain>
  </Bundle>
</Wix>
"@
$BundleWxs = Join-Path $WixRoot 'BridgeX.Bundle.wxs'
[System.IO.File]::WriteAllText($BundleWxs, $bundle, [System.Text.UTF8Encoding]::new($false))

$ExePath = Join-Path $OutputDirectory "$BuildName-Setup.exe"
& wix build -arch x64 -ext WixToolset.Bal.wixext -o $ExePath $BundleWxs
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $ExePath)) { throw "WIX_BUNDLE_BUILD_FAILED=$LASTEXITCODE" }
Write-Host 'WIX_BUNDLE_BUILD=PASS'

$msiHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $MsiPath).Hash.ToLowerInvariant()
$exeHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $ExePath).Hash.ToLowerInvariant()
Write-Host "WIX_MSI_SHA256=$msiHash"
Write-Host "WIX_SETUP_SHA256=$exeHash"
Write-Host "WIX_PAYLOAD_FILES=$($files.Count)"
Write-Host 'LEGACY_INSTALL_MARKER_GATE=REMOVED'
Write-Host 'RECURSIVE_UNVERIFIED_INSTALL_DIR_DELETE=NONE'
Write-Host 'INSTALLER_ENGINE=WIX_BURN_MSI'
Write-Host 'CUSTOM_SELF_EXTRACTOR=NONE'
Write-Host 'INSTALLER_PACKER=NONE'
Write-Host 'INSTALLER_OBFUSCATION=NONE'
Write-Host 'INSTALLER_POWERSHELL_RUNTIME=NONE'
Write-Host 'INSTALLER_PROCESS_KILL=NONE'
Write-Host 'WIX_INSTALLER_BUILD=PASS'
