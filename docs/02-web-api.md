# 02 — The local REST API (`/web-api/`)

Base URL: `http://127.0.0.1:<HTTP port>/web-api/` (or `https://127.0.0.1:<TLS port>/web-api/`, certificate
check disabled). See [01-local-servers.md](01-local-servers.md) for the ports and
[03-web-api-auth.md](03-web-api-auth.md) for authentication.

**Prefix:** on the 2026 client every REST route sits under **`/web-api/`**. `GET /v1/gateway` (no prefix) is a
404; `GET /web-api/v1/gateway` answers ✅ 2026-09-28 (401) and ✅ 2026-10-13 (200). The server matches the
pattern `web-api/(.*)` 🔎 (`ClientSdk.dll`).

The client's own screens call these routes (profile, ladder, map stats). The local server answers by asking
Blizzard's backend, so a call here causes traffic to Blizzard just as opening that screen would. Be gentle.

## Endpoints already documented by bw-web-api

These come from [bw-web-api](https://github.com/evanandrewrose/bw-web-api), written before the `/web-api/`
prefix and the credential check existed (as far as we can tell). Prefix them with `/web-api`.

| Endpoint | Notes | Status here |
|---|---|---|
| `/v1/gateway` | Gateways with online user counts | ✅ 2026-10-13 (200, shape below) |
| `/v1/leaderboard` | All leaderboards | ✅ 2026-10-13 (200, shape below) |
| `/v1/leaderboard/{ladder}?offset={o}&length={n}` | Paginated rankings | per bw-web-api; not called here |
| `/v1/leaderboard-name-search/{ladder}/{toon}` | Ranked name search | per bw-web-api; not called here |
| `/v1/leaderboard-rank-by-toon/{ladder}/{toon}/{gateway}` | Ranked data for one profile | per bw-web-api; not called here |
| `/v1/aurora-profile-by-toon/{toon}/{gateway}` | Profile (v1, deprecated) | per bw-web-api; not called here |
| `/v2/aurora-profile-by-toon/{toon}/{gateway}?request_flags=scr_mmgameloading` | Minimal account info | per bw-web-api |
| `…?request_flags=scr_mmtooninfo` | Minimal + recent game count | per bw-web-api |
| `…?request_flags=scr_profile` | Full account info | per bw-web-api |
| `…?request_flags=scr_tooninfo` | Full info minus game history | per bw-web-api |
| `/v1/map-stats-by-toon/{toon}/{gateway}` | Win rate by map and season | per bw-web-api |
| `/v1/matchmaker-gameinfo-playerinfo/{matchId}` | Ranked match info + replay link | per bw-web-api |
| `/v1/file-set/classic.files.global.maps-1v1` | Ladder maps by season | per bw-web-api |

Profile, name-search and map-stats calls need a player name; none were made for these notes.

### `GET /web-api/v1/gateway` ✅ 2026-10-13

An object keyed by gateway id. Sample: [`samples/web-api-gateway_20261013.json`](../samples/web-api-gateway_20261013.json).

| Field | Type | Example |
|---|---|---|
| *(key)* | string gateway id | `"10"`, `"11"`, `"20"`, `"30"`, `"45"` |
| `name` | string | `"U.S. West"`, `"U.S. East"`, `"Europe"`, `"Korea"`, `"Asia"` |
| `region` | string | `"usw"`, `"use"`, `"eu"`, `"kr"`, `"asia"` |
| `is_official` | bool | `true` |
| `online_users` | int | live count |

### `GET /web-api/v1/leaderboard` ✅ 2026-10-13

Top-level keys: `gamemodes`, `gateways`, `leaderboards`, `matchmaked_current_season`, `team_leaderboard_info`.

| Key | Shape |
|---|---|
| `gamemodes` | `{ "<id>": { name } }` — one entry, `"1": {"name": "1v1"}` |
| `gateways` | `{ "<id>": { is_official, name, region } }` (same five as above, no counts) |
| `leaderboards` | `{ "<id>": { id, name, gamemode_id, gateway_id, season_id, season_name, program_id, benefactor_id, last_update_time, next_update_time } }` — 114 entries; `gateway_id` 0 = "Global"; times are unix seconds as strings; `program_id` `"S1"` |
| `matchmaked_current_season` | int (20 on 2026-10-13) |
| `team_leaderboard_info` | object (empty on 2026-10-13) |

## Names found in the client, not in bw-web-api 🔎

### File sets: `/v1/file-set/{name}`

| Name | Probable contents (by name) |
|---|---|
| `classic.files.global.chat-icons` | Chat icon images (global) |
| `classic.files.global.maps-popular` | Popular custom maps |
| `classic.files.global.maps-preview` | Map preview metadata |
| `classic.files.player.maps` | The player's cloud maps |
| `classic.files.player.mp-saves` | Multiplayer save games |
| `classic.files.player.replays` | Cloud-synced replays |
| `classic.files.player.settings` | Synced settings |
| `classic.files.player.sp-saves` | Single-player saves |

None of these were called. Response shapes: **unknown**.

Related cloud-file names 🔎: classes `CloudFileSystem`, `CloudFileStore`, `CloudFileListCacheCollection`,
`DownloadOperation`, `UploadOperation`; fields `cloudFileId`, `isCloud`, `isCloudFolder`, `gameCloudFolder`,
`gameCloudMaps`, `gameCloudPopularMaps`, `gameCloudReplays`, `gameCloudSaveGames`; a `cloud://` URI scheme.
`cloudFileId`, `isCloud` and `isCloudFolder` do appear live in map-browser entries ✅ 2026-10-04
(see [panels/MapBrowserPanel.md](panels/MapBrowserPanel.md)).

### Map preview image

```
GET http://127.0.0.1:<HTTP port>/map-preview.bmp?hash=<32 hex>
```

- The Create screen's map entries carry this URL in `minimapPreviewUrl` ✅ 2026-10-04.
- A GET from the channel screen on 2026-10-13 (for a hash seen on 10-04, and for an all-zero hash) returned
  `404` with body `Not FoundNot Found` ✅. **UNCONFIRMED:** the image is probably only served while that map
  is loaded on a screen (Create / map browser).
- Response type when it works: presumably `image/bmp` (by the name); not captured.

### Portraits

`portrait\%s%d.webm` 🔎 — portrait videos by string id + index, from the game's own assets. Friend and chat
objects carry `portraits.gameIconUrl` pointing to `https://scrassets.classic.blizzard.com/chat-icons/...png`
✅ 2026-10-04.

### Config URL keys 🔎

Remote URLs resolved by key (main-menu carousel, banners, profile links):
`Url.Marketing-Carousel-facebook`, `-teamliquid`, `-twitter`, `-vk`, `-youtube`, `Url.StarCraftBannerChat`,
`Url.StarCraftBannerMain`, `Url.StarCraftMap`, `Url.StarCraftMapPreview`, `Url.Game-Toast`,
`Url.Leaderboard-Personal`, `Url.Profile`, `Url.Profile-Gateway`, `Url.Profile-MatchMaking`,
`Url.Profile-Registry`. Resolver classes `UrlResolveGateway`, `UrlResolveToonMatchMakingToast`; template
variables `{gateway}`, `{toonName}`, `$SEASONID$`. The Registry panel sends `UrlResolved {resetResponse:true}`
when a toon is picked 📄.

### Seasons 🔎

`$SEASONID$`, `seasonNumber`, `BattlenetNewSeasonPopup`, `OnSeasonsIndexFileUnreadable`,
`ShowNewSeasonInfoPopup`, `Seen Seasonal Info Popup`. Suspected routes `/v1/season`, `/v1/season-info`:
**UNCONFIRMED**, not tried. (The leaderboard list above already carries `season_id` and
`matchmaked_current_season`.)

### Avatars 🔎

`AvatarUrlCache`, `AvatarUrlResolveReceiver`, `AvatarResolveSuccessNotification`,
`AvatarResolveFailureNotification`; a JSON field `avatarUrl` in profile responses (not typed by bw-web-api).

### Backend host names 🔎

`us.actual.battle.net`, `test.actual.battle.net`.

## Still unknown

- `request_flags` values beyond the four known.
- Response shapes of the file-set routes.
- When `map-preview.bmp` is served, and which hash function names the map.
- What `Url.Game-Toast` is used for.
- The season index file format (`OnSeasonsIndexFileUnreadable`).
