<#
.SYNOPSIS
  Prints the open Battle.net custom games from StarCraft: Remastered's Join screen. Read-only.

.DESCRIPTION
  Live mode: connects to the Join screen's panel socket
      ws://127.0.0.1:<port>/panel/GameSearchPanel/<id>
  sends RefreshGameList (the request the screen's own Refresh button sends), listens for -Seconds, and prints
  the games from the GameListInsert / GameListUpdate / GameListDelete stream.

  Offline mode (-FromFile): renders a saved capture (one JSON message per line), e.g. the sample in samples\.

  This script sends nothing except RefreshGameList (and nothing at all with -NoRefresh or -FromFile). It never
  joins, creates, selects or chats. No game memory is read and no input is sent to the game.

  Requirements for live mode:
    * StarCraft is on the Battle.net Join screen (the panel does not exist on the channel screen).
    * -Guid: the panel id of that GameSearchPanel instance. It is assigned per session and per screen; this
      repository does not provide a way to discover it (see docs\04-ui-panel-sockets.md).
  While an outside socket is attached, the on-screen panel may stop redrawing until the screen is reopened.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\gamelist.ps1 -FromFile samples\gamelist_20261013.scrubbed.jsonl
.EXAMPLE
  powershell -ExecutionPolicy Bypass -File tools\gamelist.ps1 -Guid 12345 -Seconds 20 -SaveTo my_capture.jsonl
#>
[CmdletBinding()]
param(
  [string]$Guid,
  [int]$Port,
  [int]$Seconds = 30,
  [string]$FromFile,
  [string]$SaveTo,
  [switch]$NoRefresh,
  [switch]$IncludeClosed,
  [switch]$PassThru
)

$ErrorActionPreference = 'Stop'
$Panel = 'GameSearchPanel'

# ---------------------------------------------------------------- port + socket helpers (read-only)
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

function Open-PanelSocket([int]$Port, [string]$Panel, [string]$Guid) {
  $uri = [Uri]"ws://127.0.0.1:$Port/panel/$Panel/$Guid"
  $ws = New-Object Net.WebSockets.ClientWebSocket
  try { [void]$ws.ConnectAsync($uri, [Threading.CancellationToken]::None).Wait(3000) } catch {}
  if ($ws.State -ne 'Open') {
    $ws.Dispose()
    throw "The socket $uri was refused or timed out: the screen is not open, or the id is wrong / stale."
  }
  return $ws
}

function Send-PanelRequest($ws, [string]$Panel, [int]$N, [string]$Endpoint) {
  $msg = @{ requestId = "panel/${Panel}:$N"; routes = @('allExceptMe'); data = @{ endpoint = $Endpoint; data = @{} } } |
    ConvertTo-Json -Depth 4 -Compress
  $bytes = [Text.Encoding]::UTF8.GetBytes($msg)
  [void]$ws.SendAsync((New-Object System.ArraySegment[byte] -ArgumentList (, $bytes)), 'Text', $true,
    [Threading.CancellationToken]::None).Wait(3000)
}

# Calls $OnText for every complete text message (frames joined until EndOfMessage) until $Seconds pass.
function Receive-PanelMessages($ws, [int]$Seconds, [scriptblock]$OnText) {
  $buf = New-Object byte[] 65536
  $acc = New-Object IO.MemoryStream
  $deadline = (Get-Date).AddSeconds($Seconds)
  $pending = $null
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
      & $OnText $text
    }
  }
}

function Close-PanelSocket($ws) {
  if (-not $ws) { return }
  try { [void]$ws.CloseAsync([Net.WebSockets.WebSocketCloseStatus]::NormalClosure, '', [Threading.CancellationToken]::None).Wait(2000) } catch {}
  $ws.Dispose()
}

# ---------------------------------------------------------------- the list
$games = @{}            # gameID -> @{ info; closed }
$counts = @{}
function Add-Message([string]$text) {
  try { $m = $text | ConvertFrom-Json } catch { return }
  if (-not $m.data) { return }
  $ep = [string]$m.data.endpoint; $d = $m.data.data
  $counts[$ep] = 1 + [int]$counts[$ep]
  switch ($ep) {
    'GameListInsert' { $games[[string]$d.GameInfo.gameID] = @{ info = $d.GameInfo; closed = $false } }
    'GameListUpdate' {
      $games.Remove([string]$d.PrevGameInfo.gameID)
      $games[[string]$d.CurrGameInfo.gameID] = @{ info = $d.CurrGameInfo; closed = $false }
    }
    'GameListDelete' { $k = [string]$d.GameInfo.gameID; if ($games.ContainsKey($k)) { $games[$k].closed = $true } }
  }
}

function Clean([string]$s) { if ($null -eq $s) { return '' }; return ($s -replace '[\x00-\x1F]', '').Trim() }

if ($FromFile) {
  foreach ($line in [IO.File]::ReadAllLines((Resolve-Path $FromFile).Path, [Text.Encoding]::UTF8)) {
    if ($line.Trim()) { Add-Message $line }
  }
} else {
  if (-not $Guid) { throw '-Guid is required for live mode (or use -FromFile).' }
  if (-not $Port) { $Port = Get-PlainHttpPort }
  $ws = Open-PanelSocket $Port $Panel $Guid
  try {
    Write-Host "connected: ws://127.0.0.1:$Port/panel/$Panel/$Guid"
    if (-not $NoRefresh) { Send-PanelRequest $ws $Panel 1 'RefreshGameList'; Write-Host 'sent RefreshGameList' }
    $save = $null
    if ($SaveTo) { $save = New-Object IO.StreamWriter($SaveTo, $false, (New-Object Text.UTF8Encoding($false))) }
    try {
      Receive-PanelMessages $ws $Seconds { param($t) if ($save) { $save.WriteLine($t) }; Add-Message $t }
    } finally { if ($save) { $save.Dispose() } }
  } finally { Close-PanelSocket $ws }
}

$rows = foreach ($g in $games.Values) {
  if ($g.closed -and -not $IncludeClosed) { continue }
  $i = $g.info
  $type = Clean $i.gameType
  if ($i.gameSubTypeTitle) { $type = "$type $(Clean $i.gameSubTypeTitle)" }
  [pscustomobject]@{
    Game    = Clean $i.gameName
    Map     = Clean $i.mapName
    Type    = $type
    Players = "$($i.numPlayers)/$($i.maxPlayers)"
    Obs     = "$($i.numObservers)/$($i.maxObservers)"
    Turn    = $i.netTurnRate
    Private = [bool]$i.private
    Host    = Clean $i.creatorName
    Closed  = $g.closed
  }
}
$rows = @($rows | Sort-Object Type, Game)
$summary = ($counts.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name) $($_.Value)" }) -join ', '
Write-Host "messages: $summary"
Write-Host "games: $($games.Count) seen, $(@($games.Values | Where-Object { -not $_.closed }).Count) open"
if ($PassThru) { $rows } else { $rows | Format-Table -AutoSize }
