#!/usr/bin/env python3

"""
=====================================
Log tracer converter to ASM
=====================================
Read txt files from directory traces/
Generate asm files in result/
=====================================
"""

import re
from pathlib import Path
import sys
from collections import Counter, OrderedDict, defaultdict

import config

def main():
    print_start()
    extract_traces_files()
    print_end()

def print_start():
    print('==============================================================')
    print(f'            SNES Assembly Log Trace Extractor')
    print('==============================================================')
    print(f'\nResults are generated at : {config.CODE_PATH}\n')

def print_end():
    print('\n==================================')
    print(f'            Finished')
    print('==================================\n')

# /--------------------------------------/

def extract_traces_files():
    """Extract all available traces files."""

    print('Start extracting traces...\n')

    config.KEEP_LOOP_TRACK = ask_keep_looped()
    files = get_traces_files()
    
    for file in files:
        extract_trace_file(file)

def extract_trace_file(file):
    """Extract given trace files."""

    # 1) load result
    seen, hits, seen_s, hits_s = read_trace_file(file)
    
    # 2) code generation
    generate_trace_code(seen, hits, seen_s, hits_s)

def generate_trace_code(seen, hits, seen_s, hits_s):

    print('\n==============================================================')
    print(f'                 Generating {config.CODE_EXT} at /{config.CODE_DIR}...')
    print('==============================================================\n')

    by_bank = defaultdict(list)
    for addr in seen:
        by_bank[addr[:2]].append(addr)

    for bank, addrs in sorted(by_bank.items()):
        file = write_bank(bank, addrs, seen, hits)
        print(f'    - {file.relative_to(config.REPO_ROOT)}  ({len(addrs)} instructions)')

    if seen_s:
        file = write_audio(seen_s, hits_s)
        print(f'    - {file.relative_to(config.REPO_ROOT)}  ({len(seen_s)} instructions)')

def ask_keep_looped():
    return input('Keep tracked looped code in result ? (y/n): ').lower().startswith('y')

# /--------------------------------------/

def get_traces_files():
    """Load all files from traces directory, and return them."""

    files = sorted(config.TRACES_PATH.glob(f'*.{config.TRACES_EXT}'))

    if not files:
        print(f"\nNo .{config.TRACES_EXT} found in {config.TRACES_PATH}")
        print(f"Export log from Mesen (or any emulator) and place it in {config.TRACES_DIR} before usage.\n")
        sys.exit(1)
    return files

def read_trace_file(file):
    """Reads given file and return uniques instructions."""

    print('\n==============================================================')
    print(f'                Reading {file.name}...')
    print('==============================================================\n')
    
    seen   = OrderedDict()
    hits   = Counter()
    seen_s = OrderedDict()
    hits_s = Counter()

    update_trace_dir(file.name)

    file_size = file.stat().st_size // 1024
    print(f"  - Process reading {file.name}... ({file_size} Ko)")
    print(f"(Can be very long depending on file size, please be patient)")

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

    print_trace_load(seen, hits, seen_s, hits_s)
    return seen, hits, seen_s, hits_s

def update_trace_dir(file_name):
    """Create a folder for specified file name, and update current trace name value."""

    # Remove `.txt` from file name
    trace_name = Path(file_name).with_suffix('')
    config.CURRENT_TRACE_NAME = trace_name

    # We update globally code path for each trace file
    config.CODE_PATH = config.REPO_ROOT / config.CODE_DIR / trace_name

    # Create folder
    path = config.CODE_PATH
    if path.exists():
        print(f"  - {path} already exists, please remove it")
        exit()


    path.mkdir(parents=True, exist_ok=True)
    print(f"  - {path} created")

def print_trace_load(seen, hits, seen_s, hits_s):

    total_lines_nb = sum(hits.values())
    unique_lines_nb = len(seen)
    redond_lines_nb = total_lines_nb - unique_lines_nb
    banks = sorted(set(a[:2] for a in seen))
    sum_hits = sum(hits_s.values())
    nb_seens = len(seen_s)

    print(f'')
    print(f'{config.CURRENT_TRACE_NAME} loaded :')
    print(f'    65C816  : {total_lines_nb} lines -> {unique_lines_nb} uniques ({redond_lines_nb} double code deleted)')
    print(f'    {config.AUDIO_CPU}  : {sum_hits} lines -> {nb_seens} uniques')
    print(f'    Detected Banks  : {banks}')

# /--------------------------------------/

def write_bank(bank_id, adresses, seen, hits):
    """Write Bank_XX/Bank_XX.asm"""

    bank_name = f'Bank_{bank_id}'
    dir_path = config.CODE_PATH / bank_name
    dir_path.mkdir(parents=True, exist_ok=True)
    file = dir_path / f'{bank_name}.{config.CODE_EXT}'

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
            content.append(f'\n; --- gap ${addr_int - prev:04X} bytes (non traced) ---\n')

        comment = get_instr_comment(d['instr'], hits[addr])
        content.append(f'CODE_{addr}:  {d["instr"]:<36}{comment}')
        prev = addr_int

    content = '\n'.join(content) + '\n'
    file.write_text(content)
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

def get_instr_comment(instr, hits_addr):
    """Generate a comment for a given instruction, and returns it."""

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

    # Loop tracking
    if config.KEEP_LOOP_TRACK and hits_addr > 1:
        parts.append(f'(looped x{hits_addr} in traces)')

    comment = ('  ; ' + ', '.join(parts)) if parts else ''
    return comment

if __name__ == '__main__':
    main()
