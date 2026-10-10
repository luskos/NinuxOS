# NinuxOS - what each version brought

Newest first. v2.9.60 and later are written by hand; everything from v2.9.50 down is the text the v2.9.59
kernel carries in itself.

- **v3.0.02** (10 October 2026)
  - py2asm: the rest of the system's functions found in the old runtime and connected
    (`pyton/ninux_system.inc`): save_text, save_page, load_text, ob_count, ob_meta, meta_of,
    system, logline, random, spawn, kill, key_send, play, sound_stop, save_rating, screen_w,
    screen_h; textl and textof in prelude.py. 16 of the 20 programs of v2.9.59 compile and
    assemble; Paint, Nest (images), PyNamp (a sound object) and Ask (the network) wait.
  - Corrected from v3.0.01: ticks is place +0xA0 (not +0x10, which is the size of the screen);
    key_mods is the second value poll gives.
  - Learned on the way: a program that saves a text builds the whole object itself and leaves
    the identity 0 - the system fills it in when it saves.
  - `test/try`: pyhello, pycalc, pychronos, pynotepad, pybags as objects. Nothing was run.
- **v3.0.01** (10 October 2026)
  - The project moved to the folder `NinuxOS_v3`; `DIRECTIVE.md` says how the work goes.
  - py2asm reaches NinuxOS: fill, fill_round, text, window, poll, key, the mouse, the cursor, ticks,
    log and meta are connected - their places in the system's table were read from the runtime of
    the old programs. Calc and ASMONCRAFT compile with the new py2asm; the other 18 programs wait
    for save_text, load_text, ob_meta, system and the rest (TODO.md).
  - prelude.py has names of its own now: a program may have a `_helper` with the same name.
    `char`, `code`, `field`, `textof` of the v2.9 PyTon are there for the old programs.
  - `test/try`: pyhello and pycalc as objects, to find out whether `files get` takes them.
  - The architecture document: the shell and all its commands (the help text taken out of the
    kernel), PyTon and py2asm in full, the formats (kernel on the disk, the source container, the
    QEMU scripts), versions.
  - Nothing of this was run: by the directive the owner tests.
- **v3.0.0** (10 October 2026) - versions are v3.x.xx from here. The system on the disk is still the
  v2.9.59 kernel (TODO.md, part 1).
  - PyTon: `pyton/py2asm.py` written anew. The program is read with Python's own parser and compiled
    to assembly: for, break, continue, +=, dicts, tuples, sets, fractions, slices, f-strings,
    comprehensions, default values, *args, def inside def, lambda, functions as values,
    try / except / finally / raise, the methods of texts, lists, dicts and sets. No class, on purpose.
    Most of the language is written in PyTon itself (`pyton/prelude.py`) on a small assembly core
    (`pyton/runtime.inc`). `python pyton/test.py` runs the examples under real Python and compiled
    (a Windows .exe made by nasm alone) and compares: the same output.
  - For NinuxOS py2asm writes an ASMO v4 object, but only print and input reach the system yet:
    13 of the system's functions are not found (`pyton/platform_ninux.inc`).
  - The source container: `tools/source_container.py` packs every file of the project;
    the build makes it, Puffus writes it onto the stick 1 GiB from its start.
  - TODO.md: where everything is if the disk is lost again; winlolz / linlolz (the disks of
    Windows and Linux); file names with Greek letters (.Ω for the system).
- **v2.9.60** (10 October 2026) - the project is back after the disk was lost. The system itself is
  still the v2.9.59 that came off the stick (its kernel says v2.9.59: other bytes in the kernel would
  fail its SHA-256 check, and nothing signs a new one yet - TODO.md). New in the project:
  - the whole system taken from a bootable stick: `disk.img`, the 165 objects of the cabinet,
    the PyTon sources of 20 programs, the pages, themes and scripts
  - `boot/Boot.kasm` and `kernel/Kernel.kasm`: the boot sector and the kernel as NASM source again,
    made from the compiled kernel by `tools/kdis/kdis.py`; they assemble to the same bytes
  - `tools/build_disk.py`: the build - assembles the boot sector and the kernel, puts them and the
    objects into the base image, writes `disk.img`
  - `Puffus.exe` (`tools/puffus`): builds, writes `disk.img` onto a USB stick, reads it back, ejects it
  - `tools/qemu/qrun.py` and `test/qemu/q_v2959_*.txt`: the system in QEMU, driven by scripts
  - `docs/NinuxOS_Architecture.tex`: the system and the files of the project, described anew
  - `TODO.md`, and `docs/chat`: the conversation in which all this was done
- **v2.9.51 - v2.9.59** - the kernel carries no line about these. What is known: Keys is
  "NinuxOS v2.9.59", Ask is "v2.9.56" (the dates in their sources).

NinuxOS v2.9.59 with ASMO v4 objects

- **v2.9.50** - Studio's panel and tabs, a program as wallpaper, people
- **v2.9.49** - NET on the whole screen, login, Phone
- **v2.9.48** - install for UEFI, the screen above 4 GB, level strict
- **v2.9.47** - move mode (Alt+M); an uprooted system is sealed, uproot BURN
- **v2.9.45** - Copycat, games on the whole screen
- **v2.9.44** - the Realtek network card, ratings
- **v2.9.43** - colors; the UEFI start takes the biggest screen
- **v2.9.42** - the UEFI start
- **v2.9.41** - tune asks every core
- **v2.9.40** - mnt tries harder, games swap with the desktop, Shift marks text
- **v2.9.39** - Alt + the Ngage key swaps a program and the desktop; a new look for Studio
- **v2.9.38** - the chained record, uproot / root
- **v2.9.37** - fastback - letters drawn from ready answers
- **v2.9.36** - tune steers through Speed Shift, says who holds the processor back
- **v2.9.34** - tune - the processor's clock: turbo, charts, the EMA governor
- **v2.9.33** - PrtSc, Ctrl+Alt+L, Ctrl keys, alarms, PyNamp / Search / Projector / Bags / Widgets
- **v2.9.32** - mnt - a USB stick put in after the start
- **v2.9.31** - security - maint asks the password, only verified code runs on the kernel's page tables
- **v2.9.30** - the tools are a kernel suit (k_tools) - the extension has room again
- **v2.9.29** - bench - one performance test
- **v2.9.28** - Mail (name@ninux), search in Device
- **v2.9.27** - every core gets its own stack at the start, Nest, Device
- **v2.9.26** - update keeps a backup - update back returns to it
- **v2.9.25** - every start tries all cores again, cores says who does the shared work
- **v2.9.24** - ASMONCRAFT, the first META game
- **v2.9.23** - Interfacer - build a NET page with the mouse
- **v2.9.22** - Paint - brush sizes and Undo
- **v2.9.21** - META the launcher, a late core parks itself, labels centred
- **v2.9.20** - menus over every window, Cyrillic in Notepad, a line a core in cores
- **v2.9.19** - the letters are in every build now, EN / BG in the dock, the Windows key closes the menu
- **v2.9.18** - files from FAT32 pen drives, WAV in play
- **v2.9.17** - its own letters with Cyrillic, BG keyboard (Alt+Shift), the Windows key
- **v2.9.16** - Puffer makes bootable USB sticks
- **v2.9.15** - the mouse no longer lags behind the hand
- **v2.9.14** - the build signs the kernel as it is on the disk - update can replace it
- **v2.9.13** - shared work can't hang (solo after 5 s), update writes the kernel first and checks it
- **v2.9.12** - the other cores get their caches on, help in pages, cores solo
- **v2.9.11** - update from a USB stick, restart fixed, one core by default
- **v2.9.10** - the safe start, 'cores one / all / beat'
- **v2.9.9** - Photon from the desktop, the floor as a plane
- **v2.9.8** - the Photon engine in the SUB-GPU
- **v2.9.7** - the log ring
- **v2.9.6** - Notepad, Console, summer time
- **v2.9.5** - machine keys, the Sentinel checks the kernel
- **v2.9.4** - Paint
- **v2.9.3** - programs on every CPU core at once
- **v2.9.2** - the Sentinel refuses changed objects, machine identity
- **v2.9** - window buttons per app, minimise, DesktopStone, kill, NET, Chronos, the PC clock) (every program an .asmo, the kernel in .kasm parts, a system cabinet only the system reads, the stencil look: rounded see-through glass), a storage room of cabinets and drawers, RGBA identities, a split kernel, the Multiplexer (programs side by side in windows), system sockets, locked objects, PyTon (text, lists, dicts, floats, functions; compiled to native code inside NinuxOS), every CPU core, USB keyboards and mice (every xHCI controller, report-protocol mice; UHCI and OHCI too, v2.2), USB sticks on xHCI and EHCI, sound (HD Audio, AC97) and screen modes (v2.3), the network and Meta Net with signed, encrypted pages (v2.4) with share / transfer / broadcast / subscribe (v2.5); kernel suits (KASM objects) put on when needed (v2.6), SATA (AHCI) and NVMe disks and an installer onto them, ACPI power-off, a virtio-gpu driver and the GPU lab, a taskbar and Studio drawn as pages, memory and page tables per program with time slices (v2.1), apps, Studio, HTML + CSS pages with PyTon scripts, shield
