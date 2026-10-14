#!/usr/bin/env python3
"""rep_cmds.py - offline StarCraft replay (.rep) reader. Read-only: it only opens the file for reading.

Handles both container formats:
  * SC:R era (1.18+, id "seRS"): sections of zlib chunks; SC:R command types 0x60-0x65 carry 4-byte unit tags.
  * classic (1.16, id "reRS"): sections of PKWARE DCL "implode" chunks (decoded by the blast.c port below;
    no pip install needed).

Section = u32 checksum, u32 chunk count, then per chunk u32 length + data. A chunk is at most 8192 bytes
decompressed; a chunk whose stored length equals its decompressed size is stored raw.
File order: replay id (4) | [SC:R only: one raw u32] | header (0x279) | command length (4) | commands | map ...
Header (file offsets): frame count u32 at 1, game name at 0x18, host name at 0x48, map name at 0x61,
12 player records at 0xA1 + 36*i: u16 slot at 0, u8 player id at 4, type at 8, race at 9, team at 10, name at 11.
Command stream: blocks of (u32 frame, u8 block length), then commands (u8 player id, u8 type, arguments).

Usage:
  python rep_cmds.py <file.rep> [--player NAME] [--dump N] [--leavers]

Part of scr-local-interfaces (MIT, see LICENSE), except the PKWARE DCL decoder, which is a Python port of
blast.c and keeps its original notice:

  blast.c / blast.h
  Copyright (C) 2003, 2012, 2013 Mark Adler
  version 1.3, 24 Aug 2013

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the author be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.

  Mark Adler    madler@alumni.caltech.edu

  (Altered: this file contains a Python translation of the C original's explode routine.)
"""
import sys, struct, zlib, collections, argparse

# ---------------------------------------------------------------- PKWARE DCL explode (blast.c port)
_LITLEN = [11, 124, 8, 7, 28, 7, 188, 13, 76, 4, 10, 8, 12, 10, 12, 10, 8, 23, 8, 9, 7, 6, 7, 8, 7, 6, 55, 8, 23,
           24, 12, 11, 7, 9, 11, 12, 6, 7, 22, 5, 7, 24, 6, 11, 9, 6, 7, 22, 7, 11, 38, 7, 9, 8, 25, 11, 8, 11, 9, 12,
           8, 12, 5, 38, 5, 38, 5, 11, 7, 5, 6, 21, 6, 10, 53, 8, 7, 24, 10, 27, 44, 253, 253, 253, 252, 252, 252, 13,
           12, 45, 12, 45, 12, 61, 12, 45, 44, 173]
_LENLEN = [2, 35, 36, 53, 38, 23]
_DISTLEN = [2, 20, 53, 230, 247, 151, 248]
_BASE = [3, 2, 4, 5, 6, 7, 8, 9, 10, 12, 16, 24, 40, 72, 136, 264]
_EXTRA = [0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8]
_MAXBITS = 13

def _construct(rep):
    length = []
    for b in rep:
        length += [b & 15] * ((b >> 4) + 1)
    count = [0] * (_MAXBITS + 1)
    for l in length: count[l] += 1
    offs = [0] * (_MAXBITS + 1)
    for l in range(1, _MAXBITS): offs[l + 1] = offs[l] + count[l]
    symbol = [0] * len(length)
    for s, l in enumerate(length):
        if l: symbol[offs[l]] = s; offs[l] += 1
    return count, symbol

_LITCODE, _LENCODE, _DISTCODE = _construct(_LITLEN), _construct(_LENLEN), _construct(_DISTLEN)

def explode(data):
    pos = 0; bitbuf = 0; bitcnt = 0; out = bytearray()
    def bits(n):
        nonlocal pos, bitbuf, bitcnt
        while bitcnt < n:
            if pos >= len(data): raise ValueError('explode: out of input')
            bitbuf |= data[pos] << bitcnt; pos += 1; bitcnt += 8
        v = bitbuf & ((1 << n) - 1); bitbuf >>= n; bitcnt -= n
        return v
    def decode(h):
        count, symbol = h
        code = first = index = 0
        for l in range(1, _MAXBITS + 1):
            code |= bits(1) ^ 1
            c = count[l]
            if code < first + c: return symbol[index + code - first]
            index += c; first += c; first <<= 1; code <<= 1
        raise ValueError('explode: bad code')
    lit = bits(8); dict_ = bits(8)
    if lit > 1 or not 4 <= dict_ <= 6: raise ValueError(f'explode: bad header {lit} {dict_}')
    while True:
        if bits(1):
            sym = decode(_LENCODE)
            ln = _BASE[sym] + bits(_EXTRA[sym])
            if ln == 519: break
            sh = 2 if ln == 2 else dict_
            dist = (decode(_DISTCODE) << sh) + bits(sh) + 1
            if dist > len(out): raise ValueError('explode: distance too far')
            for _ in range(ln): out.append(out[-dist])
        else:
            out.append(decode(_LITCODE) if lit else bits(8))
    return bytes(out)

# ---------------------------------------------------------------- sections
def read_section(f, size):
    chk, n = struct.unpack('<II', f.read(8))
    out = bytearray()
    for _ in range(n):
        ln = struct.unpack('<I', f.read(4))[0]
        d = f.read(ln)
        want = min(8192, size - len(out))
        if ln == want: out += d                       # stored raw
        elif d[:1] == b'\x78': out += zlib.decompress(d)
        else: out += explode(d)
    return bytes(out[:size])

def load(path):
    with open(path, 'rb') as f:
        rid = read_section(f, 4)
        modern = rid == b'seRS'
        if modern: f.read(4)                          # SC:R: raw u32 before the header section
        elif rid != b'reRS': raise ValueError(f'unknown replay id {rid!r}')
        hdr = read_section(f, 0x279)
        cmdlen = struct.unpack('<I', read_section(f, 4))[0]
        cmds = read_section(f, cmdlen) if cmdlen else b""   # an empty stream has no section at all
    return rid.decode(), hdr, cmds

RACES = {0: 'Z', 1: 'T', 2: 'P', 6: 'R'}
def players(hdr):
    pl = []
    for i in range(12):
        r = hdr[0xA1 + 36 * i: 0xA1 + 36 * (i + 1)]
        slot, = struct.unpack_from('<H', r, 0); pid = r[4]; typ, race, team = r[8], r[9], r[10]
        name = r[11:36].split(b'\0')[0].decode('utf-8', 'replace')
        if typ and name: pl.append(dict(i=i, slot=slot, id=pid, type=typ, race=RACES.get(race, race), team=team, name=name))
    return pl

# ---------------------------------------------------------------- names (BWAPI ids)
UNIT = {0:'Marine',1:'Ghost',2:'Vulture',3:'Goliath',5:'SiegeTank',7:'SCV',8:'Wraith',9:'ScienceVessel',11:'Dropship',
 12:'Battlecruiser',13:'SpiderMine',14:'NuclearMissile',30:'SiegeTankSieged',32:'Firebat',33:'ScannerSweep',34:'Medic',
 35:'Larva',36:'Egg',37:'Zergling',38:'Hydralisk',39:'Ultralisk',40:'Broodling',41:'Drone',42:'Overlord',43:'Mutalisk',
 44:'Guardian',45:'Queen',46:'Defiler',47:'Scourge',50:'InfestedTerran',58:'Valkyrie',59:'Cocoon',60:'Corsair',
 61:'DarkTemplar',62:'Devourer',63:'DarkArchon',64:'Probe',65:'Zealot',66:'Dragoon',67:'HighTemplar',68:'Archon',
 69:'Shuttle',70:'Scout',71:'Arbiter',72:'Carrier',73:'Interceptor',83:'Reaver',84:'Observer',85:'Scarab',97:'LurkerEgg',
 103:'Lurker',106:'CommandCenter',107:'ComsatStation',108:'NuclearSilo',109:'SupplyDepot',110:'Refinery',111:'Barracks',
 112:'Academy',113:'Factory',114:'Starport',115:'ControlTower',116:'ScienceFacility',117:'CovertOps',118:'PhysicsLab',
 120:'MachineShop',122:'EngineeringBay',123:'Armory',124:'MissileTurret',125:'Bunker',130:'InfestedCC',131:'Hatchery',
 132:'Lair',133:'Hive',134:'NydusCanal',135:'HydraliskDen',136:'DefilerMound',137:'GreaterSpire',138:'QueensNest',
 139:'EvolutionChamber',140:'UltraliskCavern',141:'Spire',142:'SpawningPool',143:'CreepColony',144:'SporeColony',
 146:'SunkenColony',149:'Extractor',154:'Nexus',155:'RoboticsFacility',156:'Pylon',157:'Assimilator',159:'Observatory',
 160:'Gateway',162:'PhotonCannon',163:'CitadelOfAdun',164:'CyberneticsCore',165:'TemplarArchives',166:'Forge',
 167:'Stargate',169:'FleetBeacon',170:'ArbiterTribunal',171:'RoboticsSupportBay',172:'ShieldBattery',
 176:'Mineral1',177:'Mineral2',178:'Mineral3',188:'VespeneGeyser',228:'None'}
TECH = ['StimPacks','Lockdown','EMP','SpiderMines','ScannerSweep','TankSiegeMode','DefensiveMatrix','Irradiate',
 'YamatoGun','CloakingField','PersonnelCloaking','Burrowing','Infestation','SpawnBroodlings','DarkSwarm','Plague',
 'Consume','Ensnare','Parasite','PsionicStorm','Hallucination','Recall','StasisField','ArchonWarp','Restoration',
 'DisruptionWeb','?26','MindControl','DarkArchonMeld','Feedback','OpticalFlare','Maelstrom','LurkerAspect','?33','Healing']
UPG = ['TerranInfantryArmor','TerranVehiclePlating','TerranShipPlating','ZergCarapace','ZergFlyerCarapace',
 'ProtossGroundArmor','ProtossAirArmor','TerranInfantryWeapons','TerranVehicleWeapons','TerranShipWeapons',
 'ZergMeleeAttacks','ZergMissileAttacks','ZergFlyerAttacks','ProtossGroundWeapons','ProtossAirWeapons',
 'ProtossPlasmaShields','U238Shells','IonThrusters','?18','TitanReactor','OcularImplants','MoebiusReactor',
 'ApolloReactor','ColossusReactor','VentralSacs','Antennae','PneumatizedCarapace','MetabolicBoost','AdrenalGlands',
 'MuscularAugments','GroovedSpines','GameteMeiosis','MetasynapticNode','SingularityCharge','LegEnhancements',
 'ScarabDamage','ReaverCapacity','GraviticDrive','SensorArray','GraviticBoosters','KhaydarinAmulet','ApialSensors',
 'GraviticThrusters','CarrierCapacity','KhaydarinCore','?45','?46','ArgusJewel','?48','ArgusTalisman','?50',
 'CaduceusReactor','ChitinousPlating','AnabolicSynthesis','CharonBoosters']
ORDER = {0x06:'Move',0x08:'Attack1',0x0A:'AttackUnit',0x0E:'AttackMove',0x13:'TowerAttack',0x19:'DroneStartBuild',
 0x1B:'CastInfestation',0x1E:'PlaceBuilding',0x1F:'PlaceProtossBuilding',0x22:'Repair',0x24:'PlaceAddon',
 0x27:'RallyPointUnit',0x28:'RallyPointTile',0x2E:'BuildNydusExit',0x31:'Follow',0x44:'ShieldBattery(68)',
 0x45:'?69',0x47:'BuildingLand',0x4F:'Harvest1',0x5C:'EnterTransport',0x6F:'Unload',0x70:'MoveUnload',
 0x71:'FireYamatoGun',0x73:'CastLockdown',0x77:'CastDarkSwarm',0x78:'CastParasite',0x79:'CastSpawnBroodlings',
 0x7A:'CastEMPShockwave',0x7E:'NukePaint',0x80:'CastNuclearStrike',0x84:'PlaceMine',0x85:'RightClickAction',
 0x89:'CastRecall',0x8B:'CastScannerSweep',0x8D:'CastDefensiveMatrix',0x8E:'CastPsionicStorm',0x8F:'CastIrradiate',
 0x90:'CastPlague',0x91:'CastConsume',0x92:'CastEnsnare',0x93:'CastStasisField',0x94:'CastHallucination',
 0x98:'Patrol',0xAF:'Medic?',0xB0:'MedicHeal',0xB4:'CastRestoration',0xB5:'CastDisruptionWeb',0xB6:'CastMindControl',
 0xB8:'CastFeedback',0xB9:'CastOpticalFlare',0xBA:'CastMaelstrom',0x6B:'HoldPosition'}
def un(t): return UNIT.get(t, f'unit{t}')

# ---------------------------------------------------------------- commands
# fixed argument lengths (bytes after the type byte); 'S2' = count + count*u16 tags, 'S4' = count + count*4-byte tags
LEN = {0x05:0,0x08:0,0x09:'S2',0x0A:'S2',0x0B:'S2',0x0C:7,0x0D:2,0x0E:4,0x0F:1,0x10:0,0x11:0,0x12:4,0x13:2,0x14:9,
 0x15:10,0x18:0,0x19:0,0x1A:1,0x1B:0,0x1C:0,0x1D:0,0x1E:1,0x1F:2,0x20:2,0x21:1,0x22:1,0x23:2,0x25:1,0x26:1,0x27:0,
 0x28:1,0x29:2,0x2A:0,0x2B:1,0x2C:1,0x2D:1,0x2E:0,0x2F:4,0x30:1,0x31:0,0x32:1,0x33:0,0x34:0,0x35:2,0x36:0,0x37:6,
 0x38:0,0x39:0,0x3A:1,0x3B:1,0x3C:0,0x3D:1,0x3E:5,0x3F:7,0x40:17,0x41:2,0x42:1,0x43:1,0x44:2,0x45:2,0x48:12,0x54:0,
 0x55:1,0x56:9,0x57:1,0x58:4,0x5A:0,0x5B:0,0x5C:81,0x60:11,0x61:12,0x62:4,0x63:'S4',0x64:'S4',0x65:'S4'}
NAME = {0x05:'KeepAlive',0x08:'Restart',0x09:'Select',0x0A:'ShiftSelect',0x0B:'ShiftDeselect',0x0C:'Build',0x0D:'Vision',
 0x0E:'Alliance',0x0F:'GameSpeed',0x10:'Pause',0x11:'Resume',0x12:'Cheat',0x13:'Hotkey',0x14:'RightClick',
 0x15:'TargetedOrder',0x18:'CancelBuild',0x19:'CancelMorph',0x1A:'Stop',0x1B:'CarrierStop',0x1C:'ReaverStop',
 0x1D:'OrderNothing',0x1E:'ReturnCargo',0x1F:'Train',0x20:'CancelTrain',0x21:'Cloak',0x22:'Decloak',0x23:'UnitMorph',
 0x25:'Unsiege',0x26:'Siege',0x27:'TrainFighter',0x28:'UnloadAll',0x29:'Unload',0x2A:'MergeArchon',0x2B:'HoldPosition',
 0x2C:'Burrow',0x2D:'Unburrow',0x2E:'CancelNuke',0x2F:'Lift',0x30:'Tech',0x31:'CancelTech',0x32:'Upgrade',
 0x33:'CancelUpgrade',0x34:'CancelAddon',0x35:'BuildingMorph',0x36:'Stim',0x37:'Sync',0x3C:'StartGame',
 0x55:'Latency',0x56:'ReplaySpeed',0x57:'LeaveGame',0x58:'MinimapPing',0x5A:'MergeDarkArchon',0x5C:'Chat',
 0x60:'RightClick(SCR)',0x61:'TargetedOrder(SCR)',0x62:'Unload(SCR)',0x63:'Select(SCR)',0x64:'ShiftSelect(SCR)',
 0x65:'ShiftDeselect(SCR)'}

# unit tags: classic u16 = (uniq << 11) | (index + 1) (1700 units); SC:R u32 = (uniq << 13) | (index + 1) (3400 units).
# Printed as #index u uniq; 0 = no unit.
def tag11(v): return 'none' if v == 0 else f'#{(v & 0x7FF) - 1}u{v >> 11}'
def tag13(v): return 'none' if v == 0 else f'#{(v & 0x1FFF) - 1}u{v >> 13}'

def meaning(t, a):
    u16 = lambda o: struct.unpack_from('<H', a, o)[0]
    u32 = lambda o: struct.unpack_from('<I', a, o)[0]
    if t in (0x09, 0x0A, 0x0B): return f'n={a[0]} units=' + ','.join(tag11(u16(1+2*i)) for i in range(a[0]))
    if t in (0x63, 0x64, 0x65): return f'n={a[0]} units=' + ','.join(tag13(u32(1+4*i)) for i in range(a[0]))
    if t == 0x0C: return f'order 0x{a[0]:02X} {ORDER.get(a[0],"?")} tile ({u16(1)},{u16(3)}) {un(u16(5))}'
    if t == 0x1F: return f'{un(u16(0))}'
    if t in (0x23, 0x35): return f'-> {un(u16(0))}'
    if t == 0x30: return f'{TECH[a[0]] if a[0] < len(TECH) else a[0]}'
    if t == 0x32: return f'{UPG[a[0]] if a[0] < len(UPG) else a[0]}'
    if t == 0x13: return f'{["assign","select","add"][a[0]] if a[0] < 3 else a[0]} group {a[1]}'
    if t == 0x14: return f'({u16(0)},{u16(2)}) target {tag11(u16(4))} {un(u16(6))} queued={a[8]}'
    if t == 0x15: return f'({u16(0)},{u16(2)}) target {tag11(u16(4))} {un(u16(6))} order 0x{a[8]:02X} {ORDER.get(a[8],"?")} queued={a[9]}'
    if t == 0x60: return f'({u16(0)},{u16(2)}) target {tag13(u32(4))} {un(u16(8))} queued={a[10]}'
    if t == 0x61: return f'({u16(0)},{u16(2)}) target {tag13(u32(4))} {un(u16(8))} order 0x{a[10]:02X} {ORDER.get(a[10],"?")} queued={a[11]}'
    if t in (0x29,): return f'unit {tag11(u16(0))}'
    if t == 0x62: return f'unit {tag13(u32(0))}'
    if t == 0x20: return f'slot/tag {u16(0):04X}'
    if t in (0x2C, 0x2D, 0x2B, 0x1A, 0x1E, 0x25, 0x26, 0x21, 0x22, 0x28): return f'queued/flag={a[0]}'
    if t == 0x5C: return 'chat ' + a[1:].split(b'\0')[0].decode('utf-8', 'replace')
    return ''

def commands(cmds):
    """yield (frame, player, type, argbytes); stops a block on an unknown type (block length keeps us in sync)"""
    pos = 0; n = len(cmds); unknown = collections.Counter()
    while pos + 5 <= n:
        frame, blen = struct.unpack_from('<IB', cmds, pos); pos += 5
        end = pos + blen
        while pos < end:
            pl, t = cmds[pos], cmds[pos + 1]; p = pos + 2
            L = LEN.get(t)
            if L == 'S2': L = 1 + 2 * cmds[p]
            elif L == 'S4': L = 1 + 4 * cmds[p]
            if L is None or p + L > end:
                unknown[t] += 1; break
            yield frame, pl, t, cmds[p:p + L]
            pos = p + L
        pos = end
    commands.unknown = unknown

def main():
    ap = argparse.ArgumentParser(description='Offline StarCraft replay reader (read-only).')
    ap.add_argument('rep', help='path to a .rep file')
    ap.add_argument('--player', default=None, help='only count / dump this player name (default: everyone)')
    ap.add_argument('--dump', type=int, default=0, help='print the first N commands')
    ap.add_argument('--leavers', action='store_true', help='list LeaveGame (0x57) commands with their frame')
    a = ap.parse_args()
    rid, hdr, cmds = load(a.rep)
    frames = struct.unpack_from('<I', hdr, 1)[0]
    mapn = hdr[0x61:0x61 + 26].split(b'\0')[0].decode('utf-8', 'replace')
    pl = players(hdr)
    print(f'file {a.rep}\n  id {rid} ({"SC:R zlib" if rid == "seRS" else "classic PKWARE"}), frames {frames} '
          f'({frames / 23.81 / 60:.1f} min at Fastest), map {mapn!r}, command bytes {len(cmds)}')
    for p in pl:
        print(f'  player i={p["i"]} slot={p["slot"]} id={p["id"]} type={p["type"]} race={p["race"]} team={p["team"]} {p["name"]!r}')
    names = {p['id']: p['name'] for p in pl}
    allc = list(commands(cmds))
    print(f'  commands parsed: {len(allc)}; unknown types (block abandoned): {dict(commands.unknown)}')
    byp = collections.Counter(c[1] for c in allc)
    print('  commands per player id: ' + ', '.join(f'{k} {names.get(k, "?")!r}: {v}' for k, v in sorted(byp.items())))
    if a.player is not None:
        ids = [p['id'] for p in pl if p['name'] == a.player]
        if not ids:
            sys.exit(f'no player named {a.player!r} in this replay')
        sel, who = [c for c in allc if c[1] in ids], a.player
    else:
        sel, who = allc, 'all players'
    cnt = collections.Counter(c[2] for c in sel)
    print(f'\n== {who}: count per command type')
    for t, k in sorted(cnt.items()):
        print(f'  0x{t:02X} {NAME.get(t, "?"):22} {k}')
    if a.leavers:
        print('\n== LeaveGame commands (frame m:ss | player)')
        for f, p, t, arg in allc:
            if t == 0x57:
                print(f'  F{f:6} {f // 23.81 // 60:2.0f}:{f / 23.81 % 60:02.0f} | {p} {names.get(p, "?")!r}')
    if a.dump:
        print(f'\n== first {a.dump} commands of {who} (frame | player | raw | meaning)')
        for f, p, t, arg in sel[:a.dump]:
            print(f'  F{f:6} | {p:2} | {t:02X} {arg.hex(" ")} | {NAME.get(t, "?")} {meaning(t, arg)}')


if __name__ == '__main__':
    main()
