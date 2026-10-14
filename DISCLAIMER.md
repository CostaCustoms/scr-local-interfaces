# Disclaimer

- **Not affiliated with Blizzard.** This project is not made, endorsed, sponsored or supported by Blizzard
  Entertainment. StarCraft, StarCraft: Remastered and Battle.net are trademarks or registered trademarks of
  Blizzard Entertainment, Inc.
- **Read-only research.** These are notes from observing a normally running, logged-in client on the author's
  own PC: listening on its loopback sockets, reading its local HTTP responses, and reading the client's own UI
  scripts and binary strings for names. Nothing here modifies the game, its files or its memory.
- **No game files included.** No Blizzard code, scripts, images, data archives (CASC) or binaries are in this
  repository. Message and field names are quoted only as far as needed to describe what was observed. The tables
  in `docs/` are written from scratch.
- **Use at your own risk.** The interfaces are undocumented and can change or disappear with any patch. Talking to
  them can change what the client shows (for example, a panel can stop redrawing while an outside socket is
  attached to it; see `docs/04-ui-panel-sockets.md`). The authors accept no liability for anything that happens to
  your client, your account or your PC.
- **Respect Blizzard's terms.** Read and follow the Blizzard End User License Agreement and the Battle.net terms
  that apply to you. Do not use anything here to cheat, to automate play, to harass other players, to collect
  other players' data, or to overload Blizzard's services. A few message names in the docs describe actions
  (chatting, joining from the games list); they are documented so the protocol can be understood, and the tools
  here do not send them. Lobby host controls and requests aimed at other players' games are deliberately left out.
- **Privacy.** Samples are scrubbed: player names, account names, ids, passwords, addresses and distances are
  replaced. If you capture your own data, scrub it the same way before you share it — friend presence objects,
  for instance, carry the name **and password** of the game a friend is in.
