# GameCreatePanel — Battle.net Create Game

**Live when:** the Battle.net Create Game screen is open ✅ (used live from 2026-09-28; full settings test
2026-10-04). The LAN Create screen is **native**; only `MapBrowserInfoPanel` takes a socket there ✅ 2026-10-03.

## IN (game → page)

On connect the game pushes the whole form state. Order seen ✅ 2026-10-04: `ColorTable`, `PopulateTurnRates`,
`OnTurnRateChanged`, `OnGameNameChanged`, `OnPrivacyChanged`, `OnPasswordChanged`, `PopulateGameTypes`,
`PopulateSubTypes`, `OnFileBrowserSelectionChanged`, `OnGameTypeChanged`, `OnOriginalGameLimitsChanged`,
`OnCustomHotkeysChanged`, `OnFileBrowserContentChanging`, `OnRecentFilesContentAdded` (one per recent map),
`OnFileBrowserContentChanged`.

| Endpoint | Data | Status |
|---|---|---|
| `PopulateGameTypes` | `{gameTypes: [{id, name}]}` (lower-case `g` here) | ✅ |
| `PopulateSubTypes` | `{subTypeTitle, subTypes: [{id, name}], selectedId}` | ✅ |
| `OnGameTypeChanged` | `{id}` | ✅ |
| `OnGameNameChanged` | `{gameName}` | ✅ |
| `OnPrivacyChanged` | `{public: bool}` | ✅ |
| `OnPasswordChanged` | `{password}` | ✅ |
| `OnOriginalGameLimitsChanged` | `{originalGameLimits: bool}` | ✅ |
| `OnCustomHotkeysChanged` | `{customHotkeysDisabled: bool}` | ✅ |
| `PopulateTurnRates` | `{turnRates: [{id, rate}]}` | ✅ |
| `OnTurnRateChanged` | `{turnRate}` | ✅ |
| `OnGameSpeedChanged` | `{speed}` | 📄 |
| `OnFileBrowserContentChanging` | `{locationTitle}` — the recent list is reset | ✅ |
| `OnRecentFilesContentAdded` | `{entry}` — one recent map (fields below) | ✅ |
| `OnFileBrowserSelectionChanged` | `{entry}` — the selected map; `{entry:{}}` when none | ✅ |
| `OnFileBrowserContentChanged` | `{selectedId}` | ✅ |
| `OnMapSelected` | `{entryID}` — back from the map browser; the page answers with `OnFileSelectionChanged` | 📄 |
| `ColorTable` | see doc 04 | ✅ |

### Values seen ✅ 2026-10-04

- `PopulateGameTypes`: Top vs Bottom 15, Melee 2, Free For All 3, One on One 4, Use Map Settings 10, Capture The
  Flag 5, Greed 6, Slaughter 7, Sudden Death 8, Team Melee 11, Team Free For All 12, Team Capture The Flag 13.
- `PopulateSubTypes` for Top vs Bottom on an 8-player map: `subTypeTitle:"Teams"`, `subTypes` "7 vs 1" (7) …
  "1 vs 7" (1), i.e. id = players on Top; `selectedId` remembered from the last game.
- `PopulateTurnRates`: `{id:-1, rate:"Dynamic"}`, then ids 0–6 = rates "8", "10", "12", "14", "16", "20", "24".

### Map entry fields (`entry`) ✅ 2026-10-04

| Field | Example / meaning |
|---|---|
| `id` | entry id; this is what `OnFileSelectionChanged {id}` takes |
| `fileBrowserEntryTitle` | file name, e.g. `(8)SomeMap.scm` |
| `infoPaneHeading`, `infoPaneParagraph` | map title and description text (with "Suggested Players:" / author lines) |
| `mapTitle`, `mapCreatorName`, `mapTileset`, `mapWidth`, `mapHeight`, `mapNumber` | |
| `minPlayers`, `maxPlayers`, `numHumans`, `numOpponents` | |
| `minimapPreviewUrl` | `http://127.0.0.1:<port>/map-preview.bmp?hash=<32 hex>` |
| `isMap`, `isReplay`, `isSavedGame`, `isEUDMap`, `isFolder`, `isRecentFile`, `isRecentMap`, `isLocalFileAvailable`, `isCloud`, `isCloudFolder`, `loaded` | flags |
| `type`, `status`, `gameType`, `authCandidate`, `cloudFileId`, `saveGameId`, `errorMessage` | numbers / text, meaning not studied |

## OUT (page → game)

| Endpoint | Data | Status |
|---|---|---|
| `OnGameNameChanged` | `{name}` | ✅ 2026-10-04 |
| `OnGameVisibilityChanged` | `{visibility: "public" \| "private"}` | ✅ `"private"` 2026-10-04; `"public"` 📄 |
| `OnPasswordChanged` | `{password}` (the row is hidden when public) | ✅ 2026-10-04 |
| `OnGameTypeSelectionChanged` | `{id, line}` (`id` from `PopulateGameTypes`) | ✅ 2026-10-04 (`id:15` → Top vs Bottom, echoed by `OnGameTypeChanged`) |
| `OnSubTypeSelectionChanged` | `{id, line}` (`id` from `PopulateSubTypes`) | ✅ 2026-10-04 (`id:4` = "4 vs 4") |
| `OnFileSelectionChanged` | `{id, line}` — pick a map from the recent list | 📄 |
| `OnGameSpeedChanged` | `{speed}`, 0–6 = Slowest … Fastest (page default 6) | 📄 |
| `OnTurnRateChanged` | `{turnRate: <turnRates[i].id>}` | 📄 |
| `OnSetGameLimits` | `{useOriginalLimits: bool}` | ✅ 2026-10-04 |
| `OnDisableHotkeysChanged` | `{hotkeysDisabled: bool}` | 📄 |
| `OnSetObserversAreReferees` | `{observersAreReferees: bool}` | 📄 |
| `ShowFileBrowser` | none — opens the map browser (folder icon / Alt+S) | 📄 |
| `StartGame` | none — creates the game and opens the lobby (also what Enter sends) | ✅ 2026-10-04 |

`line` is the page's own source reference (`"GameCreatePanel.jsx:234"`); the game accepted it ✅.

## Page logic worth knowing 📄

- Visibility options are `public` (id 0) and `private` (id 1); limits `Extended` / `Original`; hotkeys
  `enabled` / `disabled`.
- Selecting a **saved game** forces private; an **EUD map** forces original limits.
- Settings are remembered between creates (map, type, sub-type) ✅ 2026-10-04.
- A map change can reset type / sub-type / privacy, so set the map first **UNCONFIRMED** (reasoned from the page
  re-sending state on selection, not tested).
