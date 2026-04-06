#!/usr/bin/env python3

"""
=====================================
Log tracer converter to ASM
=====================================
Read txt files from directory traces/
Generate asm files in code/
=====================================
"""

import re
from pathlib import Path
import sys
from collections import Counter, OrderedDict, defaultdict

import config

def main():
    print_start()
    extract_traces()
    print_end()

def print_start():
    print('')
    print('==============================================================')
    print(f'            SNES Assembly Log Trace Extractor')
    print('==============================================================')
    print('')

def print_end():

    print('')
    print('==================================')
    print(f'            Finished')
    print('==================================')
    print('')

# /--------------------------------------/

def extract_traces():
    files = load_traces_files()
    
    for file in files:
        extract_trace(file)

def extract_trace(file):

    print(f'Processing {file.name}')

    # ----- 1) load result -----
    
    seen, hits, seen_s, hits_s = load_trace_file(file)

    total_lines_nb = sum(hits.values())
    unique_lines_nb = len(seen)
    redond_lines_nb = total_lines_nb - unique_lines_nb
    banks = sorted(set(a[:2] for a in seen))

    print_trace_load(
        config.CURRENT_TRACE_NAME, 
        total_lines_nb, 
        unique_lines_nb, 
        redond_lines_nb, 
        hits_s, seen_s, 
        banks
    )

    # ----- 2) code writing -----

    print('')
    print(f'Writing in {config.CODE_DIR}')

    by_bank = defaultdict(list)
    for addr in seen:
        by_bank[addr[:2]].append(addr)

    for bank, addrs in sorted(by_bank.items()):
        file = write_bank(bank, addrs, seen, hits)
        print(f'    - {file.relative_to(config.REPO_ROOT)}  ({len(addrs)} instructions)')

    if seen_s:
        file = write_audio(seen_s, hits_s)
        print(f'    - {file.relative_to(config.REPO_ROOT)}  ({len(seen_s)} instructions)')

    print('')

# /--------------------------------------/

def load_traces_files():
    """Load all files from traces directory, and return them."""

    files = sorted(config.TRACES_PATH.glob(f'*.{config.TRACES_EXTENSION}'))
    if not files:
        print(f"No .{config.TRACES_EXTENSION} found in {config.TRACES_PATH}")
        print(f"Export log from Mesen (or any emulator) and place it in {config.TRACES_DIR}")
        sys.exit(1)
    return files

def load_trace_file(file):
    """Reads given file and return uniques instructions."""

    file_size = file.stat().st_size // 1024
    print(f"  - Reading {file.name} ({file_size} Ko)")

    seen   = OrderedDict()
    hits   = Counter()
    seen_s = OrderedDict()
    hits_s = Counter()
    
    update_trace_dir(file.name)

    for line in file.open(encoding='utf-8', errors='replace'):
        line = line.rstrip()
        match = config.PAT_65816.match(line)

        if match:
            addr = match.group(1)
            hits[addr] += 1
            if addr not in seen:
                seen[addr] = {'instr': match.group(2).strip(), 'P': match.group(6)}
            continue

        match = config.PAT_SPC700.match(line)
        if match:
            addr = match.group(1)
            hits_s[addr] += 1
            if addr not in seen_s:
                seen_s[addr] = match.group(2).strip()
    return seen, hits, seen_s, hits_s

def update_trace_dir(file_name):
    """Create a folder for specified file name, and update current trace name value."""

    # Remove `.txt` from file name
    trace_name = Path(file_name).with_suffix('')
    config.CURRENT_TRACE_NAME = trace_name

    # We update globally code path for each trace file
    config.CODE_PATH = config.REPO_ROOT / config.CODE_DIR / trace_name
    
    # Create folder
    print(f"    - Creating {trace_name} folder")
    config.CODE_PATH.mkdir(parents=True, exist_ok=True)

def print_trace_load(trace_name, total_lines_nb, unique_lines_nb, redond_lines_nb, hits_s, seen_s, banks):
    print(f'')
    print(f'{trace_name} loaded :')
    print(f'    65C816  : {total_lines_nb} lines -> {unique_lines_nb} uniques ({redond_lines_nb} double code deleted)')
    print(f'    {config.AUDIO_CPU}  : {sum(hits_s.values())} lines -> {len(seen_s)} uniques')
    print(f'    Banks : {banks}')

# /--------------------------------------/

def write_bank(bank_id, adresses, seen, hits):
    """Write Bank_XX/Bank_XX.asm"""

    dir_path = config.CODE_PATH / f'Bank_{bank_id}'
    dir_path.mkdir(parents=True, exist_ok=True)
    file = dir_path / f'Bank_{bank_id}.asm'

    content = [
        f'; {config.CURRENT_TRACE_NAME}',
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
 
def write_audio(seen_s, hits_s):
    """Write SPC700/SPC700.asm (Audio CPU)"""

    directory = config.CODE_PATH / config.AUDIO_CPU
    directory.mkdir(exist_ok=True)

    file_name = f'{config.AUDIO_CPU}.asm'
    file = directory / file_name

    content = [
        f'; {config.AUDIO_CPU} (Audio CPU)',
        '; Boot ROM standard, do not modify',
        '',
    ]
    
    for addr, instr in seen_s.items():
        c = hits_s[addr]
        com = f'  ; (looped x{c} in traces)' if c > 1 else ''
        content.append(f'SPC_{addr}:  {instr:<30}{com}')

    file.write_text('\n'.join(content) + '\n')
    return file

def comment_instr(instr, hits_addr):
    """Generate comment for a given instruction."""

    mnemonic = instr.split()[0]
    parts = []

    # Hardware register name
    m = re.search(r'\$([0-9A-F]{4})', instr)
    if m:
        reg = int(m.group(1), 16)
        if reg in config.HARDWARE_REGISTERS:
            parts.append(config.HARDWARE_REGISTERS[reg])

    # Change 8/16 bits mode
    if mnemonic in ('REP', 'SEP'):
        m2 = re.search(r'#\$([0-9A-F]{2})', instr)
        if m2:
            v = int(m2.group(1), 16)
            size = '16' if mnemonic == 'REP' else '8'
            if v & 0x20: parts.append(f'A={size}b')
            if v & 0x10: parts.append(f'X/Y={size}b')

    # Loop detected
    if hits_addr > 1:
        parts.append(f'(looped x{hits_addr} in traces)')

    return ('  ; ' + ', '.join(parts)) if parts else ''

if __name__ == '__main__':
    main()
