import re
from pathlib import Path

# /-----/ Globals /-----/

REPO_ROOT = Path(__file__).parent.parent

# Traces
TRACES_DIR = "traces"
TRACES_PATH = REPO_ROOT / TRACES_DIR
TRACES_EXTENSION = "txt"
CURRENT_TRACE_NAME = "" # value updated in each file process
KEEP_LOOP_TRACK = False

# Code Banks
CODE_DIR = "result"
CODE_PATH = REPO_ROOT / CODE_DIR

# Audio
AUDIO_CPU = "SPC700"

# /-----/ Pattern parsing /-----/

# CPU
PAT_65816 = re.compile(
    r'^([0-9A-F]{6})\s+(\S.*?)\s{2,}'
    r'A:([0-9A-F]{4}) X:([0-9A-F]{4}) Y:([0-9A-F]{4}) '
    r'S:[0-9A-F]{4} D:[0-9A-F]{4} DB:[0-9A-F]{2} '
    r'P:(\S+)'
)

# AUDIO
PAT_SPC700 = re.compile(
    r'^([0-9A-F]{4})\s+(\S.*?)\s{2,}'
    r'A:[0-9A-F]{2} X:[0-9A-F]{2} Y:[0-9A-F]{2} '
    r'S:[0-9A-F]{2} P:(\S+)'
)

# /-----/ Hardware Registers /-----/

HARDWARE_REGISTERS = {
    0x2100:'INIDISP', 0x2101:'OBSEL',    0x2102:'OAMADDL', 0x2103:'OAMADDH',
    0x2104:'OAMDATA', 0x2105:'BGMODE',   0x2106:'MOSAIC',  0x2107:'BG1SC',
    0x2108:'BG2SC',   0x2109:'BG3SC',    0x210A:'BG4SC',   0x210B:'BG12NBA',
    0x210C:'BG34NBA', 0x210D:'BG1HOFS',  0x210E:'BG1VOFS', 0x210F:'BG2HOFS',
    0x2110:'BG2VOFS', 0x2111:'BG3HOFS',  0x2112:'BG3VOFS', 0x2115:'VMAIN',
    0x2116:'VMADDL',  0x2117:'VMADDH',   0x2118:'VMDATAL', 0x2119:'VMDATAH',
    0x211A:'M7SEL',   0x211B:'M7A',      0x211C:'M7B',
    0x2121:'CGADD',   0x2122:'CGDATA',   0x2123:'W12SEL',  0x2124:'W34SEL',
    0x2130:'CGWSEL',  0x2131:'CGADSUB',  0x2132:'COLDATA', 0x2133:'SETINI',
    0x4016:'JOYA',    0x4017:'JOYB',
    0x4200:'NMITIMEN',0x4201:'WRIO',     0x4202:'WRMPYA',  0x4203:'WRMPYB',
    0x4204:'WRDIVL',  0x4205:'WRDIVH',   0x4206:'WRDIVB',
    0x420B:'MDMAEN',  0x420C:'HDMAEN',   0x420D:'MEMSEL',
    0x4300:'DMAP0',   0x4301:'BBAD0',    0x4302:'A1T0L',   0x4304:'A1B0',
    0x4305:'DAS0L',
    0x2180:'WMDATA',  0x2181:'WMADDL',   0x2182:'WMADDM',  0x2183:'WMADDH',
}
