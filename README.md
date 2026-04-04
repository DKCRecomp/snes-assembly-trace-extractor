# SNES Assembly Extractor 

This tool converts [Mesen](https://github.com/SourMesen/Mesen2) emulator `.txt` log traces, into structured `.asm` files.

It handles code repetitions and SPC700 audio code.

This was developed using [Mesen](https://github.com/SourMesen/Mesen2), but I don't guarantee it will for other emulators.

> [!IMPORTANT]
> **No rom, assets, nor extracted code in this repository**.

## How to create a game code log trace ?

### **1. Code capture from Mesen-S (or any emulator)**

Select `Trace Logger`.

![step1](./assets/1-toolbar.png)

### **Make sure you got these exact settings for better compatibility**

![step2](./assets/2-settings.png)


### **3. Log to a `.txt` file**

Select `Log to file...` and save it as a `.txt` file.

![step3](./assets/3-log-to-file.png)

### **4. Start trace creation**

![step4](./assets/4-trace-log-run.png)


### **5. Place logs in `snes-assembly-trace-extractor/traces`**

![step5](./assets/5-traces-location.png)

## How to use it ?

```bash
bash run.sh
```

This will reads **all** `.txt` from `traces/`, delete double code, and generate `.asm` files in `code/`.