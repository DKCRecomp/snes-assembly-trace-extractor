# DKC1 SNES — Decompiled Code

Decompiled source code of **Donkey Kong Country** (ROM USA V1.0).

No ROM, assets, or extracted code in this repository.

## How to use it ?

**1. Code capture from Mesen-S**

```txt
Mesen-S → Debug → Trace Logger → Log to file
Launch game → Stop → Save traces as .txt
```

**2. Place logs in `traces/`**

```txt
traces/boot_session1.txt
traces/gameplay_jungle.txt
traces/player_jump.txt
```

**3. Run script**

```bash
python3 tools/trace_to_asm.py
```

This script reads **all** `.txt` from `traces/`, delete double code, and generate `.asm` files in `src/`.

---

## Progress

| Bank | Identified content | Statut |
|---|---|---|
| $00 | RESET, Init bootstrap, DMA setup | Partial |
| $B8 | PPU Hardware Init | Complete |
| SPC700 | Boot ROM Sony | Complete |
| $80 | Main loop, NMI, IRQ | Empty |
| $81–$8F | Game logic code | Empty |

## Sessions to record

- [ ] Complete boot / start screen sequence
- [ ] Gameplay 30s level 1
- [ ] Jump, roll
- [ ] Attack an ennemi / die
- [ ] Animals buddy

## TODO

- [] Translate RAM_Map from french.