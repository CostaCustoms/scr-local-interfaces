# MapBrowserPanel — the map / file browser list

**Live when:** the map browser opened from Create (folder icon / Alt+S) 📄. Never attached live.

## IN (game → page) 📄

| Endpoint | Data | Page use |
|---|---|---|
| `OnFileBrowserContentChanging` | `{locationTitle}` | Clears the list; shows the folder name |
| `OnFileBrowserContentAdded` | `{entry: {id, fileBrowserEntryTitle, isFolder, isCloud, isCloudFolder, ...}}` | One row per entry |
| `OnFileBrowserContentChanged` | `{selectedId}` | The selected row |

The `entry` objects are the same family as the Create screen's map entries
([GameCreatePanel.md](GameCreatePanel.md#map-entry-fields-entry--2026-10-04)).

## OUT (page → game) 📄

| Endpoint | Data | When |
|---|---|---|
| `OnFileSelectionChanged` | `{id, line:"MapBrowserPanel.jsx:89"}` | Single click |
| `OnFileActivated` | `{id}` | Double-click: opens a folder, or picks the map (Create then receives `OnMapSelected {entryID}`) |
| `EnableHotkeySuppression` | `{enable}` | Search box focus |

There is no back / ok request in this page; those buttons are native.
