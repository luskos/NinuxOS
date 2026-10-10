# NinuxOS - what each version brought

Newest first. v2.9.60 is written by hand; everything from v2.9.50 down is the text the v2.9.59
kernel carries in itself.

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
  - `pyton/py2asm.py`, written anew: PyTon is read with Python's own parser and compiled to assembly.
    for, break, continue, +=, dicts, tuples, fractions, slices, f-strings, default values, the methods
    of texts, lists and dicts. Most of it is written in PyTon itself (`pyton/prelude.py`) on a small
    assembly core (`pyton/runtime.inc`). Not tried yet; see TODO.md
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
