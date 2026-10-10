# dump_usb.ps1 - read a USB stick sector by sector into an image file (disk.img).
# The stick is opened read-only; nothing is ever written to it.
#
#   powershell -ExecutionPolicy Bypass -File tools\dump_usb.ps1                 list the USB disks
#   powershell -ExecutionPolicy Bypass -File tools\dump_usb.ps1 -Disk 2         whole stick -> disk.img
#   powershell -ExecutionPolicy Bypass -File tools\dump_usb.ps1 -Disk 2 -SizeMB 512
#
# Needs an Administrator PowerShell (raw disk access).
param(
    [int]$Disk = -1,
    [string]$Out = (Join-Path (Split-Path $PSScriptRoot -Parent) 'disk.img'),
    [int]$SizeMB = 0                      # 0 = the whole stick
)

$usb = @(Get-Disk | Where-Object { $_.BusType -eq 'USB' })
if ($Disk -lt 0) {
    if ($usb.Count -eq 0) { Write-Host 'No USB disk is plugged in.'; exit 1 }
    $usb | Select-Object Number, FriendlyName, @{n='SizeGB';e={[math]::Round($_.Size/1GB,2)}}, PartitionStyle | Format-Table -AutoSize
    Write-Host 'Run again with  -Disk <Number>  to make the image.'
    exit 0
}

$d = $usb | Where-Object { $_.Number -eq $Disk }
if (-not $d) { Write-Host "Disk $Disk is not a USB disk - refusing to read it."; exit 1 }

$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { Write-Host 'Start PowerShell as Administrator and run this again.'; exit 1 }

Add-Type -Namespace Ninux -Name Raw -MemberDefinition @'
[DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
public static extern Microsoft.Win32.SafeHandles.SafeFileHandle CreateFile(
    string name, uint access, uint share, IntPtr sec, uint disposition, uint flags, IntPtr template);
'@

$GENERIC_READ = 0x80000000L
$SHARE_RW     = 3
$OPEN_EXISTING = 3
$h = [Ninux.Raw]::CreateFile("\\.\PhysicalDrive$Disk", $GENERIC_READ, $SHARE_RW, [IntPtr]::Zero, $OPEN_EXISTING, 0, [IntPtr]::Zero)
if ($h.IsInvalid) {
    Write-Host ("Cannot open the stick (error {0})." -f [Runtime.InteropServices.Marshal]::GetLastWin32Error())
    exit 1
}

$total = [int64]$d.Size
if ($SizeMB -gt 0) { $total = [Math]::Min($total, [int64]$SizeMB * 1MB) }

$chunk = 1MB                                   # a multiple of the sector size, as raw reads require
$buf = New-Object byte[] $chunk
$src = New-Object IO.FileStream($h, [IO.FileAccess]::Read, $chunk, $false)
$dst = [IO.File]::Create($Out)
$done = [int64]0
try {
    while ($done -lt $total) {
        $want = [int][Math]::Min([int64]$chunk, $total - $done)
        $got = $src.Read($buf, 0, $want)
        if ($got -le 0) { break }
        $dst.Write($buf, 0, $got)
        $done += $got
        if (($done % 64MB) -eq 0) { Write-Host ("{0} / {1} MB" -f [int]($done/1MB), [int]($total/1MB)) }
    }
} finally {
    $dst.Close(); $src.Close()
}

Write-Host ("Done: {0} MB from '{1}' -> {2}" -f [int]($done/1MB), $d.FriendlyName, $Out)
if ($done -lt $total) { Write-Host 'WARNING: the read stopped early - the image is incomplete.' }
