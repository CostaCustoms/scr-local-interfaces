# ChatPanelHDAd — Battle.net channel (chat + ad)

**Live when:** on the Battle.net channel (chat) screen ✅ (from 2026-09-28). Its socket being accepted is a
reliable sign that the channel screen is up ✅.

No copy of this page's script was kept for these notes; everything below comes from live use.

## OUT (page → game)

| Endpoint | Data | Status |
|---|---|---|
| `SendChatMessage` | `{message, target: "CurrentBattlenetChannel"}` — a line in the current channel | ✅ 2026-09-28 |
| `SendWhisper` | `{name, message}` — a whisper to that player | ✅ 2026-09-28 (it reached the player) |

Battle.net drops a chat line identical to the previous one ✅ 2026-09-28.

## IN (game → page)

- App broadcasts (`OnMessage`, friend and channel-member updates) are expected here as on every panel socket;
  confirmed on the lobby and Create sockets ✅ 2026-10-04, **UNCONFIRMED** on this one.
- The channel page keeps its own chat history by saving the **whole log as one JSON string** with
  `LocalStorageSetValue {key: "chatLogs", value: "<JSON text>"}` on every chat change ✅ 2026-09-28 (observed
  inside the client, not on a socket). Each entry: `{type, channel, channelName, content, sender: {name,
  battleTag, isInLobby, isInGame, ...}}`, no timestamp, no id; `type` one of `message`, `whisperInbound`,
  `friendFollow`, `info`, `joinLeave`. Lobby chat is not in this log. Because page requests are relayed to other
  sockets (doc 04, "allExceptMe"), an outside socket on this panel may receive these saves: **UNCONFIRMED**.
  [`tools/chatlog.ps1`](../../tools/chatlog.ps1) prints them if they arrive.
