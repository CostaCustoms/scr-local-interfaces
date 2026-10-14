# StarCraft: Remastered — local interfaces

Notes on the interfaces that the StarCraft: Remastered (SC:R) Windows client opens **on your own PC**:
its loopback HTTP/TLS server (`/web-api/...`), the WebSocket that its in-game web UI panels use, the
custom-games list those panels receive, the friend / chat / presence objects that ride on them, and the
replay file format.

Everything here was observed on one Windows PC with a normal, logged-in client. It is research notes,
not an SDK. It can be wrong and it can break with any patch.

> Not affiliated with or endorsed by Blizzard Entertainment. Read [DISCLAIMER.md](DISCLAIMER.md) first.

## What is in here

| Path | What it covers |
|---|---|
| [docs/01-local-servers.md](docs/01-local-servers.md) | The two loopback listeners (plain HTTP + TLS), how to find their ports, what answers where |
| [docs/02-web-api.md](docs/02-web-api.md) | The `/web-api/` REST routes: the ones bw-web-api already knows, plus file sets, map preview, config URL keys and other names found in the client |
| [docs/03-web-api-auth.md](docs/03-web-api-auth.md) | The `/web-api/` prefix, the 401 seen in September, the credential check found in the client, and the 200 seen in October |
| [docs/04-ui-panel-sockets.md](docs/04-ui-panel-sockets.md) | How the web UI panels talk to the game: URL, envelope, routing, broadcasts, side effects, web vs native screens |
| [docs/panels/](docs/panels/) | One page per panel: when it is live, messages in, messages out, field tables |
| [docs/05-game-list.md](docs/05-game-list.md) | The Battle.net custom-games list (`GameListInsert` / `Update` / `Delete`) and every `GameInfo` field |
| [docs/06-presence-friends.md](docs/06-presence-friends.md) | Friend, channel-member and chat-message objects; rich presence and friends names found in the client |
| [docs/07-replays.md](docs/07-replays.md) | The `.rep` container (classic 1.16 and SC:R), header, players, command stream framing |
| [tools/find-ports.ps1](tools/find-ports.ps1) | Lists SC:R's loopback ports and tells the HTTP one from the TLS one |
| [tools/gamelist.ps1](tools/gamelist.ps1) | Read-only: prints the open custom games from the Join screen's panel socket (or from a saved capture) |
| [tools/chatlog.ps1](tools/chatlog.ps1) | Read-only: prints chat / info lines that arrive on a panel socket (or from a saved capture) |
| [tools/rep_cmds.py](tools/rep_cmds.py) | Offline `.rep` reader: header, players, command counts, optional dump |
| [samples/](samples/) | Scrubbed captures: the game list, a lobby chat stream, a gateway response |

## How claims are marked

| Mark | Meaning |
|---|---|
| ✅ *(date)* | Proven live on a real client on that date |
| ❌ *(date)* | Tried live on that date; it did **not** work |
| 📄 | Read from the client's own UI panel scripts (the page's code sends or handles it); not necessarily exercised live |
| 🔎 | Name found in the client binary's strings; never called or seen on the wire |
| **UNCONFIRMED** | A guess or an inference; treat it as a lead, not a fact |

Dates are 2026. The client build studied was the one current in March–October 2026
(binary string research on 1.23.10.13515).

## Quick start

```powershell
# 1. Which ports is the running client listening on, and which one is plain HTTP?
powershell -ExecutionPolicy Bypass -File tools\find-ports.ps1

# 2. Ask the local REST API for the gateway list (read-only)
Invoke-RestMethod http://127.0.0.1:<http-port>/web-api/v1/gateway

# 3. Render the scrubbed game-list sample offline
powershell -ExecutionPolicy Bypass -File tools\gamelist.ps1 -FromFile samples\gamelist_20261013.scrubbed.jsonl

# 4. Live game list: open the Join screen in the client first, then
powershell -ExecutionPolicy Bypass -File tools\gamelist.ps1 -Guid <panel id>
```

**Open item — the panel id.** Every panel socket URL ends in a per-session numeric id that the client
assigns when it builds the screen. This repository does not ship a way to discover it; you have to obtain
it yourself. See [docs/04-ui-panel-sockets.md](docs/04-ui-panel-sockets.md#the-panel-id).

## Scope

In scope: what the client exposes on `127.0.0.1`, what its UI panels send and receive, and the replay file
format. Out of scope, on purpose: anything that reads or writes game memory, sends input to the game, injects
commands, or automates play. The tools only listen, plus one request the UI itself sends (`RefreshGameList`).

## Credits

- [bw-web-api](https://github.com/evanandrewrose/bw-web-api) (GitHub user evanandrewrose) documented the local REST endpoints
  first; [docs/02-web-api.md](docs/02-web-api.md) builds on its endpoint list.
- `tools/rep_cmds.py` contains a Python port of Mark Adler's `blast.c` (PKWARE DCL decompressor, zlib license;
  the notice is kept in the file).
- Unit / tech / upgrade id names in `rep_cmds.py` follow the community (BWAPI) enumerations.

## License

- Scripts in `tools/`: MIT, see [LICENSE](LICENSE) (except the `blast.c` port inside `rep_cmds.py`, which keeps
  its zlib-style notice).
- Documentation (`README.md`, `DISCLAIMER.md`, `docs/`) and `samples/`: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- No Blizzard files are included. StarCraft and Battle.net are trademarks of Blizzard Entertainment.
