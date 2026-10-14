# GameLobbyPanel — the game lobby

**Live when:** in a game lobby, on Battle.net and on LAN ✅ (from 2026-09-28; LAN 2026-10-03). It is the one
web panel of the LAN game flow. The lobby's **start (Ok) and Cancel buttons are native**: the page has no
start or leave request 📄, and starting is done in the client UI. After the host starts, the lobby pushes a
countdown ✅ 2026-10-04.

## IN (game → page)

What an outside socket gets on connect ✅ (2026-09-28 … 2026-10-04): `ColorTable`, `SetMapStatus` (sometimes),
then one `SetPlayerData` per player slot, one `SetObserverData` per observer slot, and `SetLocalPlayer`. The same
messages repeat as the lobby changes.

| Endpoint | Data | Status |
|---|---|---|
| `SetPlayerData` | `{id, name, race, color, state, latency, latencyBars}` — `id` is the **slot** (0–7) | ✅ |
| `SetObserverData` | `{id, name, state, latency, latencyBars}` — observer slot ids 128–131 | ✅ |
| `SetLocalPlayer` | `{id, host: bool, raceSelect: [{id, localUpdate, visible}], colorSelect: [...]}` — which slot is you, whether you host, and which slots' race/color you may change (one entry per slot id 0–7 and 128–131) | ✅ |
| `SetMapStatus` | `{mapstatus: [{id, percent}]}` — map download per slot; 100 = done | ✅ |
| `SetCountdown` | `{count}` — 5, 4, 3 … after the host starts | ✅ 2026-10-04 |
| `ColorTable` | see doc 04 | ✅ |
| `SlotSetup` | the team layout: `teams: [{id, name, slots: [{id}, ...]}]`, `observers: [{id}, ...]` (+ `numSlots`, `slots`, `numTeams` 🔎) | 📄 — **never received on an outside socket** (over 100 lobbies watched, through 2026-10-04) |
| `UpdateSelection` | `{GameInfo: {gameTypeId, gameSubType, gameSubTypeTitle, gameSpeed, replay, savedGame, observersAreReferees, ...}}` | 📄 — never received on an outside socket |
| `SetUnavailablePlayerColors` | `{Players: {"<slot>": {UnavailableColorNames: [...]}}}` | 📄 |
| `OnMessage`, `OnFriendUpdated`, `OnChannelMemberUpdated` | app broadcasts (chat, friends) — see [06](../06-presence-friends.md) | ✅ 2026-10-04 |
| relayed `SendChatMessage` / `PlaySound` | from `GameLobbyChatPanel`, `originRoutePath:"panel/GameLobbyChatPanel"` | ✅ 2026-10-04 |

`SlotSetup` and `UpdateSelection` are probably sent once when the page first loads, before any outside socket
can attach (**UNCONFIRMED**). Without them an outside reader does not get team ids from the stream.

### Values seen ✅

| Field | Values |
|---|---|
| `state` | `human`, `open`, `closed`, `computer` (computer ✅ 2026-10-10) |
| `race` | `SelectRace` (joined, not picked yet), `Zerg`, `Terran`, `Protoss`, `Random` |
| `color` | `Random` (the only value seen) |
| `latencyBars` | 0–5; `latency` in ms |

Top vs Bottom, "4 vs 4", 8-slot map: **Top = slots 0–3 (host in 0), Bottom = 4–7** ✅ 2026-10-04 (confirmed on
screen). A player joining a private game took the next open slot (slot 1) ✅ 2026-10-04 (one observation).

## OUT (page → game)

| Endpoint | Data | Who | Status |
|---|---|---|---|
| `RequestRaceChange` | `{id: <slot>, race: "Zerg" \| "Terran" \| "Protoss" \| "Random"}` | anyone, own slot | ✅ (Battle.net and LAN, from 2026-10-03) |
| `RequestColorChange` | `{id: <slot>, color}` | | 📄 |
| `RequestPlayer` | `{team: <teams[].id>}` — clicking a team header moves you to that team | anyone | 📄 |
| `RequestObserver` | none | anyone | 📄 |
| `EnableHotkeySuppression` | `{enable:true}` on connect | | 📄 |

The lobby host's own controls (slot and player management) are deliberately not documented here.

The page drops every request once the countdown is below 3 (`lockAllOptions`) 📄.

## Page logic worth knowing 📄

- Game type ids used by the lobby page: Melee 2, Free For All 3, One on One 4, Capture The Flag 5, Greed 6,
  Slaughter 7, Sudden Death 8, Ladder 9, Use Map Settings 10, Team Melee 11, Team FFA 12, Team CTF 13,
  Team Ladder 14, Top vs Bottom 15, and `WGT_1V1` 17, `WGT_2V2` 18, `WGT_TOURNAMENT` 19,
  `WGT_CLAN_LEAGUE` 20, `WGT_CLAN_WAR` 21, `WGT_NATION_WAR` 22.
