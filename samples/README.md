# Samples

All samples are scrubbed. Nothing in them identifies a real player.

| File | What it is | How it was scrubbed |
|---|---|---|
| `gamelist_20261013.scrubbed.jsonl` | The full 30-second capture of a `GameSearchPanel` socket after `RefreshGameList` on 2026-10-13: 75 messages, one JSON object per line, exactly as received (inbound envelope included) | Every `creatorName` → `Player1`…`Player42` (consistent per player); every `gameName` → `Game 01`…`Game 43`; `gameID` and `createdTime` renumbered from 100001 (they were equal in the original, so they are kept equal); `geoDistance` → 0; one map name with a real person's name → `Custom Map A`. Other map names are public custom-map titles and were kept. `lastUpdatedTime` kept |
| `lobby-socket_20261004.scrubbed.jsonl` | 16 messages showing what a `GameLobbyPanel` socket receives: slot updates, local player, map status, chat lines (`OnMessage` of types `info`, `playerStats`, `message`, `friendFollow`), a friend presence update, a relayed lobby-chat request, the countdown | **Abridged and rewritten.** Endpoint names, envelope shapes and field names are verbatim from a 2026-10-04 capture; every value (names, BattleTags, ids, GUID, icon hash, win/loss numbers, game name, password) was replaced |
| `web-api-gateway_20261013.json` | `GET /web-api/v1/gateway` on 2026-10-13 | Nothing personal in it; pretty-printed |

Render the game list offline:

```powershell
powershell -ExecutionPolicy Bypass -File ..\tools\gamelist.ps1 -FromFile gamelist_20261013.scrubbed.jsonl
powershell -ExecutionPolicy Bypass -File ..\tools\chatlog.ps1 -FromFile lobby-socket_20261004.scrubbed.jsonl
```
