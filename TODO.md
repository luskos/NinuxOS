# NinuxOS - what is left to do

State on 10 October 2026, project v3.0.08 (everything that is compiled has a source now; the build
writes the version, adds objects, signs).
Versions: v3.x.xx - a small update raises xx, a big one x. How the work goes: DIRECTIVE.md.
Order inside a part = importance.

## To try now (the owner)

**The whole list, step by step, is `docs/TESTS.md`.** Nothing built since v2.9.59 has run on a
machine; part C of that list (the start) decides whether the signing is right.

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

Solved in v3.0.04 by reading the image (docs/NinuxOS_Architecture.tex, section 3) - **not tried
on a machine yet**:

- [x] The SHA-256 of the extension: at byte 0xF058 of the kernel; the build writes it anew.
- [x] The Sentinel's list: 64 bytes Ed25519 signature, 'NXSN', 98 lines of name + SHA-256 (an
      object from byte 0x68 to its end; @kernel = the 480 sectors). The build writes it and signs
      it with its own key (build/key/build.key); the public half goes to byte 0x2D280 of the kernel.
- [x] The table of the cabinet: sector 481, 'CABN', 32 bytes an object, 63 places; drawers are the
      same table in the DATA of an object. The build adds the objects of build/add/.
- [x] The identity: an object with 0 is not compared with the table - not needed for a build.
- [x] The "580 KB between the objects": 58 of the 165 objects in the image are old copies no
      table points at. The system has 107.
- [x] The version: written into the whole kernel.

Open:

- [ ] **Try it** (the owner): does v3.0.04 start, what does `sentinel` say, do `pyhello` and
      `pycalc` appear (`ls`, `run pyhello`, the desktop). If it does not start: build with
      `--no-seal`, then with `--keep-version`, then without the files of build/add/ - the first
      one that starts says which part is wrong.
- [ ] build/key/build.key is on this PC only. Copy it somewhere safe (not into git).
- [ ] Put a new object into a drawer, not only into the cabinet (63 places, 49 taken now).
- [ ] An object the build adds is not in the Sentinel's list, so the shell may refuse to `run` it
      ("runs only as a program in a window"). The build signs the list itself: give the added
      objects lines in it (the list and the object `sentinel` grow by 48 bytes a line).
- [ ] Take the 58 dead copies out of the image and out of docs/cabinet_objects.csv; build the
      image from nothing instead of from the base image.
- [ ] How an identity is computed (for `id`; the system fills it in when it saves an object).

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

## 4. The source of what is compiled

Done - everything assembles to the same bytes as v2.9.59:

- [x] `boot/Boot.kasm` - by hand, with names and comments.
- [x] `kernel/Kernel.kasm` (v3.0.05): 122 KB of code as 30952 instructions, none left as bytes;
      the tables of addresses in the data found and followed (369 addresses, now names); the
      variables in memory named; the loader's addresses named; the size of the extension written
      as `ext_end - ext_start`. Real names from two tables: `api_*` (what a program may call) and
      `cmd_*` (the shell's commands).
- [x] `kernel/suits/*.kasm` (v3.0.05): the four kernel suits; the build assembles them, puts the
      code into their objects and signs them.
- [x] `objects/*.asmo.kasm` (v3.0.04): the 34 compiled objects - Desktop, Studio, NET, the 20
      programs, the tests.

Open:

- [ ] **The proof.** Add one `nop` at the start of a function in `kernel/Kernel.kasm`, build,
      start the system (the owner). If it starts and works, lines can be added to the kernel for
      good; if not, an address is still a plain number somewhere - then compare where it fails.
      The same once for a suit and for an object (`objects/calc.asmo.kasm` -> build/add).
- [ ] A suit or an object of another size: the build takes only the same size from
      `kernel/suits` and has no step yet that assembles `objects/*.asmo.kasm` into the image.
- [ ] 84 places where a jump lands inside what was read as another instruction - look at each:
      data read as code, or two ways into the same bytes.
- [ ] The 16 KB of "other data" in the kernel, table by table: name them, and see whether code
      hides there (constants of SHA-512 and Ed25519, Photon's tables, the keyboard maps ...).
- [ ] Names. 655 functions of the kernel are still `fn_ADDR`. Sources of names: the log lines
      (`[shield]`, `[smp]`, `[pci]`, `[room]`, `[mux]` ...), the texts each function prints, the
      order of the old files. `tools/kdis/names.txt` (ADDR NAME) is read by kdis - put them there,
      not into the generated file.
- [ ] Cut the kernel into the old parts (Loader, Core, Memory, Gates, Shield, Cart, ATA; PCI,
      AHCI, NVMe, XHCI, Crypto, Files, PyTonCompiler, Tuner, VirtioGPU, Photon ...) as `%include`s.
- [ ] Photon, Puffer, Tuner, META: the objects are 560-byte launchers; the programs are functions
      of the extension. Find where each begins (`cmd_puffer`, `cmd_tune`, `cmd_spaces` lead there).
- [ ] **Rewriting.** What exists is exact, but it is a machine's reading: no structure, few
      names, no comments. Rewriting a part by hand (same behaviour, source meant to be read) is
      possible part by part; say which part first (the shell? the cabinet? the desktop?).
      After the rewrite the bytes will differ - then only running it can say it is the same.

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

## 4a. What an operating system needs and NinuxOS does not have yet

Looked at on 10 October 2026, against v2.9.59. Order = how much it hurts.

- [ ] **One copy of everything that matters on the disk.** The table of the cabinet is one
      sector run at 481; the kernel is one copy; nothing is written in two steps. One bad sector
      or a power cut in the middle of a write and the system is gone (this project was lost that
      way once). Needed: a second copy of the table and of the kernel, writes that are either
      whole or not at all, a check at every start. The owner's idea of an instance on every disk
      (below) is the big form of this.
- [ ] **The boot sector looks like a FAT12 diskette**, so Windows writes over the kernel when the
      stick is plugged in. Every user will do this once.
- [ ] **Programs do not live on.** Leaving the desktop for the shell closes every program
      ("[desktop] closed", "[mux] multiplexer off") and the desktop starts anew on the way back.
      So nothing runs in the background, and `kill NAME` has nothing to kill. Needed: programs
      that keep running whatever is on the screen, and a list of them (`tasks`).
- [ ] **Memory is never given back** by a PyTon program (old runtime and new). A program that
      runs long fills its memory and stops.
- [ ] **All cores.** By default every program takes turns on the first core ("cores all" crashed
      a real machine in v2.9.10). `bench` and `cores solo` show the same numbers on one core and
      on many (the owner, 10 Oct) - find out what `cores solo` switches and what `bench` measures.
- [ ] **A wall between programs and the system.** A program gets the whole table of the system's
      functions: it can save over any object, start and close other programs, send keys to
      another window, read every object. The shield stops it writing into the kernel, not using
      the kernel. Needed: what a program may do written in its META and checked on every call.
- [ ] **The outside world.** Read only: FAT32 sticks. No writing to a stick, no NTFS / ext4
      (winlolz / linlolz below). The network has two wired cards; no Wi-Fi. Whether there is TCP,
      DNS, TLS - a way to the internet at all - has not been read from the kernel yet.
- [ ] **Text is one byte a letter** (Latin and Cyrillic). No Unicode: no Greek (the file endings
      planned below), no other scripts, no emoji; a text from outside in UTF-8 shows wrong.
- [ ] **Laptops.** No sleep, no battery, no lid, no touchpad that is not PS/2 or USB, no screen
      brightness. ACPI is used for power-off only.
- [ ] **Programs are made outside the system.** `build` inside compiles numbers only; py2asm is a
      Python program on a PC. A system that cannot build its own programs depends on another one.
- [ ] **When something goes wrong.** A fault in a program is caught and logged; there is no way
      to look inside a running program, no saved picture of a crash, no automatic tests.
- [ ] Smaller: no clock from the network; sound out only; no printing; no Bluetooth.

## 4c. Measured against macOS, Windows, Linux, Android

What those systems have that a person meets every day. "Has" is what v2.9.59 shows or says of
itself; where it was not read from the kernel it says so. **!** = without it the system cannot
be given to someone else to use.

| area | NinuxOS has | missing |
|---|---|---|
| **Programs that run** | windows side by side, time slices, own memory and page tables per program | **!** programs that keep running when not on the screen (services, downloads, music, alarms); a list of what runs and a way to stop it; priorities; threads inside a program; a program talking to another one (today only through objects and the clipboard) |
| **Memory** | per-program memory, a kernel allocator, `mem`, `memtest` | **!** giving memory back; a limit for each program and a clean end when it is reached; loading a program's parts only when needed; anything when memory runs out |
| **Keeping data** | the cabinet, drawers, a signed list for system objects, `update back`, `scan`, `recover` | **!** a second copy of the table and the kernel; writes that are whole or not at all; **!** backup and restore of the user's own objects (Time Machine, File History); snapshots; more than 63 objects in a place; a check of user objects, not only system ones; care for SSDs (TRIM) |
| **Permissions** | users with a password and a level, age ratings, maintenance mode, locked and hidden objects, ring 3 | **!** per program: what it may read, change, start, send (Android asks; here every program may everything the table offers); each user's objects apart from the others'; asking the person before something dangerous |
| **Trust from the start** | the Sentinel, a signed kernel and suits, a machine identity | the boot sector and the loader are checked by nobody; UEFI Secure Boot; the keys kept in the machine's chip (TPM); the whole disk encrypted; one key for all builds that survives the loss of a PC (ours is in one file) |
| **Updates** | `update` from a stick, a backup of the old system | updates over the network; an update that cannot leave the machine half-done; the old systems must accept the new key (ours changed) |
| **Getting programs** | objects travel by `share`, `send`, `get`, FAT32 `files` | **!** installing and removing a program as one act; where programs come from (a store, a list); who made a program and whether to trust them (today only the build's own key); versions of a program and of the functions it needs |
| **The network** | two wired cards, DHCP, ping, Meta Net (its own pages, signed and encrypted) | **!** Wi-Fi; a way to the ordinary internet - TCP, DNS, TLS, HTTP - if not there (to be read from k_net); a firewall; the clock from the network |
| **The web** | NET shows NinuxOS pages (HTML + CSS + PyTon) | **!** the pages of the rest of the world. No other system is used without a browser. To decide: a real browser is years of work; a bridge (a relay on another machine, as Ask does) is weeks |
| **Hardware** | disks (ATA, AHCI, NVMe), USB (keyboard, mouse, stick, hub), PS/2, sound out, a framebuffer, virtio-gpu | **!** touchpads and touch screens (I2C, most laptops); graphics cards (everything is drawn by the processor); Bluetooth; cameras; microphones; printers; card readers; a second screen |
| **Power** | power off, restart, the processor's clock (Tuner) | **!** sleep and wake; the battery (how much is left, a warning); the lid; brightness; heat that slows the machine down by itself |
| **The screen** | windows, a taskbar, a start menu, themes, a wallpaper, a lock screen | letters at any size from a .ttf (now 8 by 16 dots only); screens with many dots (everything is small); notifications; drag and drop between programs; undo across the system |
| **Text and languages** | Latin and Cyrillic, EN / BG keyboards, time zones, summer time | **!** Unicode; other scripts; writing right to left; typing languages with many signs; texts of the system in other languages |
| **Media** | WAV, tones, pictures as raw dots | reading PNG and JPEG; MP3 / AAC / video; a mixer (two programs sounding at once) |
| **For everyone** | - | reading the screen aloud, a magnifier, high contrast, keys instead of the mouse everywhere |
| **When it breaks** | the shield catches a program's fault; a crash screen; a chained log; a safe start | a start that repairs (recovery) without another machine; the crash kept for later; a way back to the state as it came (factory reset) that keeps the user's objects; a watchdog for a program that hangs |
| **Hardening** | the kernel is closed to programs, only verified code on the kernel's page tables | programs always loaded at the same address (0x1400000): no randomising; no guard against a stack that overflows; data that cannot be run (to be read: is it there?) |
| **Making programs** | Studio, PyTon, `build` (numbers only), py2asm on a PC | **!** the whole of PyTon compiled inside the system; a description of every function a program may call, kept true (now it was dug out of old programs); looking into a running program; tests that run by themselves |
| **Other systems' programs** | - | nothing made for another system runs. Every new system answers this somehow: its own programs only (then it needs many), a layer for one other system, or the web as the common ground |

### What this says, in order

1. **Not losing things** - the second copy, whole writes, backup of the user's objects, the boot
   sector that Windows eats. Everything else is worthless on a system that can vanish.
2. **What a program is** - one that lives on in the background, with permissions of its own, that
   gives memory back and can be installed and removed. Socials, the keyboard on the screen, the
   governor all need this answered first; it changes the kernel, the table of functions and py2asm.
3. **The way out** - Wi-Fi, the ordinary internet, the web (bridge or browser), NTFS / ext4.
4. **Unicode and letters from a .ttf** - before more is written that assumes one byte a letter.
5. **Laptops** - sleep, battery, touchpad: without them it is a system for desktop PCs and QEMU.
6. The rest of the table.

### Claude's notes on the owner's ideas (10 October 2026)

- **An instance on every disk, a governor.** Right in direction: it is what "not losing things"
  becomes when there is more than one disk. The hard part is not copying, it is disagreement:
  two instances that each changed something while the other was not looking. Decide first what
  is the truth (the governor always wins? the newest? ask the person?), and whether user objects
  are synced or only the system. A/B systems on one disk (two copies, one known-good) give most
  of the safety on a machine with a single disk, and are the smaller first step.
- **Nothing on the desktop reaches the shell.** It is the same thing as per-program permissions
  (row "Permissions"): today the wall is missing for every program, not only for the shell. A
  keyboard on the screen that types into the shell is then simply the one program that has the
  permission "send keys to the shell" - shown, given by the administrator, taken back at will.
  Without the permissions it is a hole; with them it is an ordinary case.
- **`kill`, the desktop that closes everything, `cores solo`, `bench`** are one subject: how the
  system runs programs. Read the multiplexer in the kernel source before changing any of them.
- **At most 5 users**: easy to enforce; say what should happen to their objects when a user is
  removed, and whether the 5 include the administrator.
- **Order of work.** Nothing built since v2.9.59 has run (`docs/TESTS.md`, parts C and I). Until
  a changed kernel is seen to start, every point above that touches the kernel is a plan only.

## 4b. From the owner, 10 October 2026

- [ ] **The fonts.** `assets/fonts`: Exo (the shell), JetBrains Mono, Russo One - the originals
      of v2.9.59. Write `tools/make_font.py` again (a .ttf -> the object `font`); find out where
      the other two were used.
- [ ] `kill NAME` is useless as long as leaving the desktop closes everything (4a, "programs do
      not live on"). Decide: programs stay open across shell / desktop.
- [ ] `cores solo` and `bench`: the same results whatever is set - not as it should be (4a).
- [ ] **At most 5 users.**
- [ ] **An instance of the system on every physical disk.** If one dies another starts. One is
      the *governor*: it leads and starts first. `governor swap` makes another one the governor;
      `governor sync` brings every instance to the governor's settings and updates. To think
      through before building: who decides when two instances both claim to lead; what is synced
      (the system only, or the users' objects too); what happens to changes made on an instance
      that was not the governor.
- [ ] **Nothing on the desktop may reach the kernel or the shell.** Today `NAME` in the shell
      starts a program of the desktop (calc ...) and a program can send keys (Keys does). The one
      exception wanted: a keyboard on the screen that can type into the shell - decide how far
      that is safe (it is a program that types commands).

## 5a. New: Socials

The social network that comes with the system - a program of the desktop, written in PyTon.
Nothing is decided yet beyond that it must be made.

- [ ] What it is: people (the system already has users: `user add NAME LEVEL`), what they post,
      who sees it. Over Meta Net (`share`, `send`, `subscribe`, `broadcast` are there) or over
      a server of its own?
- [ ] What a post is: an object (DATA = the text or the picture, META = who, when, for whom,
      rating) - so that it is signed, rated and kept like everything else.
- [ ] Needs first: the network functions connected in py2asm (net_ask, net_answer, net_state),
      and Mail and Phone looked at - they already send things between machines.

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
