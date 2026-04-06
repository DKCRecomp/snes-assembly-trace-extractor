#!/usr/bin/env python3

"""
==================================
Log tracer converter to ASM
==================================
Read txt files from directory traces/
Generate asm files in src/Bank_XX/
==================================
"""

import re
import sys
from pathlib import Path
from collections import Counter, OrderedDict, defaultdict
import data

# /-----/ Globals /-----/

REPO_ROOT  = Path(__file__).parent.parent

# traces

TRACES_DIR = "traces"
TRACES_PATH = REPO_ROOT / TRACES_DIR
TRACES_EXTENSION = "txt"

# code banks

CODE_DIR = "code"
CODE_PATH = REPO_ROOT / CODE_DIR

def main():
    display_start()
    run()
    display_end()

def display_start():
    print('================================================================')
    print(f'            SNES Assembly Log Trace Extractor')
    print('================================================================')
    print('')

def display_end():
    print('')
    print('==================================')
    print(f'            Finished')
    print('==================================')
    print('')

def run():
    files = load_files()

    for file in files:
        trace_to_asm(file)

def load_files():
    files = sorted(TRACES_PATH.glob(f'*.{TRACES_EXTENSION}'))
    if not files:
        print(f"No .{TRACES_EXTENSION} found in {TRACES_PATH}")
        print(f"Export log from Mesen (or any emulator) and place it in {TRACES_DIR}")
        sys.exit(1)
    return files

def trace_to_asm(file):

    print(f'Reading in {TRACES_PATH}')
    seen, hits, seen_s, hits_s = load_trace(file)

    total_lines_nb   = sum(hits.values())
    unique_lines_nb = len(seen)
    redond_lines_nb  = total_lines_nb - unique_lines_nb
    banks   = sorted(set(a[:2] for a in seen))

    # /------------------------------/

    print(f'')
    print(f'Results :')
    print(f'    65C816  : {total_lines_nb} lines -> {unique_lines_nb} uniques ({redond_lines_nb} double code deleted)')
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
        print(f'    - {f.relative_to(REPO_ROOT)}  ({len(addrs)} instructions)')

    if seen_s:
        f = write_spc(seen_s, hits_s)
        print(f'    - {f.relative_to(REPO_ROOT)}  ({len(seen_s)} instructions)')

def load_trace(file):
    """Read .txt from traces directory and return uniques instructions."""

    seen   = OrderedDict()
    hits   = Counter()
    seen_s = OrderedDict()
    hits_s = Counter()

    file_size = file.stat().st_size // 1024
    print(f"  - Reading {file.name} ({file_size} Ko)")
                
    print(f"    - Creating {Path(file.name).with_suffix('')} folder")
    create_trace_folder(file.name)

    for line in file.open(encoding='utf-8', errors='replace'):
        line = line.rstrip()
        match = data.PAT_65816.match(line)

        if match:
            addr = match.group(1)
            hits[addr] += 1
            if addr not in seen:
                seen[addr] = {'instr': match.group(2).strip(), 'P': match.group(6)}
            continue

        match = data.PAT_SPC700.match(line)
        if match:
            addr = match.group(1)
            hits_s[addr] += 1
            if addr not in seen_s:
                seen_s[addr] = match.group(2).strip()
    return seen, hits, seen_s, hits_s

def create_trace_folder(file_name):

    # Remove `.txt` from file name
    global GAME_FOLDER_NAME
    GAME_FOLDER_NAME = Path(file_name).with_suffix('')

    # We update globally code path for each trace file
    global CODE_PATH 
    CODE_PATH = REPO_ROOT / CODE_DIR / GAME_FOLDER_NAME

    CODE_PATH.mkdir(parents=True, exist_ok=True)

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
            size = '16' if mnem == 'REP' else '8'
            if v & 0x20: parts.append(f'A={size}b')
            if v & 0x10: parts.append(f'X/Y={size}b')

    # Loop detected
    if hits_addr > 1:
        parts.append(f'(looped x{hits_addr} in traces)')

    return ('  ; ' + ', '.join(parts)) if parts else ''

def write_bank(bank_id, adresses, seen, hits):
    """Write code/Bank_XX/Bank_XX.asm"""

    dir_path = CODE_PATH / f'Bank_{bank_id}'
    dir_path.mkdir(parents=True, exist_ok=True)
    file = dir_path / f'Bank_{bank_id}.asm'

    content = [
        f'; {GAME_FOLDER_NAME}',
        f'; Bank ${bank_id}',
        f'; {len(adresses)} uniques instructions',
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
    """Write code/SPC700/SPC700.asm (Audio CPU)"""

    directory = CODE_PATH / 'SPC700'
    directory.mkdir(exist_ok=True)

    file_name = 'SPC700.asm'
    file = directory / file_name

    content = [
        '; SPC700 (Audio CPU Sony)',
        '; Boot ROM standard, do not modify',
        '',
    ]
    for addr, instr in seen_s.items():
        c = hits_s[addr]
        com = f'  ; (looped x{c} in traces)' if c > 1 else ''
        content.append(f'SPC_{addr}:  {instr:<30}{com}')

    file.write_text('\n'.join(content) + '\n')
    return file

if __name__ == '__main__':
    main()
