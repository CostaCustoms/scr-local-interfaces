# 07 — Replay files (`.rep`)

Offline file format notes, checked with [`tools/rep_cmds.py`](../tools/rep_cmds.py) ✅ 2026-10-02: every one of
2,622 replays in one local replay folder loaded, from 2009–2010 classic (1.16) files to 2026 SC:R autosaves,
and the fully decoded ones had **0 unknown command types**. The format is long known in the community (BWAPI,
replay parsers); this page records what was verified.

## Container

A replay is a sequence of **sections**:

```
section := u32 checksum, u32 chunkCount, chunkCount × (u32 length, data)
```

Each chunk decompresses to at most 8,192 bytes; a chunk whose stored length equals the expected decompressed size
is stored raw.

| | Classic 1.16 | SC:R (1.18+) |
|---|---|---|
| Replay id (first section, 4 bytes) | `reRS` | `seRS` |
| Chunk compression | PKWARE DCL "implode" | zlib (`78 9C …`) |
| After the id section | the header section | **one raw u32**, then the header section. The u32 is the file offset of SC:R's extra sections (`SKIN`, `LMTS`, `BFIX`, `CCLR`, `GCFG`) |
| Header | 0x279 bytes | same |
| Commands | u32 length section, then the command section | same; **an empty command stream has no section at all** ✅ (seen on games with computers only or very short games) |
| Then | map data (u32 length + section) | map data + the extra sections |

## Header (0x279 bytes, file-format offsets)

| Offset | Size | Field |
|---|---|---|
| 1 | u32 | Frame count (game length; ~23.81 frames per second at Fastest) |
| 0x18 | string | Game name |
| 0x48 | string | Host name |
| 0x61 | string (≤ 26) | Map name |
| 0xA1 + 36·i, i = 0…11 | 36 bytes | Player record |

Player record (36 bytes):

| Offset | Size | Field |
|---|---|---|
| 0 | u16 | Slot |
| 4 | u8 | Player id — the id used by the command stream (not the slot) |
| 8 | u8 | Type (0 = empty; 2 = human in every human record checked) |
| 9 | u8 | Race: 0 Zerg, 1 Terran, 2 Protoss, 6 Random (a Random player shows the resolved race) |
| 10 | u8 | Team (Top vs Bottom: 1 = Top, 2 = Bottom) |
| 11 | 25 bytes | Name (UTF-8, zero-terminated) |

## Command stream

```
block   := u32 frame, u8 blockLength, blockLength bytes of commands
command := u8 playerId, u8 type, arguments (length depends on type)
```

- Classic replays put commands on latency-multiple frames (F15, F20, F30 …); SC:R frames are exact.
- If a type is unknown, skip the rest of the block: the block length keeps the reader in sync.

### Unit tags

| Format | Size | Value |
|---|---|---|
| Classic | u16 | `(uniq << 11) \| (index + 1)` — up to 1,700 units |
| SC:R | u32 | `(uniq << 13) \| (index + 1)` — up to 3,400 units; the high half is not always 0 |

`0` = no unit.

### Command types that differ between the formats

Only the commands that carry unit tags changed:

| Command | Classic | SC:R |
|---|---|---|
| Select / Shift-select / Shift-deselect | `0x09` / `0x0A` / `0x0B`: count + count × u16 tag | `0x63` / `0x64` / `0x65`: count + count × u32 tag |
| Right-click | `0x14`: x u16, y u16, tag u16, unit type u16, queued u8 (9 bytes) | `0x60`: same with a u32 tag (11 bytes) |
| Targeted order | `0x15`: x, y, tag u16, unit type, order u8, queued (10) | `0x61`: same with a u32 tag (12) |
| Unload one | `0x29`: tag u16 | `0x62`: tag u32 |

All other command types are identical in both. The full type → name → argument-length table is in
`rep_cmds.py` (`NAME`, `LEN`); a few useful ones:

| Type | Name | Notes |
|---|---|---|
| `0x57` | LeaveGame | Its frame is when that player left ✅ 2026-10-04 (used to time a leaver) |
| `0x5C` | Chat | 81 bytes: a slot byte + zero-terminated text |
| `0x58` | MinimapPing | |
| `0x0F` | GameSpeed | |
| `0x10` / `0x11` | Pause / Resume | |
| `0x37` | Sync | |
| `0x3C` | StartGame | |

Unit, tech and upgrade ids in the arguments follow the community (BWAPI) enumerations; `rep_cmds.py` carries
name tables for printing.

## Using `rep_cmds.py`

```
python tools/rep_cmds.py <file.rep>                      # header, players, command counts
python tools/rep_cmds.py <file.rep> --player NAME        # counts for one player
python tools/rep_cmds.py <file.rep> --leavers            # who left, and when
python tools/rep_cmds.py <file.rep> --dump 50            # first 50 commands, decoded
```

Pure Python 3, standard library only. The classic decompressor is a port of Mark Adler's `blast.c` (zlib-style
license; the notice is in the file).
