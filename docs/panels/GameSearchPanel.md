# GameSearchPanel — the Battle.net custom games list

**Live when:** the Battle.net **Join** screen is open (from the channel, the Join button / Alt+J) ✅ 2026-10-13.
Refused while sitting on the channel screen ✅ 2026-10-13. A `GameSearchPanel` id used on the **LAN** games list
refused the socket ✅ 2026-10-03 — the LAN list is a native screen.

Full field list and a worked example: [../05-game-list.md](../05-game-list.md).

## IN (game → page)

| Endpoint | Data | Status |
|---|---|---|
| `PopulateGameTypes` | `{GameTypes: [{id, name}]}` — note the capital `G`; includes `{id:0, name:"Show All"}` for the filter | ✅ 2026-10-13 |
| `ColorTable` | `{colors:[{id, color}], previousID}` | ✅ 2026-10-13 |
| `GameListInsert` | `{GameInfo}` — a game appeared | ✅ 2026-10-13 |
| `GameListUpdate` | `{PrevGameInfo, CurrGameInfo}` — matched by `PrevGameInfo.gameID` | ✅ 2026-10-13 |
| `GameListDelete` | `{GameInfo}` — the page keeps the row and marks it closed | ✅ 2026-10-13 |
| `LocalStorageGetValue.response` | `{key, value}` for `filterOptions` / `searchQuery` (value is JSON text) | 📄 |
| `showGameSearchFilter`, `navigateToCreateScreen`, `resetGameSearchFilter`, `saveGameSearchFilter` | none — relayed from `GameSearchMapInfoPanel`'s hotkeys | 📄 |

After `RefreshGameList`, 30 s produced 75 messages: 34 inserts, 27 updates, 12 deletes, 1 `PopulateGameTypes`,
1 `ColorTable`; 43 distinct games ✅ 2026-10-13.

## OUT (page → game)

| Endpoint | Data | When the page sends it | Status |
|---|---|---|---|
| `RefreshGameList` | none | Refresh button; the page also clears its list and selection first | ✅ 2026-10-13 (the stream above followed) |
| `OnSelectedGameChanged` | `{selectedId: <gameID>}` | Clicking a row | 📄 |
| `JoinGameLobby` | none | Join / double-click: the page sends `OnSelectedGameChanged` then `JoinGameLobby` | 📄 |
| `ClearSelectedGame` | none | Selection cleared | 📄 |
| `CreateGame` | none | Create button (also its reaction to a relayed `navigateToCreateScreen`) | 📄 |
| `LocalStorageGetValue` | `{key:"filterOptions"}`, `{key:"searchQuery"}` | On connect | 📄 |
| `LocalStorageSetValue` | `{key, value}` | Filter saved / search typed | 📄 |
| `EnableHotkeySuppression` | `{enable}` | Search box focus | 📄 |

## Notes

- A password-protected game presumably leads to `PasswordPanel` after `JoinGameLobby`: **UNCONFIRMED**.
- `GameSearchPanel` + `GameSearchMapInfoPanel` share one screen; the second shows the selected game's details.
