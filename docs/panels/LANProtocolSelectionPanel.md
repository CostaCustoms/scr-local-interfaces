# LANProtocolSelectionPanel — LAN protocol choice

**Live when:** on Select Connection ✅ 2026-10-03 (together with `GatewayPanel`).

## IN (game → page) 📄

| Endpoint | Data | Page use |
|---|---|---|
| `SetProtocols` | `{protocols: [{id, ...}]}` | Fills the list and selects the first entry |

## OUT (page → game) 📄

| Endpoint | Data | When |
|---|---|---|
| `SetSelectedLanProtocol` | `{protocolId: <int>}` | A row is selected (also for the first row on arrival) |
| `Enter` | none | Double-click on a row. Probably acts as Ok: **UNCONFIRMED**, not tried |
