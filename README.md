# SNES ASM Code Cleaner & Extractor 

It cleans and sorts a .txt log trace file from SNES emulation debug sessions on Mesen. 

Tool made for a **Donkey Kong Country** recompilation effort. 

No ROM, assets, or extracted code in this repository.

## How to use it ?

**1. Code capture from Mesen-S**

```txt
Mesen-S -> Debug -> Trace Logger -> Log to file
Launch Game -> Stop -> Save traces as .txt
```

**2. Place logs in `traces/`**

```txt
traces/boot_session1.txt
traces/gameplay_jungle.txt
traces/player_jump.txt
```

**3. Run script**

```bash
bash extract-traces.sh
```

This script reads **all** `.txt` from `traces/`, delete double code, and generate `.asm` files in `src/`.