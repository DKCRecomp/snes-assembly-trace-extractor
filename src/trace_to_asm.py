#!/usr/bin/env python3

"""
==================================
DKC1 — Log tracer converter to ASM
==================================
Read txt files from folder traces/
Generate asm files in src/Bank_XX/
==================================
"""

import re
import sys
from pathlib import Path
from collections import Counter, OrderedDict, defaultdict
import data

# /-----/ Globals /-----/

TRACES_EXTENSION = "txt"

# /-----/ Paths /-----/

REPO_ROOT  = Path(__file__).parent.parent # dkc-decompiled-code/

TRACES_DIR = "traces"
TRACES_PATH = REPO_ROOT / TRACES_DIR

CODE_DIR = "code"
CODE_PATH = REPO_ROOT / CODE_DIR

def load_traces():
    """Read .txt from traces folder and return uniques instructions."""

    files = sorted(TRACES_PATH.glob(f'*.{TRACES_EXTENSION}'))
    if not files:
        print(f"No .{TRACES_EXTENSION} found in {TRACES_PATH}")
        print(f"Export log from Mesen and place it in {TRACES_DIR}")
        sys.exit(1)

    seen   = OrderedDict()
    hits   = Counter()
    seen_s = OrderedDict()
    hits_s = Counter()

    for file in files:

        file_size = file.stat().st_size // 1024
        print(f"  - Reading {file.name} ({file_size} Ko)")

        for line in file.open(encoding='utf-8', errors='replace'):
            line = line.rstrip()
            m = data.PAT_65816.match(line)

            if m:
                addr = m.group(1)
                hits[addr] += 1
                if addr not in seen:
                    seen[addr] = {'instr': m.group(2).strip(), 'P': m.group(6)}
                continue
            m = data.PAT_SPC700.match(line)

            if m:
                addr = m.group(1)
                hits_s[addr] += 1
                if addr not in seen_s:
                    seen_s[addr] = m.group(2).strip()

    return seen, hits, seen_s, hits_s

def comment_instr(instr, hits_addr):
    """Generate comment from a instruction."""

    mnem = instr.split()[0]
    parts = []

    # Hardware register name
    m = re.search(r'\$([0-9A-F]{4})', instr)
    if m:
        reg = int(m.group(1), 16)
        if reg in data.HARDWARE_REGISTERS:
            parts.append(data.HARDWARE_REGISTERS[reg])

    # Change 8/16 bits mode
    if mnem in ('REP', 'SEP'):
        m2 = re.search(r'#\$([0-9A-F]{2})', instr)
        if m2:
            v = int(m2.group(1), 16)
            taille = '16' if mnem == 'REP' else '8'
            if v & 0x20: parts.append(f'A={taille}b')
            if v & 0x10: parts.append(f'X/Y={taille}b')

    # Loop detected
    if hits_addr > 1:
        parts.append(f'loop x{hits_addr} in traces')

    return ('  ; ' + ', '.join(parts)) if parts else ''

def write_bank(bank_id, adresses, seen, hits):
    """Write code/Bank_XX/Bank_XX.asm"""

    folder_path = CODE_PATH / f'Bank_{bank_id}'
    folder_path.mkdir(parents=True, exist_ok=True)
    file = folder_path / f'Bank_{bank_id}.asm'

    content = [
        f'; DKC1 (SNES) — Bank ${bank_id}',
        f'; {len(adresses)} uniques instructions',
        f'; Generated from {TRACES_DIR} — Do not modify it',
        f'; To write comments: Bank_{bank_id}_annotated.asm in the folder',
        '',
    ]

    prev = None
    for addr in adresses:
        addr_int = int(addr, 16)
        d = seen[addr]

        if prev is not None and addr_int > prev + 8:
            content.append(f'')
            content.append(f'; --- gap ${addr_int - prev:04X} bytes (non traced) ---')
            content.append(f'')

        com = comment_instr(d['instr'], hits[addr])
        content.append(f'CODE_{addr}:  {d["instr"]:<36}{com}')
        prev = addr_int

    file.write_text('\n'.join(content) + '\n')
    return file

def write_spc(seen_s, hits_s):
    """Write code/SPC700/SPC700.asm"""

    folder = CODE_PATH / 'SPC700'
    folder.mkdir(exist_ok=True)
    file = folder / 'SPC700.asm'

    content = [
        '; DKC1 — SPC700 (CPU audio Sony)',
        '; Boot ROM standard, do not modify',
        '',
    ]
    for addr, instr in seen_s.items():
        c = hits_s[addr]
        com = f'  ; loop x{c} in traces' if c > 1 else ''
        content.append(f'SPC_{addr}:  {instr:<30}{com}')

    file.write_text('\n'.join(content) + '\n')
    return file

def trace_to_asm():

    print(f'Reading in {TRACES_PATH}')
    seen, hits, seen_s, hits_s = load_traces()

    total_lines_nb   = sum(hits.values())
    unique_lines_nb = len(seen)
    redond_lines_nb  = total_lines_nb - unique_lines_nb
    banks   = sorted(set(a[:2] for a in seen))

    # /------------------------------/

    print(f'')
    print(f'Results :')
    print(f'    65c816  : {total_lines_nb} lines -> {unique_lines_nb} uniques ({redond_lines_nb} double code deleted)')
    print(f'    SPC700  : {sum(hits_s.values())} lines -> {len(seen_s)} uniques')
    print(f'    Banks : {banks}')

    # /------------------------------/

    print(f'')
    print(f'Writing in {CODE_DIR}')

    by_bank = defaultdict(list)
    for addr in seen:
        by_bank[addr[:2]].append(addr)

    for bank, addrs in sorted(by_bank.items()):
        f = write_bank(bank, addrs, seen, hits)
        print(f'    -> {f.relative_to(REPO_ROOT)}  ({len(addrs)} instrs)')

    if seen_s:
        f = write_spc(seen_s, hits_s)
        print(f'    -> {f.relative_to(REPO_ROOT)}  ({len(seen_s)} instrs)')


def main():
    print('================================================================')
    print(f'Starting cleaning and exporting code from : {TRACES_DIR}')
    print('================================================================')

    trace_to_asm()

    print('==================================')
    print(f'Finished')
    print('==================================')

if __name__ == '__main__':
    main()
