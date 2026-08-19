[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$roots = @(
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild01'),
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild02'),
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild03'),
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild04'),
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild05'),
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild06'),
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild07'),
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild09'),
    (Join-Path $env:LOCALAPPDATA 'FileZillaDarkBuild12'),
    (Join-Path $env:LOCALAPPDATA 'TNSuiteBridgeXBuild11Hotfix1'),
    (Join-Path $env:LOCALAPPDATA 'TNSuiteBridgeXBuild12')
) | Select-Object -Unique

Write-Host 'TNSuite BridgeX - isolated build environment cleanup' -ForegroundColor Cyan
Write-Host 'The portable TNSuite BridgeX ZIP and your SSH/FileZilla settings are NOT touched.' -ForegroundColor DarkGray

# Stop only processes whose executable actually lives inside one of our private build roots.
Get-Process -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $path = $_.Path
        if ($path) {
            foreach ($root in $roots) {
                if ($path.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
                    Write-Host "Stopping isolated build process: $($_.ProcessName) [$path]"
                    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
                    break
                }
            }
        }
    } catch {}
}
Start-Sleep -Milliseconds 500

# Remove Start Menu shortcuts only when their target points into our isolated roots.
$startMenu = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\MSYS2'
if (Test-Path $startMenu) {
    $shell = New-Object -ComObject WScript.Shell
    Get-ChildItem -LiteralPath $startMenu -Filter '*.lnk' -File -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $target = $shell.CreateShortcut($_.FullName).TargetPath
            foreach ($root in $roots) {
                if ($target -and $target.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
                    Write-Host "Removing isolated MSYS2 shortcut: $($_.Name)"
                    Remove-Item -LiteralPath $_.FullName -Force
                    break
                }
            }
        } catch {}
    }
    if (-not (Get-ChildItem -LiteralPath $startMenu -Force -ErrorAction SilentlyContinue)) {
        Remove-Item -LiteralPath $startMenu -Force -ErrorAction SilentlyContinue
    }
}

# Remove uninstall registrations only if the uninstall command itself points to our isolated root.
$uninstallBases = @(
    'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall',
    'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall',
    'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'
)
foreach ($base in $uninstallBases) {
    if (-not (Test-Path $base)) { continue }
    Get-ChildItem $base -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $item = Get-ItemProperty $_.PSPath -ErrorAction Stop
            $u = [string]$item.UninstallString
            foreach ($root in $roots) {
                if ($u -and $u.IndexOf($root, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
                    Write-Host "Removing isolated installer registration: $($item.DisplayName)"
                    Remove-Item $_.PSPath -Recurse -Force -ErrorAction SilentlyContinue
                    break
                }
            }
        } catch {}
    }
}

foreach ($root in $roots) {
    if (Test-Path $root) {
        Write-Host "Removing: $root"
        Remove-Item -LiteralPath $root -Recurse -Force
    }
}

Write-Host ''
Write-Host 'CLEANUP=PASS' -ForegroundColor Green
Write-Host 'Removed isolated MSYS2/compiler/source/object/package-cache state created by this build kit.' -ForegroundColor Green
Write-Host 'Not removed: your build-kit folder, dist artifact, %APPDATA%\FileZilla, SSH keys, or generic shared Windows/Qt caches.' -ForegroundColor DarkGray
