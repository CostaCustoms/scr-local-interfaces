# MapBrowserInfoPanel — map / replay info pane

**Live when:** next to the map browser, and on the **LAN Create** screen ✅ 2026-10-03, where it streamed only
`ColorTable` (no map name reached the socket).

## IN (game → page)

| Endpoint | Data | Status |
|---|---|---|
| `ColorTable` | `{colors:[{id, color}], previousID}`; decoded as ARGB by this page | ✅ 2026-10-03 |
| `OnFileBrowserSelectionChanged` | `{entry}` — fields used: `infoPaneHeading`, `infoPaneParagraph`, `minPlayers`, `maxPlayers`, `numOpponents`, `mapTitle`, `mapCreatorName`, `mapWidth`, `mapHeight`, `mapTileset`, `minimapPreviewUrl`, `errorMessage`, `isReplay`; for replays also `replayGameTypeInText`, `replayGameDateInText`, `replayLengthInText`, `replayFilename`, `replayGamePlayerList` | 📄 |
| `OnMapPreferencesChanged` | — | 📄 |
| `SetSelectedFileBrowserEntry` | — resets the pane | 📄 |

The page parses "Suggested Players:" out of `infoPaneParagraph`. Its replay player list is rendered with race
(`zerg`, `terran`, `protoss`, `random`) and result (`win`, `loss`, `draw`, `disconnect`, `undecided`) values 📄.

## OUT (page → game) 📄

| Endpoint | Data | When |
|---|---|---|
| `OnMinimapPreviewImageClicked` | none | Click on the minimap |
