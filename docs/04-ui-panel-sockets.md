# 04 — The UI panel sockets

Many SC:R menu screens are web pages ("panels") drawn by an embedded Chromium (`SceneCefBrowser.exe`). Each
panel page talks to the game over a **WebSocket on the client's own HTTP port**. Anything else on the PC that
knows the URL can open the same kind of socket, receive what the game pushes to that panel, and send the
requests the page would send.

Per-panel details: [panels/](panels/).

## The URL

```
ws://127.0.0.1:<HTTP port>/panel/<Panel>/<id>
```

- `<Panel>` is the page name, e.g. `GameSearchPanel`. Each page declares its route in its HTML as
  `<route path="panel/<Panel>">` 📄, and the socket path is `/<route path>/<id>` 📄 ✅.
- The page reads **`port`** and **`guid`** from its own URL query string and builds the socket URL from them 📄.
  Over https the page uses `wss://loopback.classic.blizzard.com:<port>/<route path>/<guid>` instead 📄.
- The pages are packaged inside the game data and loaded as `webui/dist/<Panel>/<Panel>.html?...` 📄; the local
  HTTP server does **not** serve them (all such paths are 404) ✅ 2026-10-13.

### The panel id

- The id (`guid` in the page's URL) is a number assigned by the client ✅.
- It is assigned when the client builds that screen's page, so it is **per session and per screen instance**:
  leaving and re-entering a screen produces a new id ✅.
- A socket for a panel whose screen is **not currently shown** is refused ✅ (e.g. `GameSearchPanel` while
  sitting on the channel screen, 2026-10-13).
- No HTTP route lists panels or their ids (see [01-local-servers.md](01-local-servers.md#http-behaviour--2026-10-13)),
  and the embedded browser exposes no debugging port ✅ 2026-10-13.
- **This repository does not include a way to discover the id.** The tools take it as a `-Guid` parameter; you
  need to obtain it yourself.

## The envelope

**Page → game** (what the page's `sendMessage(endpoint, data)` builds) 📄 ✅:

```json
{ "requestId": "<route path>:<n>",
  "routes": ["allExceptMe"],
  "data": { "endpoint": "RefreshGameList", "data": {} } }
```

- `data.data` is `{}` when the request has no payload.
- Some requests carry a `line` field naming the page's source line, e.g.
  `{"id": 15, "line": "GameCreatePanel.jsx:234"}`; the game accepted requests with it ✅ 2026-10-04.

**Game → page** ✅ 2026-10-04 / 2026-10-13:

```json
{ "originRoutePath": "app",
  "requestId": "app-8006",
  "data": { "endpoint": "GameListInsert", "data": { "GameInfo": { "...": "..." } } } }
```

- `requestId` is `app-<n>`, a counter shared across all panels of the session.
- Replies to a request use the endpoint name plus `.response`: `GetStrings.response`,
  `LocalStorageGetValue.response` 📄.
- Large messages arrive as several WebSocket frames; a reader must join frames until end-of-message, or big
  messages (lobby state, file lists) are lost ✅ 2026-10-04.

## Routing: `allExceptMe`

The socket server is a hub. A message is delivered to the other connected clients, not only to the game:

- **Page-to-page relay** ✅ 2026-10-04: a socket attached to `GameLobbyPanel` received requests sent by the
  lobby's chat page, unchanged, with `"originRoutePath": "panel/GameLobbyChatPanel"`, `"requestId": ":0"` and
  `"routes": ["allExceptMe"]` (a `PlaySound` and a `SendChatMessage {message:"hi", target:"GameLobby"}`).
- Pages rely on this: `GameSearchMapInfoPanel` sends `navigateToCreateScreen`, `showGameSearchFilter`,
  `resetGameSearchFilter`, `saveGameSearchFilter`, and it is `GameSearchPanel`'s handler that reacts to them 📄.
- **App broadcasts reach every panel socket** ✅ 2026-10-04: a `GameLobbyPanel` socket received chat lines
  (`OnMessage`), `OnFriendUpdated` and `OnChannelMemberUpdated`; a `GameCreatePanel` socket received
  `OnChannelMemberLeft`. See [06-presence-friends.md](06-presence-friends.md).

## Side effect: the on-screen panel stops updating

When an outside socket is attached to a panel, **that panel on the game's screen can freeze** (stops redrawing
/ reacting) until the screen is rebuilt ✅ 2026-09-28 (friends list and channel panels). Whether closing the
outside socket un-freezes it was not tested. Keep sessions short, and expect to leave and re-enter the screen.

## What a page can send on any screen 📄

Every panel bundles the same small library. These requests exist on every page (most are only used by a few):

| Endpoint | Payload | Notes |
|---|---|---|
| `GetStrings` | `{ids:[...]}` | Page asks for localized strings on connect; reply `GetStrings.response {strings}` |
| `PlaySound` | `{id}` | UI sounds, e.g. `GLUSND_MOUSE_OVER`, `GLUSND_MOUSE_DOWN` |
| `EnableHotkeySuppression` | `{enable: bool}` | Sent while a text box has focus, so typing is not taken as hotkeys |
| `LocalStorageGetValue` / `LocalStorageSetValue` | `{key}` / `{key, value}` (value = JSON text) | Page settings stored by the game, e.g. `filterOptions`, `searchQuery` on the Join screen |
| `NavigateToPopup` | `{resourceFilename}` | |
| `NavigateToPreviousPopup` | none | |
| `Exit` | none | The page's cancel/close. **Effect when sent from outside is untested**; do not send it casually |
| `LoginToLegacy`, `CreateLegacyAccount`, `ChangeLegacyPassword`, `ChangeLegacyEmailAddress`, `ResetLegacyPassword` | account names, passwords, e-mail, gateway | Legacy (classic Battle.net) account pages. Never used here |

## Which screens are web panels ✅ 2026-10-03 / 2026-10-13 unless marked

| Screen | Panels that take a socket there | Notes |
|---|---|---|
| Main menu | `MainMenuHDAdPanel` | Menu buttons themselves are native |
| Select Connection | `LANProtocolSelectionPanel`, `GatewayPanel` | The Battle.net / LAN choice is native; `ConnectionSelectionPanel` was not seen live |
| Battle.net channel | `ChatPanelHDAd` | The chat/ad panel; `ParticipantsPanel` (friends list) when that list is open — on 2026-10-04 it was not up on the plain channel screen |
| Battle.net Join (custom games list) | `GameSearchPanel` ✅ 2026-10-13, `GameSearchMapInfoPanel` 📄 | Not live while on the channel |
| Battle.net Create Game | `GameCreatePanel` ✅ | `MapBrowserPanel` + `MapBrowserInfoPanel` when browsing maps 📄 |
| Game lobby (Battle.net and LAN) | `GameLobbyPanel` ✅, `GameLobbyChatPanel` ✅ (seen as a relay origin) | The lobby's start (Ok) and Cancel are **native**; the lobby page has no start or leave request 📄 |
| Password prompt | `PasswordPanel` 📄 | |
| LAN Games list, LAN Create, Registry (LAN id), score screen, Victory/Defeat box | **none** — native screens | `RegistrySelectionPanel` exists 📄 but took no socket on the LAN Registry screen; the LAN id of `GameSearchPanel` refused the socket |
| LAN Create screen | `MapBrowserInfoPanel` only | Streams only `ColorTable` |

## Shared push: `ColorTable` ✅

Pushed on connect by several panels (Join, Create, lobby, map info):

```json
{ "colors": [ { "id": 2, "color": 4294489252 }, ... ], "previousID": 1 }
```

`color` is a 32-bit value; the map-info page decodes it as `alpha = c>>24`, `blue = (c>>16)&255`,
`green = (c>>8)&255`, `red = c&255` 📄. The ids are the in-text color codes used in map/game names.

## Chat targets 🔎 (+ ✅ where marked)

`SendChatMessage {message, target}` takes one of: `CurrentBattlenetChannel` ✅ 2026-09-28, `GameLobby` ✅
2026-10-04 (the lobby chat page's own request, seen relayed), `Lan`, `InGameAll`, `InGameAllies`,
`InGameObservers`, `InGameSpecificPlayer` (names from the client's strings; the in-game ones are
**UNCONFIRMED** over a panel socket).
