# 05 — The Battle.net custom games list

✅ 2026-10-13: the full list of open custom games, live, from the Join screen's panel socket.

## How to get it

1. In the client, go to the Battle.net channel and open the **Join** screen (Join button / Alt+J). The list is
   not available on the channel screen itself — the panel only exists while the Join screen is shown ✅.
2. Connect to `ws://127.0.0.1:<HTTP port>/panel/GameSearchPanel/<id>` (port: [01](01-local-servers.md); id:
   [04](04-ui-panel-sockets.md#the-panel-id)).
3. Send `RefreshGameList` (no data) — the same request the page's Refresh button sends.
4. Read. Join frames until end-of-message before parsing.

[`tools/gamelist.ps1`](../tools/gamelist.ps1) does steps 2–4 and prints a table; it can also render a saved
capture (`-FromFile`).

## Messages

| Endpoint | Data | Meaning |
|---|---|---|
| `PopulateGameTypes` | `{GameTypes: [{id, name}]}` | Filter list: Show All 0, Top vs Bottom 15, Melee 2, Free For All 3, One on One 4, Use Map Settings 10, Capture The Flag 5, Greed 6, Slaughter 7, Sudden Death 8, Team Melee 11, Team Free For All 12, Team Capture The Flag 13 |
| `ColorTable` | `{colors, previousID}` | Text color codes for game / map names |
| `GameListInsert` | `{GameInfo}` | A game is listed |
| `GameListUpdate` | `{PrevGameInfo, CurrGameInfo}` | A listed game changed (match on `PrevGameInfo.gameID`) |
| `GameListDelete` | `{GameInfo}` | A game left the list (started, closed or filled) |

In the 2026-10-13 capture (30 s): 34 inserts, 27 updates, 12 deletes; 43 distinct games, 32 still open at the
end. Most updates were `numPlayers` changes, `closedSlots` changes and a fresh `lastUpdatedTime`.
Sample: [`samples/gamelist_20261013.scrubbed.jsonl`](../samples/gamelist_20261013.scrubbed.jsonl).

## `GameInfo` fields ✅ 2026-10-13

Order as sent. "Seen" = values across the 100 `GameInfo` records in the capture.

| Field | Type | Seen / meaning |
|---|---|---|
| `gameName` | string | The game's name (may contain color codes) |
| `gameType` | string | `"Top vs Bottom"`, `"Use Map Settings"`, `"Melee"`, `"Free For All"`, `"One on One"` |
| `gameTypeId` | int | 15, 10, 2, 3, 4 (same ids as Create / lobby) |
| `gameSubTypeTitle` | string | The **teams value**, e.g. `"3 vs 3"`, `"4 vs 4"`, `"1 vs 2"`, `"2 vs 6"`; `""` when the type has none |
| `gameSubType` | string | The **label**, `"Teams:"`, or `""`. (The two names look swapped compared with the Create screen's `subTypeTitle:"Teams"`.) |
| `mapName` | string | Map title |
| `mapWidth`, `mapHeight` | int | Tiles: 64, 96, 128, 192, 256 |
| `gameSpeed` | string | `"Fastest"` (only value seen) |
| `netTurnRate` | string | `"Dynamic"`, `"10"`, `"12"`, `"14"`, `"16"`, `"20"`, `"24"` |
| `replay` | bool | `true` on one game (a replay being watched together) |
| `savedGame` | bool | always `false` here |
| `computersAllowed` | bool | always `true` here |
| `hotkeysDisabled` | bool | |
| `originalLimits` | bool | original (vs extended) unit limits |
| `proxied` | bool | `true` on ~10 % of records; meaning **UNCONFIRMED** (relayed connection?) |
| `isEUDGame` | bool | EUD map |
| `gameID` | int | Unique per listed game. In every record it was **equal to `createdTime`** |
| `creatorName` | string | The host's name |
| `numPlayers` / `maxPlayers` | int | 1–8 / 2–8 |
| `numObservers` / `maxObservers` | int | mostly 0 / 0; 4 when observers are on |
| `closedSlots` | int | 0, 2, 4 |
| `geoDistance` | int | Distance to the host, unit unknown (scrubbed to 0 in the sample) |
| `private` | bool | `true` for 10 % of records: **private games are listed too**, flagged |
| `lastUpdatedTime` | int | Unix time in **milliseconds** (2026 values) |
| `createdTime` | int | Same value as `gameID` (10-digit, but **not** a 2026 unix time); meaning **UNCONFIRMED** |
| `visibility` | int | 0, 1 or 3; meaning **UNCONFIRMED** (no correlation with `private` checked) |

## Joining (documented, not done here) 📄

The page joins a game with `OnSelectedGameChanged {selectedId: <gameID>}` followed by `JoinGameLobby` (no data).
A private game presumably then shows `PasswordPanel` (`ConfirmPassword {password}`): **UNCONFIRMED**.
The tools in this repository do not send these.

## Not covered

- The LAN games list is a **native** screen; there is no socket for it ✅ 2026-10-03.
- The list is a snapshot of what the Join screen shows; the screen's own filters (`filterOptions`) may hide games.
  Whether the server filters by them is **UNCONFIRMED**.
