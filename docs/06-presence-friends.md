# 06 — Presence, friends and chat

Two kinds of material here: objects actually received on panel sockets (✅), and names found in the client
binary that look related (🔎 — **UNCONFIRMED** until seen on the wire).

## App broadcasts on panel sockets ✅ 2026-10-04

The game pushes these to panel sockets regardless of which panel they belong to (seen on `GameLobbyPanel` and
`GameCreatePanel` sockets; see [04](04-ui-panel-sockets.md#routing-allexceptme)):

| Endpoint | Data |
|---|---|
| `OnMessage` | a chat / info line: `{content, channel, type, sender?}` |
| `OnFriendUpdated` | `{friend: <member object>}` |
| `OnChannelMemberUpdated` | `{channelId, channelMember: <member object>}` |
| `OnChannelMemberLeft` | `{channelId, id, channelMember: <member object>}` |

Sample: [`samples/lobby-socket_20261004.scrubbed.jsonl`](../samples/lobby-socket_20261004.scrubbed.jsonl).

### `OnMessage`

| `channel` | `type` | Example `content` | `sender` |
|---|---|---|---|
| `gameLobby` | `info` | "X has joined the game." / "X has left the game." | none |
| `gameLobby` | `message` | a lobby chat line | member object (yours has `isLocalUser: true`) |
| `legacyBattlenet` | `playerStats` | "[U.S. West] Custom Games - Wins: N, Losses: N, Disconnects: N." (shown when a player joins your lobby) | short member object |
| `legacyBattlenet` | `info` | system lines | none |
| `modernBattlenet` | `friendFollow` | "Your friend X entered a custom game called Y." / "Your friend X left a game." | none |

`channelId` values seen on member updates: `"lan"` and numeric strings (`"12"`).

### The friend / channel-member object ✅

One object family is used for `friend`, `channelMember` and `sender`. Fields seen (not all appear every time):

| Group | Fields |
|---|---|
| Identity | `id`, `name`, `rawName`, `legacyToonName`, `lanToonName`, `auroraFullName`, `fullName`, `battleTag` (`Name#1234`), `prettyBattleTag`, `GUID` (base64), `gatewayId`, `legacyChatToonId`, `lanChatToonId` |
| Relationship | `isFriend`, `canBeBefriended`, `isLocalUser`, `isOnLanSubnet` |
| Presence | `isOnline`, `availability` (`"online"`), `isAway`, `isBusy`, `inProgram`, `currentProgram`, `programId` / `program_id` (`"S1"`, `"STAR"`), `globalRichPresence` (empty string when seen), `isInLobby`, `isInGame` |
| Current game | `gameNetwork` (`"battlenet"`), `gameName`, **`gamePassword`** — present while the friend is in a game lobby |
| Channel roles | `isAdmin`, `isModerator`, `isSpeaker`, `isChannelRestricted`, `isTalkRestricted`, `isWhisperRestricted` |
| Squad | `isInSquad`, `isSquadLeader`, `isInvitePending`, `isReady`, `isAvailableForSquad` |
| Other | `attributes: [{key, value}]` (`program_id` → `"SEXP"`, `battle_tag`), `portraits: {gameIconUrl}` (`https://scrassets.classic.blizzard.com/chat-icons/...png`) |

**Privacy note ✅:** a friend's presence carries the **name and password** of the private game they are in.
That is what lets the friends list's Join icon work, and it is why captures must be scrubbed before sharing.

### Whispers

- `SendWhisper {name, message}` is the channel page's own whisper request ✅ 2026-09-28.

## Rich presence 🔎 (UNCONFIRMED)

Classes: `LocalRichPresence`, `GlobalRichPresence`, `RichPresenceManager`, `LocationField@GlobalRichPresence`,
`ILocalRichPresenceAttributeV1`. A payload key `presence`.

State names (look like the source of the `friendFollow` lines above):

```
bnet_friendFollow_enteredBattlenet          bnet_friendFollow_exitedBattlenet
bnet_friendFollow_enteredCustomGameLobby    bnet_friendFollow_exitedGameLobby
bnet_friendFollow_enteredRankedGameLobby    bnet_friendFollow_enteredStarCraft
bnet_friendFollow_enteredReplayGameLobby    bnet_friendFollow_exitedStarCraft
bnet_friendFollow_enteredSinglePlayerGameLobby
bnet_friendFollow_online                    bnet_friendFollow_offline
```

The member object's `globalRichPresence` was an empty string every time it was seen.

## Friends services 🔎 (UNCONFIRMED)

- Modern (Aurora): `AuroraFriendsService`, `AuroraFriendsMessageReceiver`, `InvitationSentSuccessNotification`,
  `InvitationSentErrorNotification`, `InvitationsUpdatedNotification`, `UpdatedNotification`.
- Legacy: `LegacyFriendsService`, `LegacyFriendsMessageReceiver`, `AddSuccessNotification` /
  `AddErrorNotification`, `RemoveSuccessNotification` / `RemoveErrorNotification`, `ConnectedNotification` /
  `DisconnectedNotification`.
- JSON keys: `friends`, `OnlineFriends`, `suggestedFriends`, `isMutualFriendship`,
  `FriendsPresenceNotifications`, `FriendsPresenceNotificationsEnabled`.
- Chat commands in the client: `/friends list`, `listAll`, `listBlizzard`, `listOnline`, `add <name>`,
  `remove <name>`, `msg <message>`, `msgAll <message>`, `on`, `off`.
- Suspected REST routes, **never seen or confirmed**: `/v1/friends/{toon}/{gateway}`,
  `/v1/friends/invitations/{toon}/{gateway}`, `/v1/friends/suggested/{toon}/{gateway}`,
  `/v1/friends/online/{toon}/{gateway}`. The live friend data above arrives over the panel sockets, so these
  may not exist.

## Chat targets

`SendChatMessage {message, target}`: `CurrentBattlenetChannel` ✅ 2026-09-28, `GameLobby` ✅ 2026-10-04
(relayed from the lobby chat page), and 🔎 `Lan`, `InGameAll`, `InGameAllies`, `InGameObservers`,
`InGameSpecificPlayer`.
