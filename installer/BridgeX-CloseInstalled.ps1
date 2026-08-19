param(
    [Parameter(Mandatory = $true)]
    [string]$TargetExecutable
)

$ErrorActionPreference = 'Stop'
try {
    $target = [System.IO.Path]::GetFullPath($TargetExecutable)
}
catch {
    exit 2
}

$matched = @()
Get-Process -Name 'BridgeX' -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $path = $_.Path
        if ($path -and ([System.IO.Path]::GetFullPath($path) -ieq $target)) {
            $matched += $_
        }
    }
    catch {
        # Protected/inaccessible process: it cannot be proven to belong to this
        # install path, so do not terminate it.
    }
}

foreach ($process in $matched) {
    try {
        [void]$process.CloseMainWindow()
        if (-not $process.WaitForExit(3000)) {
            $process.Kill()
            [void]$process.WaitForExit(2000)
        }
    }
    catch {
        # RMDir /REBOOTOK remains the final fallback for files still locked by
        # a process Windows refused to close.
    }
}
exit 0
