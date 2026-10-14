# Panels

One page per panel. Envelope, routing and the panel id are in [../04-ui-panel-sockets.md](../04-ui-panel-sockets.md).
"IN" = game → page (what an attached socket receives). "OUT" = page → game (requests the page sends).

| Panel | Screen | Live socket seen | Page |
|---|---|---|---|
| `ChatPanelHDAd` | Battle.net channel (chat + ad) | ✅ | [ChatPanelHDAd.md](ChatPanelHDAd.md) |
| `ParticipantsPanel` | Friends list | ✅ | [ParticipantsPanel.md](ParticipantsPanel.md) |
| `GameSearchPanel` | Battle.net Join: custom games list | ✅ 2026-10-13 | [GameSearchPanel.md](GameSearchPanel.md) |
| `GameSearchMapInfoPanel` | Battle.net Join: selected game's details | 📄 only | [GameSearchMapInfoPanel.md](GameSearchMapInfoPanel.md) |
| `GameCreatePanel` | Battle.net Create Game | ✅ | [GameCreatePanel.md](GameCreatePanel.md) |
| `MapBrowserPanel` | Map / file browser list | 📄 only | [MapBrowserPanel.md](MapBrowserPanel.md) |
| `MapBrowserInfoPanel` | Map info pane (Create, map browser) | ✅ (LAN Create) | [MapBrowserInfoPanel.md](MapBrowserInfoPanel.md) |
| `GameLobbyPanel` | Game lobby (Battle.net and LAN) | ✅ | [GameLobbyPanel.md](GameLobbyPanel.md) |
| `PasswordPanel` | Password prompt | 📄 only | [PasswordPanel.md](PasswordPanel.md) |
| `ConnectionSelectionPanel` | Select Connection list | not seen live | [ConnectionSelectionPanel.md](ConnectionSelectionPanel.md) |
| `LANProtocolSelectionPanel` | Select Connection: LAN protocol | ✅ 2026-10-03 | [LANProtocolSelectionPanel.md](LANProtocolSelectionPanel.md) |
| `RegistrySelectionPanel` | LAN id (Registry) selection | refused on the LAN Registry screen | [RegistrySelectionPanel.md](RegistrySelectionPanel.md) |

Other panel names seen taking a socket, without a page here: `GameLobbyChatPanel` (lobby chat line; seen as
the origin of relayed requests, 2026-10-04), `GatewayPanel` (Select Connection), `MainMenuHDAdPanel` (main
menu) ✅ 2026-10-03.

Every page also has the shared requests listed in
[04-ui-panel-sockets.md](../04-ui-panel-sockets.md#what-a-page-can-send-on-any-screen-), and most receive
`GetStrings.response {strings}` after asking for their strings on connect. Those are not repeated per page.
