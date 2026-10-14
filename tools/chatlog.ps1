<#
.SYNOPSIS
  Prints chat and info lines that StarCraft: Remastered pushes to a UI panel socket. Read-only: sends nothing.

.DESCRIPTION
  Live mode: connects to ws://127.0.0.1:<port>/panel/<Panel>/<id> and prints, as they arrive:
    * OnMessage            chat / info lines broadcast by the game (lobby chat, joins / leaves, friend
                           notices, player stats). Seen on GameLobbyPanel sockets (2026-10-04).
    * SendChatMessage      relayed requests from this client's own chat pages (what you typed), when the
                           socket server relays them (seen from GameLobbyChatPanel, 2026-10-04).
    * LocalStorageSetValue key "chatLogs" - the channel page's saved chat log, IF the server relays it to
                           outside sockets (UNCONFIRMED); new entries are printed.
  Offline mode (-FromFile): the same, from a saved capture (one JSON message per line).

  This script never sends a message on the socket (not even the page's own GetStrings). No game memory is
  read and no input is sent to the game. -Guid (the panel id) is per session and per screen; this repository
  does not provide a way to discover it (see docs\04-ui-panel-sockets.md). While an outside socket is
  attached, the on-screen panel may stop redrawing until the screen is reopened.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\chatlog.ps1 -FromFile samples\lobby-socket_20261004.scrubbed.jsonl
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\chatlog.ps1 -Panel GameLobbyPanel -Guid 12345 -Seconds 120
#>
[CmdletBinding()]
param(
  [string]$Guid,
  [string]$Panel = 'ChatPanelHDAd',
  [int]$Port,
  [int]$Seconds = 0,          # 0 = until Ctrl+C
  [string]$FromFile,
  [string]$SaveTo,
  [switch]$ShowAll            # also print the endpoint name of every other message
)

$ErrorActionPreference = 'Stop'

function Get-PlainHttpPort {
  $procs = @(Get-Process -Name StarCraft -ErrorAction SilentlyContinue)
  if ($procs.Count -ne 1) { throw "Found $($procs.Count) StarCraft processes; pass -Port (see tools\find-ports.ps1)." }
  $ports = @(Get-NetTCPConnection -OwningProcess $procs[0].Id -State Listen -ErrorAction SilentlyContinue |
    Where-Object LocalAddress -eq '127.0.0.1' | Sort-Object LocalPort -Unique | ForEach-Object LocalPort)
  foreach ($p in $ports) {
    $c = New-Object Net.Sockets.TcpClient
    try {
      $ar = $c.BeginConnect('127.0.0.1', $p, $null, $null)
      if (-not $ar.AsyncWaitHandle.WaitOne(2000)) { continue }
      $c.EndConnect($ar); $c.ReceiveTimeout = 2000
      $s = $c.GetStream(); $req = [Text.Encoding]::ASCII.GetBytes("GET / HTTP/1.0`r`n`r`n"); $s.Write($req, 0, $req.Length)
      $buf = New-Object byte[] 64; $n = 0; try { $n = $s.Read($buf, 0, 64) } catch {}
      if ($n -gt 0 -and [Text.Encoding]::ASCII.GetString($buf, 0, $n).StartsWith('HTTP/')) { return $p }
    } catch {} finally { $c.Close() }
  }
  throw 'No plain-HTTP listener found for StarCraft (is it running and logged in?).'
}

function Clean([string]$s) { if ($null -eq $s) { return '' }; return ($s -replace '[\x00-\x1F]', ' ').Trim() }
function Stamp { (Get-Date).ToString('HH:mm:ss') }

$script:chatLogSeen = -1   # entries already printed from a relayed "chatLogs" save

function Show-Message([string]$text) {
  try { $m = $text | ConvertFrom-Json } catch { return }
  if (-not $m.data) { return }
  $ep = [string]$m.data.endpoint; $d = $m.data.data
  switch ($ep) {
    'OnMessage' {
      $who = ''
      if ($d.sender -and $d.sender.name) { $who = "$(Clean $d.sender.name): " }
      Write-Output ("[{0}] {1,-16} {2,-12} {3}{4}" -f (Stamp), (Clean $d.channel), (Clean $d.type), $who, (Clean $d.content))
    }
    'SendChatMessage' {
      Write-Output ("[{0}] {1,-16} {2,-12} (sent by this client via {3}) {4}" -f (Stamp), (Clean $d.target), 'outgoing', (Clean $m.originRoutePath), (Clean $d.message))
    }
    'LocalStorageSetValue' {
      if ($d.key -ne 'chatLogs') { if ($ShowAll) { Write-Output "[$(Stamp)] LocalStorageSetValue key=$($d.key)" }; return }
      try { $log = @($d.value | ConvertFrom-Json) } catch { return }
      $start = 0
      if ($script:chatLogSeen -ge 0 -and $log.Count -ge $script:chatLogSeen) { $start = $script:chatLogSeen }
      for ($i = $start; $i -lt $log.Count; $i++) {
        $e = $log[$i]; $who = ''
        if ($e.sender -and $e.sender.name) { $who = "$(Clean $e.sender.name): " }
        $ch = if ($e.channelName) { $e.channelName } else { $e.channel }
        Write-Output ("[{0}] {1,-16} {2,-12} {3}{4}" -f (Stamp), (Clean $ch), (Clean $e.type), $who, (Clean $e.content))
      }
      $script:chatLogSeen = $log.Count
    }
    default { if ($ShowAll) { Write-Output "[$(Stamp)] ($ep)" } }
  }
}

if ($FromFile) {
  foreach ($line in [IO.File]::ReadAllLines((Resolve-Path $FromFile).Path, [Text.Encoding]::UTF8)) {
    if ($line.Trim()) { Show-Message $line }
  }
  return
}

if (-not $Guid) { throw '-Guid is required for live mode (or use -FromFile).' }
if (-not $Port) { $Port = Get-PlainHttpPort }
$uri = [Uri]"ws://127.0.0.1:$Port/panel/$Panel/$Guid"
$ws = New-Object Net.WebSockets.ClientWebSocket
try { [void]$ws.ConnectAsync($uri, [Threading.CancellationToken]::None).Wait(3000) } catch {}
if ($ws.State -ne 'Open') { $ws.Dispose(); throw "The socket $uri was refused or timed out: the screen is not open, or the id is wrong / stale." }
Write-Host "listening on $uri (nothing is sent; Ctrl+C to stop)"

$save = $null
if ($SaveTo) { $save = New-Object IO.StreamWriter($SaveTo, $false, (New-Object Text.UTF8Encoding($false))) }
$buf = New-Object byte[] 65536
$acc = New-Object IO.MemoryStream
$deadline = if ($Seconds -gt 0) { (Get-Date).AddSeconds($Seconds) } else { [datetime]::MaxValue }
$pending = $null
try {
  while ($ws.State -eq 'Open' -and (Get-Date) -lt $deadline) {
    if (-not $pending) {
      $pending = $ws.ReceiveAsync((New-Object System.ArraySegment[byte] -ArgumentList (, $buf)), [Threading.CancellationToken]::None)
    }
    try { if (-not $pending.Wait(500)) { continue } } catch { break }
    $r = $pending.Result; $pending = $null
    if ($r.MessageType -eq 'Close') { break }
    $acc.Write($buf, 0, $r.Count)
    if ($r.EndOfMessage) {
      $text = [Text.Encoding]::UTF8.GetString($acc.ToArray()); $acc.SetLength(0)
      if ($save) { $save.WriteLine($text); $save.Flush() }
      Show-Message $text
    }
  }
} finally {
  if ($save) { $save.Dispose() }
  try { [void]$ws.CloseAsync([Net.WebSockets.WebSocketCloseStatus]::NormalClosure, '', [Threading.CancellationToken]::None).Wait(2000) } catch {}
  $ws.Dispose()
}
