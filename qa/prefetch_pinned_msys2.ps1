[CmdletBinding()]
param(
 [string]$InstallerRoot = (Join-Path $env:LOCALAPPDATA 'TNSuiteBridgeXBuild12Hotfix1')
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$ProgressPreference='SilentlyContinue'

# Pinned historical build-input. Never silently upgrade the source toolchain.
$name = 'msys2-x86_64-20260611.exe'
$sha = '3150D7D9AA5DEDD900A7F52300D4D918271E3A8FC47DE94848818FD5A430E6B0'
$installed = Join-Path $InstallerRoot 'msys64\usr\bin\bash.exe'
$dest = Join-Path $InstallerRoot $name
if (Test-Path -LiteralPath $installed -PathType Leaf) {
 Write-Host 'MSYS2_BOOTSTRAP=SKIPPED_EXISTING_ISOLATED_ENV'
 return
}
New-Item -ItemType Directory -Path $InstallerRoot -Force | Out-Null
if (Test-Path -LiteralPath $dest -PathType Leaf) {
 $existing = (Get-FileHash -LiteralPath $dest -Algorithm SHA256).Hash.ToUpperInvariant()
 if ($existing -eq $sha) { Write-Host 'MSYS2_BOOTSTRAP_SHA256=PASS_CACHED'; return }
 Remove-Item -LiteralPath $dest -Force
}
$urls = @(
 'https://repo.msys2.org/distrib/x86_64/msys2-x86_64-20260611.exe',
 'https://github.com/msys2/msys2-installer/releases/download/2026-06-11/msys2-x86_64-20260611.exe'
)
foreach ($url in $urls) {
 for ($n=1;$n -le 3;$n++) {
  $partial = $dest+'.partial'
  try {
   if (Test-Path $partial) { Remove-Item $partial -Force }
   & curl.exe --fail --location --silent --show-error --retry 2 --retry-all-errors --connect-timeout 30 --max-time 300 --output $partial $url
   if ($LASTEXITCODE -ne 0) { throw "HTTP_FETCH_EXIT=$LASTEXITCODE" }
   if (-not (Test-Path -LiteralPath $partial -PathType Leaf)) { throw 'DOWNLOAD_MISSING' }
   $actual = (Get-FileHash -LiteralPath $partial -Algorithm SHA256).Hash.ToUpperInvariant()
   if ($actual -ne $sha) { throw "PINNED_SHA256_MISMATCH expected=$sha actual=$actual" }
   Move-Item -LiteralPath $partial -Destination $dest -Force
   Write-Host 'MSYS2_BOOTSTRAP_SHA256=PASS'
   Write-Host "MSYS2_BOOTSTRAP_SOURCE=$url"
   Write-Host 'MSYS2_BOOTSTRAP_VERSION=2026-06-11'
   return
  }
  catch {
   Write-Host "MSYS2_BOOTSTRAP_RETRY attempt=$n reason=$($_.Exception.Message)"
   if (Test-Path $partial) { Remove-Item $partial -Force }
   if($n -lt 3) { Start-Sleep -Seconds (3*$n) }
  }
 }
}
throw 'MSYS2_BOOTSTRAP=FAIL_ALL_OFFICIAL_URLS_OR_SHA256'
