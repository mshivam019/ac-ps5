param(
    [Parameter(Mandatory=$true)][string]$Src,
    [Parameter(Mandatory=$true)][string]$Console,
    [int]$FtpPort = 2121,
    [string]$Data = ''
)
$ErrorActionPreference = 'Stop'
$arguments = @("$PSScriptRoot/install.py", '--src', $Src, '--console', $Console, '--ftp-port', $FtpPort)
if ($Data) { $arguments += @('--data', $Data) }
& python @arguments
if ($LASTEXITCODE -ne 0) { throw 'Native PS5 title upload failed' }
