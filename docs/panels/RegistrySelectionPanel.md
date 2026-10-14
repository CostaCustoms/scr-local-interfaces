# RegistrySelectionPanel — choose an id (toon)

**Live when:** unclear. On the LAN Registry screen it did **not** take a socket ✅ 2026-10-03, so that screen is
native. Everything below is 📄.

## IN (game → page) 📄

| Endpoint | Data | Page use |
|---|---|---|
| `SetToons` | `{toons: [{id, name, gateway}], selected}` | List shown as `name (gateway)`; an empty list makes the page send `ClearSelectedToon` |
| `ClearSelectedToon` | none | Clears the selection |

## OUT (page → game) 📄

| Endpoint | Data | When |
|---|---|---|
| `SetSelectedToon` | `{id: <int>}` | A row is selected |
| `UrlResolved` | `{resetResponse: true}` | Right after `SetSelectedToon` |
| `ClearSelectedToon` | none | The list arrived empty |
| `Enter` | none | Double-click on a row (probably Ok: **UNCONFIRMED**) |
