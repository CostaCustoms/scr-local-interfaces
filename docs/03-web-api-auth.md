# 03 — `/web-api/` and authentication

## What was seen

| Date | Request | Result |
|---|---|---|
| ✅ 2026-09-28 | `GET /v1/gateway` (no prefix) on the HTTP port | `404` |
| ✅ 2026-09-28 | `GET /web-api/v1/gateway`, `GET /web-api/v1/leaderboard` on the HTTP port | **`401 Not Authorized`**, no `WWW-Authenticate` header |
| ✅ 2026-09-28 | the same on the TLS port | `401 Not Authorized` |
| ✅ 2026-09-28 | WebSocket upgrade on `/` | `404` (unknown path; the panel paths are `/panel/<Panel>/<id>`, see doc 04) |
| ✅ 2026-10-13 | `GET /web-api/v1/gateway` on the HTTP port, no credentials of any kind | **`200`** with the gateway JSON |
| ✅ 2026-10-13 | `GET /web-api/v1/leaderboard` on the HTTP port, no credentials | **`200`** (24 KB JSON) |
| ✅ 2026-10-13 | `GET /web-api/v1/gateway` on the TLS port (`-k`), no credentials | **`200`** |

Both days the client was running and logged in to Battle.net on the same PC. The requests were plain
`curl` / PowerShell GETs with no cookies, headers or tokens.

## What the client contains 🔎

- The server code is in `ClientSdk.dll`: `Not Authorized`, `web-api`, `web-api/(.*)`, `GET`, `POST`,
  `Game returned error`.
- An authentication call `Authenticationservice.OutBound.VerifyWebCredentials` and the protobuf message
  `bnet.protocol.authentication.v1.VerifyWebCredentialsRequest`: the client has a path where a **Battle.net web
  credential is verified with Blizzard**. bw-web-api (`src/bw-connection.ts`) sends no credentials at all.

## What this means (as far as known)

- On 2026-09-28 the local REST API refused unauthenticated calls; on 2026-10-13 the same calls succeeded with no
  credentials. **Why it changed is UNCONFIRMED.** Candidates, none tested:
  - the check depends on session state (for example, it passes once the client has verified its own web
    credential during that session, or only on certain screens);
  - a client or server update between the two dates relaxed it;
  - the September session was in a state where the check failed.
- The 401 carried no `WWW-Authenticate` header, so the server does not say what it wants.
- No public write-up of this credential check was found (September 2026).
- Producing or replaying a Battle.net credential yourself means talking to Blizzard's authentication service on
  an account's behalf. That was **not** attempted, and this repository does not cover it.

## Practical advice

- Try the route first. If you get `401`, note the client state (screen, how long since login) and try again later
  rather than trying to forge a credential.
- Use `/web-api/` for every path from bw-web-api.
