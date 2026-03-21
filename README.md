# SNES Assembly extractor 

This tool reads [Mesen emulator](https://github.com/SourMesen/Mesen2) `.txt` log traces, delete double code, and generate structured `.asm` files.

Originally made for a **Donkey Kong Country** recompilation effort. 

This was developed using [Mesen](https://github.com/SourMesen/Mesen2), but I guess any `.txt` log traces from any emulator would work.
This tool has no dependencies with Mesen.

> [!IMPORTANT]
> **No rom, assets, nor extracted code in this repository**.

## How to use it ?

**1. Code capture from Mesen-S**

```txt
Mesen-S -> Debug -> Trace Logger -> Log to file
Launch Game -> Stop -> Save traces as .txt
```

**2. Place logs in `traces/`**

```txt
traces/super_mario_world_logs.txt
```

**3. Run script**

```bash
bash extract-traces.sh
```

This will reads **all** `.txt` from `traces/`, delete double code, and generate `.asm` files in `src/`.