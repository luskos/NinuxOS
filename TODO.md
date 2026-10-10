# NinuxOS - what is left to do

State on 10 October 2026, project v3.0.02 (the system on the disk is still the v2.9.59 kernel).
Versions: v3.x.xx - a small update raises xx, a big one x. How the work goes: DIRECTIVE.md.
Order inside a part = importance.

## To try now (the owner)

1. **Does a program made on the PC get into the system?** Copy the objects of `test/try`
   (pyhello, pycalc, pychronos, pynotepad, pybags) onto a FAT32 stick. In NinuxOS: `usb on`, `mnt`, `files`,
   `files get pyhello.asmo` (try also the short name the stick shows), then `ls`, `meta pyhello`,
   `run pyhello`, `run pyhello numbers`; for pycalc: start it from the desktop.
   Write down every answer of the system - each one says what the build must do.
   Expected problems: the identity in the header is 0; the system may want another ending or
   refuse a file that is already an object.
2. **Puffus:** close the one that is open, run `tools\puffus\make_puffus.cmd`, write a stick,
   start a PC from it. Then `python tools/source_container.py check \\.\PhysicalDriveN`.
3. `python pyton/test.py` - after the last change (prelude.py got its own names) the two
   examples were only assembled, not run.

## If the disk is lost again - where everything is

- GitHub, private: https://github.com/luskos/NinuxOS (every version has a tag).
- On every stick Puffus writes: the system from sector 0, and the whole source 1 GiB from the
  start of the stick. Take it out with `python tools/source_container.py unpack \\.\PhysicalDriveN`
  (Administrator). The same container is `build/source/NinuxOS_source.nxc` after every build.
- Before a NinuxOS stick goes into Windows: USB write protection on
  (`HKLM\SYSTEM\CurrentControlSet\Control\StorageDevicePolicies`, `WriteProtect` = 1, restart) -
  otherwise Windows writes over the kernel. Read a stick with `tools/dump_usb.ps1`.
- How the project was brought back the first time: `docs/chat`.

## 1. So that a changed system can be built

- [ ] **The kernel's own check.** The core checks the extension with SHA-256 at the start
      ("SHA-256 MISMATCH - system operations off"). Find where the expected hash lies and how the
      build fills it in; `tools/build_disk.py` must do the same.
- [ ] **The Sentinel list.** `sentinel` checks every system object and `@kernel` against "the build's
      signed list". Read the object `sentinel` (5048 bytes): its format, the hash it uses, the key.
      The private key of the old build is lost - a new build needs its own key, with the public
      half put into the kernel.
- [ ] **The object's identity** (header, 4 bytes at 0x4C; `id NAME` prints it, e.g. calc = #2032954E).
      CRC32 and FNV-1a over the obvious ranges do not give it. Find the function in the kernel.
- [ ] **The table of the cabinet.** Where the list of objects, slots, drawers and gaps lies on the
      disk (`ls` shows other addresses than the offsets in the image: +0xC4000). Until then the build
      can only replace an object by one of the same size.
- [ ] **580 KB between the objects** that belong to none of the 165 (pixels, an old Desktop v1.7).
      Find out whether the system uses them or the old build left them.
- [ ] The version the kernel says (v2.9.59 -> v3.x.xx) once the two checks above are solved.

## 2. PyTon: py2asm (pyton/)

Done in v3.0.0: the transpiler written anew; `python pyton/test.py` runs every program of
`pyton/examples` under real Python and compiled, and compares - both examples give the same output.
No class, on purpose: a program is made of objects (ASMO), not of classes.

- [x] v3.0.01: fill, fill_round, text, window, poll, key, key_mods, mouse_x/y/buttons,
      cursor_show/hide, ticks, log, meta are connected (`pyton/platform_ninux.inc`, py2asm: SYSTEM).
      Calc and ASMONCRAFT go through the new py2asm; nothing has run in the system yet.
- [x] v3.0.02: save_text, save_page, load_text, ob_count, ob_meta, meta_of, system, logline,
      random, spawn, kill, key_send, play, sound_stop, save_rating, screen_w / screen_h, textl,
      textof (`pyton/ninux_system.inc`). ticks is +0xA0 and key_mods the second value of poll
      (v3.0.01 had them wrong). 16 of the 20 programs of `apps/` compile and assemble.
- [ ] **The last functions:** load_image / save_image (Paint, Nest: the pixels of an image object
      to and from a list; an image's DATA is width, height, then 4 bytes a pixel), sound_play
      (PyNamp: place +0x138 with 1), net_ask / net_answer / net_state (Ask: place +0x150 with
      1, 2, 0), time. Method that worked: count the calls of a name in each program's source and
      the call sites of each runtime function in its object - equal counts name the function;
      then read its few lines.
- [ ] **The old programs on the screen.** They compile, but they were written for the old PyTon.
      Run each one compiled by the new py2asm beside the old one and note what differs
      (the owner; `test/try` has the first ones). Known risk: the old PyTon kept typed text as
      lists of letter codes and had its own len() / str() behaviour.
- [ ] A way in: a new object cannot be put into the cabinet from outside yet (part 1), and its
      identity (0x4C) is left 0.
- [ ] **Pages.** HTML + CSS with PyTon scripts (type:script) go through the kernel's own small
      compiler today. They should go through py2asm too, so that a page of NET is ASMO objects +
      HTML + CSS + PyTon and never needs another language. Read first how a page finds its script
      and what the script may call (Setup: the button Done runs `done()`).
- [ ] py2asm inside the system (Studio -> py2asm -> ASMO): it is a Python program now; inside
      NinuxOS it must be either PyTon compiled by itself, or the kernel's compiler brought up to it.
- [ ] The language, next: import (not now), with, yield, **kwargs, nonlocal, s[a:b] = ...,
      *name in [ ] and on the left of =; exceptions that keep more than kind and message.
- [ ] Giving memory back (nothing is freed yet); whole numbers beyond 63 bits; fractions printed
      as Python prints them (now up to 6 digits after the point).
- [ ] A def inside a def keeps the outer names as they were when it was made (Python: as they
      are when it runs). Decide whether this stays.
- [ ] More examples in `pyton/examples` - one for every place where PyTon may differ from Python.

## 3. Testing

- [ ] One command that runs everything: `pyton/test.py`, the build, the QEMU scripts of
      `test/qemu` with a check of the pictures or of the serial log - and says yes or no.
- [ ] The QEMU runs compare nothing yet: `tools/qemu/qrun.py` takes pictures, a person looks.
      Add `expect TEXT` on the serial log, and a way to compare a picture with a kept one.
- [ ] Puffus.exe, `tools/build_disk.py` and the source container on a stick have not been tried
      on a real stick since they were written (v2.9.60 / v3.0.0).
- [ ] `files get NAME` from a FAT32 stick and `build`: try with a real stick and with a USB stick
      in QEMU (`-device qemu-xhci -device usb-storage`).
- [ ] The old tests that survived (`../test` beside this folder: 35 `q_*.txt`, `script*.txt`):
      bring over the ones that still make sense.

## 4. The kernel source

- [ ] `kernel/Kernel.kasm` is 55% code, 45% `db`. Follow the code through the tables: the shell
      commands, the interrupt gates, the API table the programs call, the system sockets.
- [ ] Addresses kept in data and absolute addresses in code are still numbers. Turn them into
      labels - before that **no line may be added or removed**, only bytes changed in place.
- [ ] 143 instructions are `db` because nasm encodes them another way (lea 66, mov 58, cmp 15).
      Give them the exact form (`strict`, the long encodings).
- [ ] Names instead of addresses: from the shell commands and the log lines (`[shield]`, `[smp]`,
      `[pci]`, `[room]` ...). Then cut the file into the old parts: Loader, Core, Memory, Gates,
      Shield, Cart, ATA, and the extension's PCI, AHCI, NVMe, XHCI, Crypto, Files, PyTonCompiler ...
- [ ] The kernel suits (`build/kernel`: Tools, USB12, Network = k_net, Sound) and the compiled
      programs without a source (Desktop, Studio, NET, puffer, photon, tuner, metaspace): the same
      treatment as the kernel.

## 5. New: the disks of other systems - winlolz, linlolz

To read what is on a machine that already has Windows or Linux: see its disks, partitions and
volumes, walk the folders, copy files out, back them up - without starting that system.
Not decided what they are: kernel suits, shell commands, or desktop programs (or one of each:
a suit that reads, a command and a program that show).

- [ ] The partition tables: MBR and GPT (the kernel already reads disks through AHCI, NVMe, USB).
- [ ] winlolz: NTFS (read only: MFT, folders, files, compressed and sparse files; BitLocker says
      "locked"), exFAT, and FAT32 (already read by `files`).
- [ ] linlolz: ext4 (read only: extents, folders, links); later btrfs, xfs; LVM and LUKS say what
      they are.
- [ ] Never write to a foreign disk in the first versions: read, list, copy out.
- [ ] Where the copies go: into the cabinet as objects (a file = DATA + META with its old path,
      dates and size), or straight to another stick.
- [ ] This is also the tool that would have saved the old project: a lost NTFS partition read
      from NinuxOS.

## 6. New: the names of files - Greek letters

System formats get `.Ω` (Alt+234 on the numeric pad): a file with Ω is the system's and is not
to be touched. A proposal for the rest, to decide:

| ending | read | what it would be | today |
|---|---|---|---|
| `.Ω` | omega | a system object: only the system changes it | system `.asmo` |
| `.κ` | kappa | a part of the kernel, a kernel suit | `.kasm` |
| `.α` | alpha | a program of the user | user `.asmo` |
| `.π` | pi | PyTon source | `.py`, `X.Source.asmo` |
| `.φ` | phi | a page (HTML) | pages |
| `.θ` | theta | a theme / style (CSS) | themes |
| `.μ` | mu | media: a picture, a sound | image objects |
| `.δ` | delta | data and documents: a text, a list, settings | text / data objects |
| `.σ` | sigma | what is signed and checked: the Sentinel's list, keys | `sentinel`, `machine`, `netkey` |
| `.β` | beta | a backup or a container (the source container: `.β`) | `.nxc` |
| `.λ` | lambda | one function to plug in: a socket, a script | script objects |

- [ ] Decide the table. Inside the system an object has no file name - the ending matters where
      objects are files: in the project, on FAT32 sticks (`files`), in backups.
- [ ] The system's letters are Latin and Cyrillic: the Greek letters above must be added to the
      font, and the text encoding must have a place for them.
- [ ] Windows, git and FAT32 take these names (Unicode); check the build tools and NASM with them.

## 7. Tools

- [ ] `tools/build_disk.py`: objects of another size and new objects; build the image from nothing
      (no base image); the nasm pin of the old build (`tools/nasm.sha256`).
- [ ] `Puffus.exe`: a fresh machine identity for every stick (now every stick written from Windows
      is the same machine: ID, generation, parent).
- [ ] The source container is checked (SHA-256) but not secret. Lock it with a passphrase; and
      make it a program of the system as well: `source` in the shell that shows and unpacks it.
- [ ] Is 1 GiB from the start of the stick free for the system for good? Find where the cabinet
      grows to, and give the container a place the system knows about.
- [ ] The boot sector says "FAT12 diskette", so Windows mounts a NinuxOS stick and writes
      `System Volume Information` over sectors 19, 44, 45 of the kernel. Either a header Windows
      does not take for a file system, or keep those sectors free.

## 8. Known faults of v2.9.59 (not now)

- [ ] Bags: a page fault when it is closed with Esc (the shield catches it, the desktop goes on).
      It does not work as wanted anyway - to be redone.
- [ ] Support (the page `donate`) shows Puffer's text instead of the page with the QR code;
      probably the one object the Sentinel calls CHANGED.

## 9. Lost, not on the stick

docs (ASMO_SPEC, GUIDELINES, MAINFRAME, SECURITY_REVIEW, V2_ASSESSMENT), lab/photon, lab/pse,
lab/py3d, Editor, the old tests' harness (test/harness.c), tools/asmo_gen.py, tools/make_font.py,
tools/relay/ninux_relay.py (Ask needs it). vDNA is safe in its own repository; the ancestors of
py2asm (up to v3.21) are in the repository PypyOS.
