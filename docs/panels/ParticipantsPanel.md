# ParticipantsPanel — the friends list

**Live when:** the friends list is shown ✅ (attached from 2026-10-02). On 2026-10-04 it was **not** up on the
plain channel screen, so do not count on it there.

The page's script was read on 2026-09-28; that copy was not kept, so the request below is marked 📄 from that
reading.

## OUT (page → game)

| Endpoint | Data | Status |
|---|---|---|
| (join) | the friend row's **Join** icon / "Join Lobby" menu; uses the game name and password from the friend's presence object | 📄; clicked by hand, it joined the friend's lobby ✅ 2026-10-02 |

## IN (game → page)

| Endpoint | Data | Status |
|---|---|---|
| `OnFriendAdded` | `{friend: {...}}` | 📄 |
| `OnFriendUpdated` | `{friend: {...}}` — full field list in [06](../06-presence-friends.md#the-friend--channel-member-object-) | ✅ 2026-10-04 (seen on a lobby socket) |

A friend who is in a game lobby carries `gameName`, `gamePassword` and `gameNetwork` in this object ✅ 2026-10-04,
which is exactly what the Join icon needs.
