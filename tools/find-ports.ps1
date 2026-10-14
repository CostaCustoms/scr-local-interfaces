<#
.SYNOPSIS
  Lists StarCraft: Remastered's loopback (127.0.0.1) listening ports and tells the plain-HTTP port from the
  TLS port. Read-only.

.DESCRIPTION
  For every running StarCraft.exe, finds its TCP listeners on 127.0.0.1. For each port it sends
  "GET / HTTP/1.0" (the client answers 404 on its plain-HTTP port); if the port does not answer plain HTTP,
  it tries a TLS handshake (certificate check disabled) and prints the certificate subject and expiry.
  Nothing else is sent. No game memory is read and no input is sent to the game.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\find-ports.ps1
#>
[CmdletBinding()]
param([int]$TimeoutMs = 2000)

$ErrorActionPreference = 'Stop'

function Connect-Tcp([int]$Port, [int]$TimeoutMs) {
  $c = New-Object Net.Sockets.TcpClient
  $ar = $c.BeginConnect('127.0.0.1', $Port, $null, $null)
  if (-not $ar.AsyncWaitHandle.WaitOne($TimeoutMs)) { $c.Close(); return $null }
  try { $c.EndConnect($ar) } catch { $c.Close(); return $null }
  $c.ReceiveTimeout = $TimeoutMs; $c.SendTimeout = $TimeoutMs
  return $c
}

# First line of the answer to "GET / HTTP/1.0", '' if the port said nothing, $null if it could not be reached.
function Get-PlainHttpStatus([int]$Port, [int]$TimeoutMs) {
  $c = Connect-Tcp $Port $TimeoutMs
  if (-not $c) { return $null }
  try {
    $s = $c.GetStream()
    $req = [Text.Encoding]::ASCII.GetBytes("GET / HTTP/1.0`r`nHost: 127.0.0.1`r`n`r`n")
    $s.Write($req, 0, $req.Length)
    $buf = New-Object byte[] 512
    $n = 0
    try { $n = $s.Read($buf, 0, $buf.Length) } catch { $n = 0 }
    if ($n -le 0) { return '' }
    return (([Text.Encoding]::ASCII.GetString($buf, 0, $n)) -split "`r?`n")[0]
  } catch { return '' } finally { $c.Close() }
}

# Certificate subject + expiry if the port speaks TLS, else $null.
function Get-TlsCertificate([int]$Port, [int]$TimeoutMs) {
  $c = Connect-Tcp $Port $TimeoutMs
  if (-not $c) { return $null }
  try {
    $accept = [Net.Security.RemoteCertificateValidationCallback] { param($sender, $cert, $chain, $errors) $true }
    $ssl = New-Object Net.Security.SslStream($c.GetStream(), $false, $accept)
    $ssl.AuthenticateAsClient('loopback.classic.blizzard.com')
    $cert = New-Object Security.Cryptography.X509Certificates.X509Certificate2($ssl.RemoteCertificate)
    $ssl.Dispose()
    return "$($cert.Subject), expires $($cert.NotAfter.ToString('yyyy-MM-dd'))"
  } catch { return $null } finally { $c.Close() }
}

$procs = @(Get-Process -Name StarCraft -ErrorAction SilentlyContinue)
if (-not $procs.Count) { Write-Error 'StarCraft.exe is not running.'; exit 1 }

$rows = foreach ($p in $procs) {
  $ports = @(Get-NetTCPConnection -OwningProcess $p.Id -State Listen -ErrorAction SilentlyContinue |
    Where-Object LocalAddress -eq '127.0.0.1' | Sort-Object LocalPort -Unique | ForEach-Object LocalPort)
  if (-not $ports.Count) {
    [pscustomobject]@{ Pid = $p.Id; Port = $null; Kind = 'none'; Detail = 'no 127.0.0.1 listener (not logged in yet?)' }
    continue
  }
  foreach ($port in $ports) {
    $status = Get-PlainHttpStatus $port $TimeoutMs
    if ($status -like 'HTTP/*') {
      [pscustomobject]@{ Pid = $p.Id; Port = $port; Kind = 'HTTP'; Detail = "GET / -> $status; panel sockets: ws://127.0.0.1:$port/panel/<Panel>/<id>; REST: http://127.0.0.1:$port/web-api/..." }
    } else {
      $tls = Get-TlsCertificate $port $TimeoutMs
      if ($tls) { [pscustomobject]@{ Pid = $p.Id; Port = $port; Kind = 'TLS'; Detail = $tls } }
      else { [pscustomobject]@{ Pid = $p.Id; Port = $port; Kind = 'unknown'; Detail = 'no plain-HTTP answer and no TLS handshake' } }
    }
  }
}
$rows | Format-Table -AutoSize -Wrap
