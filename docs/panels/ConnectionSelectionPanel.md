# ConnectionSelectionPanel — connection list

**Live when:** not seen taking a socket ✅ 2026-10-03 (the Battle.net / LAN rows on Select Connection behaved as
native there). Everything below is 📄.

## IN (game → page) 📄

| Endpoint | Data | Page use |
|---|---|---|
| `SetConnections` | `{connections: [{id, ...}]}` | Fills the list and selects the first entry |

## OUT (page → game) 📄

| Endpoint | Data | When |
|---|---|---|
| `SetSelectedConnectionProtocol` | `{connectionId: <int>}` | A row is selected (also sent for the first row when the list arrives) |

There is no confirm request; Ok is native.
