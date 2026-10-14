# GameSearchMapInfoPanel — selected game's details (Join screen)

**Live when:** expected on the Battle.net Join screen next to `GameSearchPanel` (📄; not attached live).

## IN (game → page) 📄

| Endpoint | Data | Page use |
|---|---|---|
| `UpdateSelection` | `{GameInfo}` | Fields shown: `numPlayers`, `maxPlayers`, `numObservers`, `maxObservers`, `closedSlots`, `creatorName`, `gameSpeed`, `netTurnRate`, `mapWidth`, `mapHeight`, `hotkeysDisabled`, `originalLimits` |
| `SetMapPreview` | `{mapPreview}` — an image path/URL (backslashes turned into `/`) | Minimap image |
| `IsRefereeGame` | `{observersAreReferees}` | |
| `SetCountdown` | `{count}` | |
| `ClearSelection` | none | Resets the pane |

## OUT (page → game) 📄

| Endpoint | Data | When |
|---|---|---|
| `OnMinimapPreviewImageClicked` | none | Click on the minimap |
| `navigateToCreateScreen` | none | Alt + the "Create" hotkey letter. Handled by `GameSearchPanel` (relay). |
| `showGameSearchFilter` / `resetGameSearchFilter` / `saveGameSearchFilter` | none | Alt + filter / reset / save hotkeys; handled by `GameSearchPanel` |
| `EnableHotkeySuppression` | `{enable:true}` | On connect |

Note the lower-case first letter of these four relay messages: they are page-to-page messages, not game
requests.
