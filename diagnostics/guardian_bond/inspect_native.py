"""Read installed IL2CPP method map and disassemble selected game methods."""
import struct
import pathlib
import sys
import re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

ROOT = pathlib.Path(__file__).resolve().parent
GAME = pathlib.Path(r'C:\Program Files (x86)\Steam\steamapps\common\SpiritVale')
data = (GAME / 'BepInEx/interop/MethodAddressToToken.db').read_bytes()
magic, version, count, n, offset = struct.unpack_from('<5i', data)
pos = 20
assemblies = []
for _ in range(count):
    length = shift = 0
    while True:
        b = data[pos]
        pos += 1
        length |= (b & 127) << shift
        if b < 128:
            break
        shift += 7
    assemblies.append(data[pos:pos+length].decode())
    pos += length
names = {}
for line in (ROOT / 'methods.tsv').read_text(encoding='utf-8-sig').splitlines():
    token, name = line.split('\t', 1)
    names[int(token)] = name
ptrs = struct.unpack_from(f'<{n}Q', data, offset)
mapped = {}
for i, addr in enumerate(ptrs):
    token, assembly = struct.unpack_from('<2i', data, offset + n*8 + i*8)
    if assemblies[assembly].split(',')[0] == 'Assembly-CSharp':
        mapped[addr] = names.get(token, hex(token))
pe = pefile.PE(str(GAME / 'GameAssembly.dll'), fast_load=True)
base = pe.OPTIONAL_HEADER.ImageBase
cs = Cs(CS_ARCH_X86, CS_MODE_64)
pattern = re.compile(sys.argv[1])
for addr, name in mapped.items():
    if not pattern.search(name):
        continue
    end = min((p for p in ptrs if p > addr), default=addr+0x2000)
    print(f'\n{name} RVA={addr:#x}')
    for ins in cs.disasm(pe.get_data(addr, min(end-addr, 30000)), addr):
        desc = ''
        if ins.mnemonic in ('call', 'jmp') and ins.op_str.startswith('0x'):
            desc = mapped.get(int(ins.op_str,16), '')
        print(f'{ins.address:08x} {ins.mnemonic:8} {ins.op_str:45} {desc}')
