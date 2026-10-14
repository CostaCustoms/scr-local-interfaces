# 01 — The local servers

When SC:R is running and logged in, `StarCraft.exe` listens on **two TCP ports on `127.0.0.1`**. Both are
picked at launch (they change every launch) and both belong to the `StarCraft.exe` process.

| Port | Protocol | What answers there |
|---|---|---|
| the HTTP port | plain HTTP/1.0 and plain WebSocket (`ws://`) | `/web-api/...` REST, `/map-preview.bmp`, and the UI panel sockets `/panel/<Panel>/<id>` ✅ 2026-09-28 / 2026-10-13 |
| the TLS port | HTTPS / `wss://` with a Blizzard loopback certificate | the same `/web-api/...` routes ✅ 2026-10-13; the panel pages use it as `wss://loopback.classic.blizzard.com:<port>/...` when they are loaded over https 📄 |

In every session observed the two ports were consecutive and the **lower one was plain HTTP**
(e.g. 65136/65137 on 09-28, 61821/61822 on 10-13). Do not rely on that: [`tools/find-ports.ps1`](../tools/find-ports.ps1)
checks each port instead.

## Finding the ports

```powershell
$sc = Get-Process StarCraft
Get-NetTCPConnection -OwningProcess $sc.Id -State Listen |
  Where-Object LocalAddress -eq '127.0.0.1' | Sort-Object LocalPort | Select-Object LocalPort
```

`find-ports.ps1` does this, then sends `GET / HTTP/1.0` to each port: the plain port answers `HTTP/1.0 404`;
the TLS port does not speak plain HTTP, so the script tries a TLS handshake and prints the certificate subject.

## What the TLS certificate looks like ✅ 2026-09-28

- Subject `CN=loopback.classic.blizzard.com, OU=Classic Games, O="Blizzard Entertainment, Inc.", L=Irvine, S=California, C=US`,
  self-issued, **expired** (valid until 2018-09-19; re-read ✅ 2026-10-13). A client has to skip validation to talk
  to it (`curl -k`, or a validation callback that accepts it).
- The panel scripts build `wss://loopback.classic.blizzard.com:<port>/<route>/<id>` for https pages 📄, so that
  host name is expected to resolve to the loopback address on the player's machine. **UNCONFIRMED** how (hosts
  file, DNS, or the embedded browser's own resolver); not checked.

## HTTP behaviour ✅ 2026-10-13

- Responses are `HTTP/1.0` with **no headers at all** (no `Content-Type`, no `Content-Length`), then the body.
- An unknown path returns status `404` with the reason phrase **`OK`** (`HTTP/1.0 404 OK`) and the body
  `Not Found`.
- Paths tried that returned 404: `/`, `/index.html`, `/webui/`, `/webui/dist/`, `/webui/dist/<Panel>/`,
  `/webui/dist/<Panel>/<Panel>.html`, `/panel/`, `/panel/<Panel>`, `/json`, `/json/list`, `/v1/gateway`
  (without the `/web-api/` prefix). So the server does **not** serve the UI pages or list panels over HTTP.
- `/web-api/v1/gateway` and `/web-api/v1/leaderboard` returned `200` with JSON on both ports (see
  [03-web-api-auth.md](03-web-api-auth.md) for why that is notable).

## Where the code lives 🔎

- `ClientSdk.dll` (next to `StarCraft.exe` in `x86_64\`) contains the server strings: `Not Authorized`,
  `web-api`, `web-api/(.*)`, `GET`, `POST`, `Game returned error`.
- WebSocket server names: `LocalWebSocketServerService`, `LocalWebSocketServerMessageReceiver`,
  `ILocalWebsocketServerV1`, `ILocalWebsocketHttpRequestV1`, `ILocalWebsocketServerEventsV1`, and the
  notifications `BindSuccessNotification`, `BindTlsSuccessNotification`, `BindErrorNotification`,
  `BindTlsFailureNotification`, `ClientConnectNotification`, `ClientDisconnectNotification`,
  `DataReceivedNotification`. The "Bind" / "BindTls" pair matches the two listeners above.

## Answered questions from the March notes

| Question (March 2026) | Answer |
|---|---|
| Is the WebSocket on the HTTP port or a separate one? | **The same port.** The panel sockets are `ws://127.0.0.1:<HTTP port>/panel/<Panel>/<id>` ✅ (used live from 2026-09-28). The second listener is the TLS twin, not a separate WebSocket server ✅ 2026-09-28 |
| WebSocket message format? | JSON envelope, see [04-ui-panel-sockets.md](04-ui-panel-sockets.md) ✅ |
| `map-preview.bmp` hash format? | 32 hex characters (128-bit, MD5-sized), e.g. `map-preview.bmp?hash=2ddad9c8…` ✅ 2026-10-04 (in a Create-screen `minimapPreviewUrl`). Which hash function: **UNCONFIRMED** |

## Other processes

- The panels are drawn by an embedded Chromium (`x86_64\cef\SceneCefBrowser.exe`), started by the client with a
  `SyncMemName=…` argument. On 2026-10-13 none of those processes had a listening TCP port (no remote
  debugging endpoint) ✅.
- `ClientSdkMDNSHost.exe` and `ClientSdkFirewallHelper.exe` ship next to the client (LAN discovery and firewall
  setup by their names; not studied).
