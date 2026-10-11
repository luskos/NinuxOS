# NinuxOS - what is left to do

State on 10 October 2026, project v3.0.39 (everything that is compiled has a source now; the build
writes the version, adds objects, signs).
Versions: v3.x.xx - a small update raises xx, a big one x. How the work goes: DIRECTIVE.md.
Order inside a part = importance.

## THE FULL TEST of 11 October 2026 (v3.0.37 -> v3.0.38): what works, what does not, how to mend it

All 30 test scripts were run in QEMU against the image, one after another:
`python test/qemu/run_all.py` (results: `test/qemu/RESULTS.md`; pictures: `test/qemu/out_all/`,
`python tools/qemu/sheet.py` puts many on one sheet). The eight scripts of v2.9.59 (shell,
checks, desktop, the programs, META, Photon, Tuner, ASMONCRAFT) and the 22 written since.

**No script ended in a fault, a stop of the system, a refusal or a wrong seal.** The one
"object fault" in the log is `shield test` doing its work; the `[ata] read error` lines are the
backup pool being looked for on a disk too small for it (see 3 below).

### Seen working (in QEMU; nothing here was seen on a real machine)

- The start with the new boot sector, the kernel with everything written since, our key; the
  Sentinel; the four suits.
- The shell's commands of v2.9.59 (the whole script), maintenance mode, copy / rename / delete.
- The old desktop with all its programs: PyNamp, NET, Studio, Search, Paint, Interfacer,
  Projector, Chronos, Device, Console, Nest, Widgets, Phone, Ask, Keys, Task test, Core test;
  Photon, Tuner, ASMONCRAFT on the whole screen.
- **All 19 programs of v2.9.59 compiled by the new py2asm** (`--compare`): each starts and draws
  its window - Ask, ASMONCRAFT (the whole 3D world), Calc, Chronos, Console, Copycat, Device,
  Greet, Interfacer, Keys, Mail, Nest, Notepad, Paint, Phone, Projector, PyNamp, Search,
  Widgets. Seen small, side by side: none is blank or broken at a glance. **Not compared key by
  key with the old ones** - that is still the owner's (docs/TESTS.md, part M).
- Written since the recovery: Alt + *, programs kept across leaving the desktop, `tasks`,
  `keyboard` and the click in the corner, `cores solo` / `bench`, `backup`, the table of the
  cabinet twice and the loader taking the copy, `desk NAME`; Bags, Files, Settings, Socials;
  Desk2 with its card, menus, bag panel, curtain, desktops, the system's menu, the screen
  split in 4; memory given back; the five dialects (on Windows).

### What does not work, or was found wrong - and how to mend it

1. **[mended, v3.0.38] Support showed one line of Puffer's text.** Not a fault of the program:
   the page itself (`pages/Donate.asmo`) held that line - it was lost before the disk was.
   Written anew, with the picture `qr_donate`. Seen.
2. **[mended, v3.0.38] The Sentinel always said "1 CHANGED"** (that same page). The build now
   makes every line of the list true by the object's name when the old sum is not found.
   The build says "0 left as they were"; to be looked at on the screen: `sentinel` should end
   with nothing CHANGED.
3. **`[ata] read error` in the log** once a session, when a program saves on a disk under
   64 MB: the backup pool is looked for by reading where it would be. Harmless. To mend: ask
   the disk for its size first (the size is known per kind of disk - to be read), or keep
   quiet about a failed read in that one place.
4. **Five people at most: not tried.** The test typed `user add ana 1`; the level must be 18,
   16, 12, 7 or 0, so nobody was added. To do: the test with a right level
   (`test/qemu/q_v3_misc.txt`), then look for "Five people are known by now".
5. **The screen split in 9: not seen.** In the test the right button on the desk did nothing,
   because a program's window had the keys: **the first click on the desk after working in a
   window only brings the desk to the front** (the multiplexer takes it; the old desktop
   behaves the same). The second click works. To mend, if the owner wants it mended: let the
   multiplexer hand that click on to the desktop as well (`mux_input`).
6. **META from the old test**: the script's two pictures show the shell with two lines, not a
   screen of META. The log says `[meta] asked for by the desktop app` and nothing after. Either
   META needs something QEMU does not have here, or it is broken since v2.9.59 (it was not
   looked at then). To do: `meta` in the shell by hand, read what it says; compare with the
   stick of v2.9.59.
7. **In a split screen nobody can work**, only look and pick (written so; TODO "24").
8. **`sources`** was not looked at after Bags was written anew (it may say OUT OF DATE: how
   the sum of a source is made is not known).
9. **The right button of the mouse arrives as 4 in QEMU**, not 2. Desk2 takes both; the old
   desktop and the programs of v2.9.59 test for 2. To see on a real mouse.
10. **Bags in the old desktop** opens on a black screen (a program without `window()` gets the
    whole screen); over the desk only in Desk2.
11. **`view`** shows only the first lines of a long text: the papers in the drawer `project`
    cannot be read whole in the shell.
12. Not tried at all, because there was nothing to try them with: a program outside the
    Sentinel's list asking for power (`api_guard` refusing); a parcel carried to a second
    machine; a USB mouse or a touch screen on the keyboard of the shell; the stick in Windows
    with the new boot sector; `--source-inside`; the vault of Bags; `update`, `uproot`, the
    network, sound; anything on a real machine.
13. Tools: `tools/kdis/handwork.py` has not been run since `kernel/New.kasm` was cut out;
    `Puffus.exe` in the project folder is still the one of v2.9.60 (close it, run
    `tools\puffus\make_puffus.cmd`).

### What to do first, when there is time again

In this order: 4 and 5 (two small tests), 6 (META), 3 (the read error), then the owner's own
round on a real machine (docs/TESTS.md, parts C, K - T).

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

## The order of work

Sorted on 10 October 2026: what matters most, gives something that works, and is the least work
comes first, so that most gets done in one go. S = hours, M = days, L = weeks, XL = more.
"kernel" = needs a changed kernel, and that waits for step 1. The parts below hold the details.

**Step 1 - the gate (the owner, `docs/TESTS.md`)**

| # | what | size |
|---|---|---|
| 1 | Parts C-G: does v3.0.10 start, are the seals right, are `pyhello` and `pycalc` there | S |
| 2 | Part I: one `nop` in the kernel - may code be added to it | S |

**Step 2 - no kernel needed: can be written now**

| # | what | size | why here |
|---|---|---|---|
| 3 | **[written, v3.0.11]** The boot sector no longer looks like a FAT12 diskette (Windows eats the stick) | S | critical, one small file we have as source |
| 4 | **[written, v3.0.11]** The build: added objects get lines in the Sentinel's list; an object or suit of another size; `objects/*.asmo.kasm` assembled into the image | M | without it nothing new is "genuine" |
| 5 | **[written, v3.0.11]** `tools/make_font.py` again (a .ttf -> the object `font`), Exo for the shell | M | the fonts are back; needed for Greek and for other sizes |
| 6 | **[done: read]** How a page finds its PyTon script and what it may call - read it from NET | S | opens the next four |
| 7 | **[v3.0.30, in Desk2: a click at the top edge brings the curtain down (tiles, what the machine is); the page stays for the rest]** **[the page is written; the pull from the top edge waits for 22]** Settings as a curtain pulled down from the top of the screen (a page: HTML + CSS + PyTon): screen, wallpaper, themes, sound, network | M | pages are source we have |
| 8 | **[written as a program (Files); as a page after 22]** A file manager that explains itself (a page / ASMO object) | M | |
| 9 | **[v3.0.30, in Desk2: a click on a bag shows what is inside in a panel over the desk]** **[v3.0.27: the icon and the panel show the things' own pictures]** **[written anew, v3.0.11; small pictures wait for 11, the tie to a drawer for the kernel]** Bags as it was meant: folders on the desktop like on a phone - a small icon that shows what is inside, a click opens it; a home for clutter in the bottom right corner | M | Bags has a source; today it only faults |
| 10 | **[v3.0.29: "Data dump" is in the context menu of Desk2]** **[written: the key D in Files; in the context menu after 22]** `data dump` in the context menu: the DATA out of an object, kept as a thing of its own | S-M | the context menu is a page |
| 11 | **[written, v3.0.13: all 20 compile and assemble; none has run]** The last functions for py2asm: images, a sound object, the network -> Paint, Nest, PyNamp, Ask compile | M | 16 of 20 programs compile today |
| 12 | **[ready: `build_disk.py --compare` puts them in a drawer `compare` as pyNAME; the owner compares]** The 20 programs compiled by the new py2asm, each beside the old one on the screen | M | proves py2asm in the system |
| 13 | **[written, v3.0.11]** At most 5 users | S | if it is a check in a program or a page; kernel if in `user` |

**Step 3 - the kernel, once step 1 has passed**

| # | what | size |
|---|---|---|
| 14 | **[done: v3.0.16 and `tasks` in v3.0.19, seen in QEMU]** Programs live on: leaving the desktop closes nothing; `tasks`; then `kill` means something | L |
| 15 | **[v3.0.35: the loader reads the copy when the table is damaged, and every writer of the table writes the copy - both seen in QEMU; a second copy of the kernel and whole-or-nothing writes of objects are not done]** A second copy of the table of the cabinet and of the kernel; writes whole or not at all | M |
| 16 | **[written and seen in QEMU, v3.0.25: saves go to a pool of 32 MB outside the cabinet; `backup`, `backup get N`, `backup clear`]** The silent backup of the user and its pool, with a manager of the pool's space | M-L |
| 17 | **[v3.0.35: a program the Sentinel does not know is refused power, the extension's services, closing and typing into other programs; the keyboard on the screen, v3.0.23; a relay object between two programs is not written]** A desktop program is handed only what it needs; relays for the rest (the keyboard on the screen for the shell is one) | L |
| 18 | **[`cores solo` / `bench` explained and changed, v3.0.21; "all cores for programs" is `cores all`, to be tried on the real machine]** `cores solo`, `bench`, all cores for programs | M |
| 19 | **[done, v3.0.20: tried on Windows and once in QEMU]** Memory given back by PyTon programs | M |
| 20 | **[read and measured, v3.0.37 - three of the four are already outside the kernel, in the suit k_tools; nothing was cut yet: see "20, read in the kernel"]** Photon, Puffer, Tuner, META out of the kernel: programs of their own | L each |
| 21 | **[v3.0.35: 91 names, and what was written after the recovery lies in kernel/New.kasm; begun, v3.0.22: 41 names (the multiplexer, the shell, objects, keys) - `tools/kdis/renames.txt`; about 900 functions still have addresses for names]** Names for the kernel's 655 functions; the kernel cut into its parts | L |

**Step 4 - the desktop itself** (Desktop has only a machine-read source: to be rewritten first)

| # | what | size |
|---|---|---|
| 22 | **[v3.0.31: Desk2 also has the system's own menu on an object (clone, rename, hide, lock, erase, share ...) - what is left is the owner's word to let `desktop` run it; all five steps have a first form, v3.0.30 (Desk2: a bag's panel over the desk, the curtain, more desktops); what is left: the system's own actions on an object, the taskbar as a page, then Desk2 in the place of the old one; steps 1-4, v3.0.29: Desk2 also has the card, the menus (with data dump), moving icons, the start menu; steps 1 and 2, v3.0.28: the new desktop Desk2 (apps/Desk2.asmo, 230 lines of PyTon) runs beside the old one - `desk desk2`; step 1 partly, v3.0.27: pictures, clip, the kept rectangle, power, calling a socket are in py2asm; begun, v3.0.26: the object read through and named - docs/DESKTOP.md has its parts and the five steps of the rewriting; no line of the new one is written yet]** Desktop rewritten as source meant to be read (PyTon + pages) | L |
| 23 | **[v3.0.30, in Desk2: up to nine desktops - `< 1/2 >`, PgUp / PgDn, an icon let go at the edge moves over; no sliding picture, no film strip yet]** More desktops: slide for a new one as on a phone; or one endless desktop that scrolls like a film strip, a column a frame, more added when needed | M after 22 |
| 24 | **[written and seen in QEMU, v3.0.32: "All at once: 4 / 9" in the menus of Desk2 - the desk and every program that runs, each in a part of the screen, made small, live; a click picks one]** The desktop split in 4 or 9 instances at once (multiboxing) | L |

**Step 5 - machines and the world**

| # | what | size |
|---|---|---|
| 25 | Touchpads and touch screens (I2C HID) | L |
| 26 | The battery meter (needs the machine's ACPI tables read and run) | L |
| 27 | **[letters 2, 3, 4 ... times as big: `text_big`, v3.0.34; Unicode, other languages and letters drawn from a .ttf at any size are not begun]** Unicode; languages; letters of any size | L |
| 28 | Wi-Fi; Bluetooth; tether from another device | XL |
| 29 | winlolz / linlolz: read NTFS, ext4 | L each |
| 30 | **[only Alt + * (the display off and on) is written, v3.0.11]** Sleep, the lid, brightness | L |

**Step 6 - what NinuxOS is for**

| # | what | size |
|---|---|---|
| 31 | **[v3.0.36: the parcel is in code - `save_object` writes an object with the envelope as its META; Socials makes and lists them; carried by the system's own `share` / `send`; signatures, closing to others, sending from the program are not there]** The protocols: messages, pictures, video, files between two programs that only share a handle | L |
| 32 | The chain of machines: each registers when installed, cloned, copied; where the data of NET and META lie | XL |
| 33 | An instance of the system on every disk; the governor (`swap`, `sync`) | L |
| 34 | The vDNA constructor: a universal one from the demo in the repository vDNA; closed programs as chains it builds into an ASMO object; an AI checks them | XL |
| 35 | **[v3.0.36: Socials is a program - your handle, writing a message as a parcel, the list of parcels from you and for you; seen in QEMU]** Socials | L |
| 36 | **[written, v3.0.33: c2asm, c++2asm, c#2asm, java2asm, js2asm - tried on Windows: one program in the five dialects prints what the Python one prints]** The other dialects over the one back end: c2asm, c++2asm, c#2asm, java2asm, js2asm - plain code only, no OOP (part 2a) | XL |

### Seen in QEMU on 11 October 2026 (v3.0.15; the owner allowed one quick test)

`test/qemu/q_v3_quick.txt`, `q_v3_apps.txt`, `q_v3_settings.txt`; pictures in `test/qemu/out_v3`.

- [x] The system starts with the new boot sector, the changed kernel (extension 158144 bytes,
      `SHA-256 ok`), our key: `sentinel` says 103 checked, 1 CHANGED (donate, as always);
      `k_tools` is taken; the added lines (curtain, files, pycalc, pyhello, socials) are `genuine`.
- [x] `run pyhello`, `run pyhello numbers`: the new py2asm's program gives exactly the expected
      lines inside NinuxOS (lists, dicts, try/except, floats, f-strings).
- [x] **Alt + \*** : the screen goes black and comes back (QEMU's adapter).
- [x] Bags: the folder icon is drawn by its socket; it opens, a thing is put in and kept, Esc
      closes **without the old page fault**, the icon then shows a tile for the thing inside.
      A program that does not call `window()` gets the whole screen, black: the panel stands
      on black, not over the desktop. A panel over the desktop needs the desktop's help (22).
- [x] Files: the list, one type only (T), what the object says of itself, `data dump` (D)
      made `donate_data`. Socials: its icon and window.
- [x] Settings: the taskbar opens only what is on the desk ("Not on the desk: curtain"), and
      the number at 0x50 of an object's header hides it when its lowest bit is set - so the
      page is on the desk now, as "Settings", and the button opens it. The tiles change the part.
- [x] `view directive` from the drawer `project` works; `view` shows only the first lines of a
      long text, so the papers are there to be kept and opened in Notepad or Studio, not read
      whole in the shell.
- Objects are read from the disk "on first use", not all at the start: a big object
  (`--source-inside`) should not slow the start. Not tried.
- Not tried: the stick and Windows (K2), five users, the vault, the drawer `compare`, a real
  machine's display with Alt + \*.

### Where the order stands after v3.0.11 (10 October 2026)

The owner's word: 1, 2 later; 3-10, 13-28, 30, 31 to be done; 11, 12 to be explained first; 29,
32, 34 stay in the list; of Socials only the empty program.

Written in v3.0.11, **none of it has run in the system** (`docs/TESTS.md`, part K): 3, 4, 5, 7,
8 (as a program), 9, 10 (in Files), 13, Alt + * of 30, the first writing of 31, the empty Socials.

Not done, and why - said plainly, so that the list does not lie:

- **14-21 (the kernel)**: programs that live on, the second copy of the table, the silent backup,
  the smaller table of functions and relays, all cores, memory given back, Photon / Puffer /
  Tuner / META as programs, names for the kernel's functions. Each is days to weeks of work
  inside code that exists only as machine-read source, and each changes how the system starts
  and runs. Writing them blind, before one changed kernel has been seen to start (tests C and
  K), would pile untested change on untested change. Alt + * is the first, small piece of code
  in the kernel and was written so that nothing else moves; if it works, the way is open.
  What can be started without the gate: 21 (names - it changes no byte).
- **22-24 (the desktop)**: Desktop has to be written anew as readable source first (22); more
  desktops and the split screen stand on that.
- **25-28, the rest of 30**: touchpads (I2C HID), the battery and the lid (ACPI: its tables hold
  code that must be run), Unicode and letters of any size, Wi-Fi and Bluetooth (each chip its
  own driver and its own firmware file), sleep. Drivers cannot be written without the machine
  to try them on: for each the owner has to name the machine and its chips (`pci`, `machine`).
- Still asked of the owner: `data dump` - today the DATA come out as a new object of the
  cabinet (NAME_data). Should they (also) go out to a stick as a file?

### Can the kernel be moved? Tried in QEMU, v3.0.17: not yet - and why

Test I of docs/TESTS.md, done with one `nop`: **a kernel in which anything moved does not run.**
New code is therefore written only at the end of the extension and reached by a call that is
exactly as long as what it stands for (Alt + *, "programs live on" were done so, and work).

- A `nop` in the **core**: `SHA-256 MISMATCH`, then a page fault. The core's size (61968) is a
  number somewhere, and the loader copies the extension by it. The core has to stay as it is.
- A `nop` at the start of the **extension**, step by step:
  1. stopped at the first command that used a table: 23 instructions held addresses of the
     kernel as numbers (`mov [rcx*8+0x5b920],rax`). Named (`tools/kdis/numbers.py` finds them).
  2. then stopped when the desktop started: the multiplexer's table of the 18 system functions
     it takes over, and 4 pointers of the table of the kernel's small PyTon, lay as plain
     bytes. Named (`tools/kdis/pointers.py`).
  3. now the system starts, the shell works, the desktop starts - and the screen is garbage.
     What is left: **code that was never read as code** (44% of the kernel is still rows of
     bytes, and part of that is code: the functions the two tables above point at, for one).
     Its jumps and calls are bytes, so they do not follow when something moves.
- [x] v3.0.18: done for the extension. The kernel was read again by `tools/kdis/kdis.py` with
      what was learned: `tools/kdis/pointers.txt` (22 pointers to code in the data),
      `tools/kdis/seeds.txt` (77 places where code starts that nothing visible calls - the drawing
      of the graphics adapter, a driver, the stubs of the interrupts, the small PyTon's helpers),
      `tools/kdis/names.txt` (every name already in use, so nothing was renamed). 58.8% of the
      kernel is code now (was 55.6%), 33326 instructions. `tools/kdis/handwork.py` then puts the
      code written by hand back and checks that the kernel is the very same bytes.
      **Tried in QEMU: with one `nop` at the start of the extension (4117 names moved) the system
      starts, the shell works, the desktop draws, Bags, NET, Calc, Socials open and close.**
      So code may now be written anywhere in the extension, not only at its end.
- [ ] Still true: the **core** must not change size (61968 is a number the loader uses, and the
      16-bit loader is in it). And "moved runs" was seen for the start, the shell, the desktop
      and four programs - not for Photon, META, the network, sound, USB, `update`. A function
      that nothing has reached yet may still hold a jump as bytes: after a change that moves
      code, what was not tried has to be tried.
- [ ] A test that says it without a machine: every row of bytes in the extension judged by
      reading it as code (done by hand this time: 4 runs were left, now 0) - as a tool.
- All three steps left the kernel the same bytes; nothing of this changed the image.

### 14, read from the kernel (v3.0.14): how programs run side by side today

The multiplexer is one loop in the extension (`L_53d40`, where the texts `[mux] multiplexer on`
and `off` are). It is entered when the desktop starts and left when the desktop ends:

- eight places for tasks (`fn_53fdf` gives the record of place n; its first number is the state:
  0 free, 1 running, 2 to be closed); the desktop is task 0;
- the loop: the housekeeping, then for every task that runs one turn (`fn_540e7`), then - as
  long as task 0 still runs - again;
- when task 0 has ended: **every other task is marked "to be closed"**, the memory of the
  multiplexer is given back, `[mux] multiplexer off`. Starting the desktop again wipes the
  table of tasks (`fn_53f25` clears 0x1000 bytes at 0x43F60).

So "leaving the desktop closes nothing" is three changes, and each has to be seen working:

- [x] v3.0.16: the end of task 0 no longer closes the others when some still run; their
      records, memory and windows stay (they get no turns while the shell has the screen);
- [x] v3.0.16: the next start of the desktop does not wipe the table; the desktop goes under
      the kept windows and the keys go to the window that was on top. The desktop needed no
      telling: it asks the multiplexer for the tasks. Seen in QEMU (`test/qemu/q_v3_live.txt`):
      Files left open, to the shell, `mem`, `desktop` - Files is there with the same line
      chosen, takes keys, closes with Esc; leaving with nothing open ends as before.
- [x] v3.0.19: `tasks` in the shell lists the kept programs (number, name); `tasks close N`
      closes one and gives its memory back; when the last is closed the multiplexer's own memory
      goes too. Seen in QEMU (`test/qemu/q_v3_tasks.txt`). The shell's table of commands is in
      the core, which cannot grow: the shell now asks `shell_more` (in the extension) about a
      word it does not know, before it looks for an object of that name - new commands go there.
      `help` does not list `tasks` (its text is in the core too).
- [x] v3.0.21: the room for new kernel code, looked at. 0x78000 was only what the crash screen
      takes for "an address of the kernel" when it lists the calls (now 0x80000). The real
      limits: the first suit lies at 0x80000, and the boot sector reads 480 sectors of kernel.
      The kernel is 221248 bytes of 245760: **about 24 KB are left** (the build stops if the
      extension would reach 0x80000). More than that needs the boot sector to read more
      sectors and the table of the cabinet to lie further on.
- [ ] Not tried: several kept programs at once, a full-screen one (Photon), `cores all`,
      what `update`, `maint` and `shutdown` do while programs are kept.
- Later, for relays and music: turns also while the shell is in front, with drawing held back.

Not written blind: it changes what happens at every start and end of the desktop.

### 15, what is done and what is not (v3.0.24)

- [x] The table of the cabinet is written twice: a copy in the four sectors right behind it
      (485-488; the objects start at 490), the copy first, then the table - if the power goes
      during either writing, one of the two is whole. The build writes both. Seen in QEMU:
      `copy hello hello2` in maintenance mode, then both tables on the disk hold 54 objects
      and are the same. `python tools/table_copy.py check|restore DISK` looks at them and puts
      the copy back from another machine.
- [x] v3.0.35: **the loader reads the copy.** When the first sector of the table is not a
      table, it reads the one 4 sectors on, once, before saying "No cabinet found". The room
      for it in the loader was made by making two of its texts shorter (the start now says
      "NinuxOS v3.0.35 ...." without "- loading cabinet", and "Video." for "Starting
      graphics..."). Seen in QEMU: an image whose sector 481 was wiped starts with all 122
      objects; before, it came up with none.
- [x] v3.0.35: **every writer keeps the copy.** The copy is now written by the function all
      reading and writing of the disk goes through (`disk_io`), whenever it is asked to write
      a table to the table's sector - so `update`, the installer and anything else do it too,
      without having been read.
- [ ] Found on the way: why the core cannot grow - at `NINUX-EXT-LOAD::` the loader keeps
      0x17010, where the extension lies in memory before it is moved (0x7E00 + the size of the
      core), as a number. Written as a name there, the core could be let grow and be tried.
- [ ] A second copy of the kernel on the disk, and a boot sector that takes it when the first
      does not check: not begun.
- [ ] An object is still written over its old place: a cut during that loses the object. The
      whole answer is "write the new one elsewhere, then change the table" - the table being
      safe now is the first half of it.

### 16, the silent backup: what is there and what is not (v3.0.25)

- [x] Every object a program saves (api_ob_save) is written at once a second time into the
      **backup pool**: 32 MB of the disk, 32 MB from the start of the system - outside the
      cabinet, so what happens to the cabinet does not happen to it. Nothing is asked, nothing
      is said, no maintenance mode is needed. A full pool begins anew at its start (the oldest
      saves are written over). A disk under 64 MB has no pool and saving works as before.
- [x] The manager: `backup` (a line a save: number, name, size; how much of the pool is used),
      `backup get N` (that save back into the cabinet, under its name), `backup clear`.
      Seen in QEMU on a 70 MB image (`test/qemu/q_v3_backup.txt`): two saves of Bags listed,
      the first brought back; on the 23 MB image: "No backup pool here", nothing breaks.
- [ ] The pool has one fixed place and size. "A pool of changing size" and a place at the end
      of the disk need the size of the disk, which the kernel knows differently for each kind
      of disk (ATA, AHCI, NVMe, USB) - to read. Until then: the cabinet must stay under
      sector 65536 (it is at 14100; the build stops there, the system itself does not check).
- [ ] What a save shows: its name and size. The clock is kept with it (ticks since the start)
      but not shown; the date is not kept. After the pool began anew, only the saves of the
      present round are listed.
- [ ] Only saves of programs (api_ob_save). What the shell does to objects in maintenance mode
      (`copy`, `rename`, `delete`, `inject`) does not pass it.
- [ ] `backup get` puts the save over the object of that name; "as another name" is not there.
- [ ] Puffus does not know of the pool: writing a new system to the stick leaves the pool where
      it is (the image is 23 MB), which is right - but nothing tells the user it is there.

### 24, the screen split in 4 or 9: what is there and what is not (v3.0.32)

- [x] In the multiplexer (`split_service`, `split_step`, `split_show`): while the screen is split
      the multiplexer draws as always, but into memory of its own; 25 times a second every
      task's picture is drawn into its part of the real screen, made small to fit and in its
      shape (never bigger than it is). The programs go on running and are seen live. A click
      on a part makes the screen whole with that program in front; ESC makes it whole as it
      was. Asked for by the programs function, number 0x0F; `split(4)`, `split(9)`, `split(0)`
      in PyTon; "All at once: 4 / 9" in the menus of Desk2.
- [ ] One cannot *work* in a part: keys and the mouse do not reach the programs while the
      screen is split - it is for looking and picking. Working in a part needs the mouse's
      place turned back into the place in the program's own window.
- [ ] At most eight parts are ever filled (the desk and seven programs): the multiplexer has
      eight places. More instances - nine camera pictures, say - need more places.
- [ ] A part shows a program's window, not a desktop of its own: "each on its own desktop,
      full screen" (the owner's example) would be programs that take the whole screen each.
- [ ] No name under a part; the mouse is a plain square there.

### 17, what a program is handed (v3.0.35)

- [x] `api_guard`, in the one place every call of a program passes (the gate of interrupt
      0x80): a program whose code is not in the Sentinel's list is refused, with -1 and a line
      in the log - power off and restart; the services of the kernel's extension; closing
      another program, sending it keys, parking it, splitting the screen. Programs of the
      build are in the list and are handed everything, as before (seen in QEMU: the old
      desktop's programs and Desk2 work with it). The refusal itself was not seen: there is no
      program outside the list in the image to ask.
- [ ] It is the same table for all, with a few places closed to strangers - not yet "each
      program its own small table". Saving over another program's object is still judged by
      api_ob_save's own rules, which were not read.
- [ ] A relay between two programs: `ob_call` reaches a socket of another object, but a relay
      object that carries a parcel from one running program to another (docs/PROTOCOLS.md)
      is not written - it needs to be known what a called object remembers between calls.
- [ ] The keyboard on the screen: Cyrillic, Ctrl and Alt are not on it.

### 21, names and parts (v3.0.35)

- [x] 91 names now (`tools/kdis/renames.txt`): the multiplexer, the shell, objects, keys, and
      new: the disk (`disk_io`, `disk_read`, `disk_write`), the console (`console_rows`,
      `console_scroll` ...), the screen (`screen_memory`, `screen_width` ...), the loader
      (`load_table`, `load_sectors`), the functions a program is handed that were read for the
      desktop (`api_image`, `api_image_fit`, `api_ob_call`, `api_cabinet_facts`, `api_extension`).
- [x] The first cut of the kernel into parts: everything written after the recovery is in
      `kernel/New.kasm` (1557 lines, each part with what it is for), included by Kernel.kasm;
      Kernel.kasm is the kernel of v2.9.59 with the places that call into New.kasm.
- [ ] About 850 functions still have addresses for names; Kernel.kasm itself is one file of
      50000 lines - cutting it by what the code does (the loader, the console, the cabinet,
      the multiplexer, the drivers) is the next cut, when more of it has names.
- [ ] tools/kdis/handwork.py has not been tried since New.kasm was cut out and the loader's
      texts were changed; it must be before the kernel is read again by kdis.py.

### 20, read in the kernel (v3.0.37): where Photon, Puffer, Tuner and META really are

What was said before - "they are functions inside the kernel" - was wrong for three of the four.
Read now, from the objects on the desk down to the code:

- The four objects on the desk (`photon`, `puffer`, `tuner`, `metaspace`, 1024 bytes each) only
  *ask*: they call the place +0x148 of the system's table with a number. The kernel notes it
  (`desk_asks`), the desktop leaves the screen, and the shell's loop runs what was asked.
- **Puffer, Tuner and META are not in the kernel.** They are in the kernel suit `k_tools` - an
  object of the cabinet, signed, 41 KB, put on at 0x30000 when first needed (`suit_load`).
  `k_tools` has 21 entries: update, Puffer (2), files, META (2), bench, shot, tune (4: the
  command and the TUNER screen), the chain (3), uproot and root, users, login, build refresh,
  the keyboard test. So they are in an object already - but one object for 21 things, built
  for one fixed address, calling the kernel by its addresses (Kernel.sym.inc).
- **Photon is in the kernel**: its starter `photon_run` (601 bytes of its own) and the engine
  it draws with, in the SUB-GPU part of the extension (about 3.2 KB of code and 4.6 KB of data
  that nothing else uses).
- Measured with the new `tools/kdis/own.py` (what belongs to one entry only):
  Puffer 1.3 KB of code + 1.1 KB of data; the TUNER screen 2.8 KB + 1.3 KB (and it shares
  functions with the `tune` command); META 0.4 KB + 0.5 KB - it is only the starter of
  "full-screen programs", Photon among them.

What "each a program of its own, independent of everything" then asks for, in order:

- [ ] A fifth, sixth ... kernel suit: `suit_load` knows four by number, from tables in the
      extension (names, places, greatest sizes). More suits need those tables longer and
      free places in memory for them (what lies free between 0x3B000 and 0x41000, and above
      0x8C000, is to be read).
- [ ] Tuner first (it is the cleanest): its entries of k_tools cut out into `k_tuner`, built
      for its own place; the four small functions of the kernel that jump into k_tools for
      it turned to the new suit. The source of a suit has never been tried at another
      address than its own (as the kernel's had not, before v3.0.18) - that is the test.
- [ ] Then Puffer, then META; then Photon out of the extension (the engine with it).
- [ ] The further step - not a suit but an ordinary program, as Bags and Files are - is
      possible only for what needs nothing but the table programs are handed. Tuner sets the
      processor's clock, Puffer writes sticks sector by sector: they need the kernel's own
      functions, so they stay suits (kernel parts as objects, KASM) unless those functions
      are opened to programs - which the owner's rule "nothing on the desktop reaches the
      kernel" speaks against. META and Photon draw and take keys: they could be programs.
- Not done in v3.0.37: none of the cutting. It was measured, not moved.
- **Decided by the owner, 11 October 2026:** what needs the kernel's own functions (Tuner,
  Puffer) becomes a kernel suit of its own - that keeps "nothing on the desktop reaches the
  kernel"; META and Photon may become ordinary programs. Left in the list for later.

## If the disk is lost again - where everything is

- **Inside the system itself (v3.0.12):** every build puts a drawer `project` into the cabinet
  with the texts `changelog`, `todo`, `directive`, `protocols`, `tests` (`view todo`) and the
  sources of the programs written since the recovery. So the last stick always holds the last
  state, even without git.
  The whole source and the conversations (19 MB) go in as the object `nxsource` only with
  `python tools/build_disk.py --source-inside`: it is not known whether the system reads every
  object into memory when it starts - an object that big has to be tried once (does it start,
  how long does it take) before it becomes the rule. Until then the whole source is on every
  stick where Puffus writes it: 1 GiB from the start.

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

## 2a. New: the other dialects - c2asm, c++2asm, c#2asm, java2asm, js2asm (the owner, 11 October 2026)

An idea at first; **written in v3.0.33** - see "What is there" at the end of this part.

Back-end languages only. Each is supported the way PyTon is: **as a dialect** - the way of
writing - and not as that language's own machinery. If `2 + 2` is written in any of them the
way that language expects, the assembly underneath is the same that py2asm gives. Not the
language's runtime, not its libraries, not its way of talking to the processor.

And only the plain way of writing code: values, names, arithmetic, conditions, loops, functions,
lists and tables, texts. **No classes, no interfaces, no abstractions, no polymorphism** - none
of the machinery of OOP. This is object programming (the ASMO object: DATA + META + sockets),
not object-oriented programming. The same rule py2asm already keeps ("no `class`", DIRECTIVE.md).

What that means for the work (Claude):

- [ ] One back end for all. Today py2asm goes Python text -> Python's own tree (`ast`) -> NASM
      in one file. To be split: a front end a dialect (text -> a small common tree of
      statements and expressions), and the one back end that exists (the tree -> NASM, the
      prelude, the runtime, the Windows and NinuxOS targets). The common tree is what py2asm
      already handles: assignment, the operators, `if`, `while`, `for`, functions, calls,
      lists, dicts, texts, `try`.
- [ ] A front end is then a parser only: `c2asm`, `c++2asm`, `c#2asm`, `java2asm`, `js2asm`.
      Each needs its own parser written by hand (Python's `ast` reads only Python).
- [ ] To decide a dialect: what the types written in C, C#, Java mean (`int x = 2;`) - a note
      that is checked, or nothing (values stay as they are in PyTon: whole numbers of any use,
      floats, texts)? What `{ }` objects of JavaScript are - the dict. What a C pointer or
      array is - probably the list, and no address arithmetic.
- [ ] What is refused, with a clear message, as `class` is today: `class`, `struct` with
      methods, `interface`, `template`, `new` of a class, inheritance, `this`.
- [ ] The system functions (fill, text, window, poll ...) and META are the same names in every
      dialect; a program's sockets are its functions, as in PyTon.
- [ ] A test like pyton/test.py: the same small program written in every dialect must give
      the same assembly, or at least the same output.

### Memory that comes back (v3.0.20)

- [x] `pyton/runtime.inc`: every block has 16 bytes in front (its size, a mark); when a chunk of
      1 MB is full the runtime looks for what is still pointed at - from the stack, the
      registers, the program's own data, then from block to block - and the rest is free and
      used again first. It does not need to know what is a pointer (any 8 bytes that hold the
      address of a block count), so nothing in py2asm or the prelude had to change.
- [x] Tried: `python pyton/test.py` (the new `examples/garbage.py` makes and drops about 160 MB
      and must end having asked the system for less than 48 MB; it asks for a few), and
      `python pyton/test.py --stress` (a look before *every* block: both big examples still
      give what Python gives). In QEMU: Bags, Files, Socials with the new runtime.
- [ ] It costs time: garbage.py takes 1.6 s, 0.6 s without giving back. The free blocks are one
      list searched from its start; lists by size would be faster.
- [ ] `nasm -DRT_NO_GC` builds a program that never gives back, as before - if a program
      misbehaves, this tells whether the memory handling is the reason.
- [ ] pyhello and pycalc in build/add are still the objects compiled in v3.0.02 (old runtime).
- [ ] Known and accepted: a number that happens to equal the address of a block keeps that
      block; more than 256 chunks and nothing is given back any more.

### What is there (v3.0.33)

- [x] `pyton/clike.py` reads C, C++, C#, Java and JavaScript - one reader for the five, since
      they write statements the same way - and turns the text into PyTon, which py2asm compiles.
      So the back end is one, and `2 + 2` gives the same assembly whatever it was written in.
      `python pyton/c2asm.py prog.c`, `c++2asm.py`, `c#2asm.py`, `java2asm.py`, `js2asm.py`
      (the same options as py2asm: `--target ninux`, `--name`); `clike.py --show FILE` shows
      the PyTon a text becomes.
- [x] What may be written: names and values, arithmetic, comparisons, `&& || !`, `?:`,
      `++ -- +=`, `if / else`, `while`, `do-while`, `for`, `break`, `continue`, `return`,
      functions, arrays (lists), texts, printing in each language's own way (printf, cout <<,
      Console.WriteLine with `$"..."`, System.out.println, console.log with `` `...${x}` ``).
- [x] The decisions asked for above, as made: the types written in C, C#, Java are read and
      decide two things only - `/` between whole numbers divides whole (not in JavaScript),
      and `+` with a text joins. An array is a list; `new int[n]` is n zeros. A letter in
      quotes in C is its number. `{ }` objects of JavaScript are not read yet.
- [x] Refused, with a line that says why: `class` with things of its own, `struct`,
      `interface`, `template`, inheritance, `new` of a class, `this`, `switch`, `try`.
      In C# and Java the one class the language demands around `main` is read as a wrapper.
- [x] `python pyton/test_dialects.py`: `examples/dialects/same.c .cpp .cs .java .js` against
      `same.py` - 5 of 5 print the same; three texts that must be refused are.
- [ ] Not there: `switch`, `struct` as a plain record (a dict), JavaScript's `{ }` and
      `for ... of`, C's pointers, `++` inside an expression, `printf` widths (`%5d`, `%.2f`
      print the plain value), what a function gives back when its type is not written (JS).
- [ ] A program of NinuxOS written in one of them (a window, keys) has not been tried: the
      system's functions are called by the same names, so it should compile as it is.

### 27, letters and languages: what is there and what is not (v3.0.34)

- [x] `text_big(x, y, text, colour, times)` in PyTon: the system's letters (8 x 16 dots, the
      object `font`) drawn 2, 3, 4 ... times as big - a square of dots for every dot. Used for
      the clock of Desk2's curtain and the title of Socials. Seen in QEMU. No kernel change.
- [ ] They are the same letters made of bigger dots: at 3 times and more they look blocky.
      Smooth letters of any size need them drawn from the .ttf itself (a rasteriser in the
      system), or tools/make_font.py making a second, bigger font object (16 x 32) on the PC.
- [ ] Unicode: a letter is one byte everywhere (Windows-1251: Latin and Cyrillic). Greek,
      which the names of files want (part 6), and every other script need either more code
      pages (a font object each, a line of META saying which) or texts of two bytes a letter
      through the whole system - the second is the real answer and touches everything.
- [ ] The system's own texts are English, written into the kernel and the programs. Other
      languages need them out of the code: a text object a language, looked up by a key.

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

**Read 4d with this: the owner answered it.** Installing programs, permissions and the web are
not goals of NinuxOS - the rows stay as a record of how the other systems do it.

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
- **Nothing on the desktop reaches the shell.** Not by permissions (the owner: no such thing,
  4d) but by what a program is handed: a smaller table of functions, and relays for the rest.
- **`kill`, the desktop that closes everything, `cores solo`, `bench`** are one subject: how the
  system runs programs. Read the multiplexer in the kernel source before changing any of them.
- **At most 5 users**: easy to enforce; say what should happen to their objects when a user is
  removed, and whether the 5 include the administrator.
- **Order of work.** Nothing built since v2.9.59 has run (`docs/TESTS.md`, parts C and I). Until
  a changed kernel is seen to start, every point above that touches the kernel is a plan only.

## 4d. The owner's answer to 4c, and what to build (10 October 2026)

**Decided - how NinuxOS is meant, where it is not like the other systems.** (Also in
DIRECTIVE.md. Three rows of the table in 4c were written against these and are wrong as goals:
"Getting programs", "Permissions", "The web".)

- **No installing.** A program is an ASMO object and carries everything it needs. Send it to
  someone and it runs; `erase` removes it. There is nothing to install or uninstall.
- **No permissions to ask for.** A program does its work and asks for no access. There are no
  administrator levels, no CMD / PowerShell, no pyramid: the shell is for the system's settings
  and functions, the desktop for programs, NET for the internet, META for games, 3D-accelerated
  programs and, later, intelligences. If a program needs another program or its data, the answer
  is a **relay** (a bridge program) between them, not a question to the user. Asking and being
  told "yes" guarantees nothing about what is then done with the data.
- **Open by presumption.** `view` on an object must show all of it: the whole code and all the
  data. The commercial case is the vDNA project: the data become virtual DNA-string chains that
  a constructor loads, so the code cannot be read because the object is not loaded the same way.
  Later even these chains are to be opened to ASMO code - probably by an AI, to verify a program
  before it spreads.
- **No web, no browser.** NinuxOS does not show the ordinary internet. NET is a super-cluster of
  machines that run NinuxOS. What matters is **protocols**: my messenger and your "lessenger"
  look different and speak the same protocol for messages, pictures, video, files; we know each
  other's handle. No cookies, no caches of other people's content, nobody's machine used as
  somebody's server.
- **The infrastructure of NET and META** lies in immutable blocks of space on the machines of
  the people (perhaps optional). Every NinuxOS machine registers when it is installed, cloned or
  copied - each for the next - and together they form an immutable chain that says where the
  data of NET and META are to be fetched from. Infrastructure node servers may exist; like the
  disks, they keep copies and can start from a copy. The space is set apart for the
  infrastructure only - not a mine for corporations.
- **Trust** is the build's key for now; later programs come from NET.
- **Ask** is the channel to intelligences: a relay with API keys, so that no browser is needed.

**To build:**

- [ ] **`data dump`** - a function of the context menu that was understood wrongly before and is
      not there: take the DATA out of an object and **keep it on the disk as a thing of its
      own**; the object is freed of it, the data are not deleted. Example: an interface object,
      a button, with a picture in it - `data dump` and the PNG that was inside is there by
      itself. (`dropdata` deletes; this does not.)
- [ ] **Silent backup of the user.** A backup pool, perhaps of changing size; a manager of the
      pool's space.
- [ ] **Touchpads and touch screens** - critical (agreed with 4c).
- [ ] **Languages**, as a system is expected to have them (with Unicode, 4c).
- [ ] **The battery**: a meter.
- [ ] **Settings**: the screen (wallpaper, themes), sound, the internet, Bluetooth, Wi-Fi, a
      direct tether from another device.
- [ ] **A file manager** that explains itself - an ASMO object made of HTML + CSS.
- [ ] **The desktop split** (multiboxing, as the word is used in Eve Online): one screen shared
      by 4 or 9 instances at once, each separate, all watched together as if they were 4 or 9
      machines, any one picked to work in. Example: camera feeds, each relayed through META or a
      program of one's own, full screen on its own desktop.

**What follows from the decisions (Claude):**

- "No permissions" and "nothing on the desktop reaches the shell" (4b) are met the same way: not
  by asking, but by what a program is *given*. Today every program is handed the whole table of
  the system's functions - saving over any object, starting and closing programs, sending keys.
  The table for a desktop program has to hold only what a program needs for its own work; the
  rest moves into relays. The keyboard on the screen for the shell is then a relay.
- A relay needs programs that live on (4a) - it has to be there while two others talk.
- "Programs come from NET" and "open by presumption" need `view` to show code as something a
  person or an AI can read - the same work as the source of the compiled objects (part 4).
- The chain of machines starts from what exists: `whoami` already keeps an ID, a generation, a
  parent and how many clones were made; the chained log is there.

## 4f. More from the owner, 11 October 2026

- [ ] **Two laptops joined by a USB-C cable** - a protocol of our own. The owner's design: the
      two do not play ping-pong (as `ping` does) but **check-mate**: a relay keeps count of
      which way the data go, and step by step the two change places - one sends while the
      other takes, then the other sends while the first takes (+/-, then -/+).
      What it stands on (Claude): on a plain USB cable one end must be the *host* and the other
      the *device* - that is why two ordinary laptops do nothing over it, and why Thunderbolt /
      USB4 can (there both ends are equals). USB-C itself has the swap the owner describes:
      the two ends can change who is host and who is device over the cable's own wire
      ("data role swap"). But the end that becomes the device needs a controller that *can*
      be a device, and most laptop ports are host only. So: possible where both machines have
      a port that can be either (to be read from each machine: `pci`, `usb`); not possible on
      host-only ports whatever the protocol. The half-duplex turn-taking itself - who sends
      now - is ours to design freely once a link exists; it fits docs/PROTOCOLS.md part 4
      as a fourth way for a parcel to travel.
- [ ] **A screen saver as in the film The Matrix** (the owner, 11 October 2026): the threads that
      fall from the top of the screen are the *real* processes of the kernel as they run -
      what the system is doing, written as the falling code.
      What it can be made of (Claude): the multiplexer knows which task has the turn and how
      many turns each has had (`mux_turn`, the record of a task); the log is a stream of real
      lines; the functions a program calls pass one gate (`api_guard` stands in it). A column a
      task, a letter for every call it makes, its speed the task's turns - nothing invented.
      It needs a place in the kernel that counts what passes the gate, and a program that
      draws; it comes on when no key and no mouse came for a while (Alt + * is the screen
      going dark; this would be the other choice).
- [ ] **Zipper** (the owner, 11 October 2026): everything of the system kept packed and
      ready; what is asked for is unpacked at that moment and started. If unpacking is nearly
      instant, everything that is not in use waits packed - and the whole becomes very small.
      "Dynamic zipper". Perhaps a function of the shell in the kernel.
      **Can it be done? Yes** (Claude), and the system is already half built for it:
      - Objects are not read at the start but "on first use" (the log says
        `[room] loaded on first use: NAME`). That one place - where an object is read from the
        disk when first asked for - is where it would be unpacked. Nothing else has to know.
      - Measured on the PC (v3.0.36): the 122 objects of the cabinet are 4.35 MB; packed they
        are 1.34 MB - **31%** (the wallpaper 1325 KB -> 524 KB, a picture 317 -> 39, a program
        of 128 KB -> 41). That is with zlib; the kind of packing that unpacks fastest (LZ4:
        about fifty lines of assembly, hundreds of MB a second) packs a little less, perhaps
        40%.
      - The steps: (1) the build packs each object and marks it packed in the table; (2) the
        kernel unpacks in the "first use" place - the Sentinel checks the object *after*
        unpacking, so the signed list stays as it is; (3) what the system itself saves is
        written unpacked at first, packed later; (4) "dynamic": an object not used for a
        while is dropped from memory and read again packed when asked for - this needs to
        know when an object is no longer in use, which the multiplexer knows for programs.
      - What has to be looked at: everything that reads an object's bytes straight from the
        disk without the "first use" place (`scan`, `recover`, `update`, the loader, which
        reads every object named in the table at the start - so the loader must unpack too,
        or the packed ones must be left for the kernel).
- [ ] **NET Express** - a program for making content for NET. With ready templates that do what
      the big ready systems do - a blog, a vlog, a shop - so that someone drops a whole site
      in at once. Not to be thought through yet.
- [ ] **Fast Reels** (the name is a first try) - a social network / widget of the kind of
      TikTok, in its dimensions and with its functions: everyone puts up what they want. And
      something like Instagram. Not a priority now. (With Socials and the protocols, part 5a.)

## 4e. More from the owner, 10 October 2026 (third)

- **Bags are folders, as on Android:** a small icon that shows what it holds; a click and the
  programs inside are there. That is what Bags is for: when the desktop is cluttered everything
  goes inside. A place for it in the bottom right corner.
- **More than one desktop.** Either: slide, as on a phone, and a new desktop opens. Or: a
  parallax desktop without an end, scrolled like a film strip - every column one frame of the
  strip, more added when needed.
- **Settings as the curtain of a phone**, on the PC too: pull the top of the screen, it comes
  down, pick the setting.
- **vDNA is the form for closed code.** A universal constructor will be made from the demo that
  is in git (the repository vDNA). A program or a file in this form cannot start by itself: it is
  like a strand of DNA with the materials needed to make the program object, without showing
  them to the user. The constructor makes it and starts it - and what it makes is again an ASMO
  object. Because users cannot see the code, programs and files in this form are checked by an
  AI for anything wrong.
- Open question (Claude): `data dump` - do the data come out as a new object in the cabinet, or
  as a file to the outside (a stick)? The PNG example fits both.

## 4b. From the owner, 10 October 2026 (first notes)

- [ ] **The fonts.** `assets/fonts`: Exo (the shell), JetBrains Mono, Russo One - the originals
      of v2.9.59. Write `tools/make_font.py` again (a .ttf -> the object `font`); find out where
      the other two were used.
- [ ] `kill NAME` is useless as long as leaving the desktop closes everything (4a, "programs do
      not live on"). Decide: programs stay open across shell / desktop.
- [x] `cores solo` and `bench`: the same results whatever is set. Found and changed in v3.0.21:
      `cores solo` (and `cores one`, `cores all`) were *refused* outside maintenance mode ("This
      changes the cabinet: enter maintenance mode first"), because the setting is kept in the
      table of the cabinet - so nothing was set, and `bench` measured the same thing. Now the
      setting is made for the session at once; only keeping it on the disk needs `maint`.
      In QEMU with 4 cores: shared work 130 ms against 420 ms on one core; after `cores solo`
      410 ms. The sharing itself works. On the owner's machine: run `cores` and `bench` again -
      if lines 7 and 8 are still alike there, `cores` says why (a core that did not answer).
- [ ] **At most 5 users.**
- [ ] **An instance of the system on every physical disk.** If one dies another starts. One is
      the *governor*: it leads and starts first. `governor swap` makes another one the governor;
      `governor sync` brings every instance to the governor's settings and updates. To think
      through before building: who decides when two instances both claim to lead; what is synced
      (the system only, or the users' objects too); what happens to changes made on an instance
      that was not the governor.
- [x] v3.0.23: **the keyboard on the screen of the shell** - `keyboard` puts five rows of keys on
      the bottom 11 lines (the text keeps to the lines above), a click types the key, Shift
      holds for one key; `keyboard` again takes it away. It is part of the system, switched on
      by the shell itself - not a program of the desktop that was given the way to the shell.
      Seen in QEMU with the PS/2 mouse (`test/qemu/q_v3_keyboard.txt`).
      Not there: Cyrillic on it; Ctrl and Alt keys; a USB mouse and a touch screen were not
      tried (their clicks come the same way out of api_poll, so they should work); a machine
      v3.0.24: a click in the bottom right corner of the screen (32 dots) brings it, so a
      machine with no keys at all can call it. (No mouse arrow is shown in the shell while
      the keyboard is off - with a finger that does not matter, with a mouse one aims blind.)
- [ ] **Nothing on the desktop may reach the kernel or the shell.** Today `NAME` in the shell
      starts a program of the desktop (calc ...) and a program can send keys (Keys does). The one
      exception wanted: a keyboard on the screen that can type into the shell - decide how far
      that is safe (it is a program that types commands).

## 5a. New: Socials

v3.0.11: the empty program is in the cabinet (`apps/Socials.asmo`), and the protocols it is to
speak have a first writing: `docs/PROTOCOLS.md`.

v3.0.36: **Socials is a program** (190 lines of PyTon, seen in QEMU). Your handle is
NAME@MACHINE (the name from Settings; eight letters made from the object `machine`). A message
is written as a parcel - the object `p_ID`, its DATA the text, its META the envelope of
PROTOCOLS.md (type:parcel, proto:nx.msg/1, kind:text, from, to, time, id, charset). It lists
every parcel in the cabinet that is from you or for you; Enter on one from someone else puts
its sender into "to". A parcel is carried to another machine by what the system already has
for objects (`share p_ID`, `send`, a stick) - that journey has not been tried.
- [ ] Not there: sending from the program itself (the network functions of py2asm are
      connected but not tried); `sig` (the kernel keeps Ed25519 to itself - a place in the
      table programs are handed is needed); parcels closed to others; pictures, files, video;
      groups; the list of known handles; more than the first six parcels on the screen.
- [ ] In QEMU the machine gets a new identity at every start (nothing is written to the
      image), so the handle changes there; on a real machine it stays.

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

- [x] `tools/make_font.py` (v3.0.11): a .ttf -> the object `font` (8 x 16 dots, Windows-1251).
      `python tools/make_font.py Exo-Medium` writes build/font/ and a preview; `--use` puts it
      into the next build; `--back` takes it out. Exo has letters of different widths: in a
      cell of 8 dots it comes out small - look at the preview before `--use`.
      Open: does the shell draw with the object `font` or with letters inside the kernel?
- [ ] The build: the hash a source object carries (`hash:`, 12 hex letters) and its program
      (`source_hash:`) - how it is computed is not known; `sources` may call Bags OUT OF DATE.
- [ ] The build: how many lines the Sentinel's list may have (the kernel's limit is not read;
      103 now, 98 before).
- [x] The build makes kernel/Kernel.sym.inc anew from the kernel it has just assembled
      (v3.0.14), so the suits follow when code is added anywhere in the kernel. Tried on the
      PC with one `nop` under `cmd_version`: 1419 names moved, the four suits assembled against
      them. Whether such a kernel also *runs* is still test I of docs/TESTS.md - data of the
      kernel may hold addresses that are still numbers.
- [x] `tools/kdis/rename.py` + `tools/kdis/renames.txt` (v3.0.22): a line "OLD NEW ; what it
      does" and the name is changed everywhere - the kernel, Kernel.sym.inc, the suits,
      names.txt - with the comment above the function; the kernel and the suits must stay the
      same bytes or everything is put back. This is how item 21 goes on: every time a function
      is understood, one line.
- [ ] says.py takes only fn_, cmd_, api_, entry_ for the start of a function: one that got a
      real name is no longer a start for it. To change before says.py is run again.
- [x] `tools/kdis/says.py` (v3.0.14): above every function of the kernel and the suits, the
      texts it points at (299 of 940 functions have some) - a first step to names (21).

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

- [x] Bags: a page fault when it is closed with Esc. v3.0.11: Bags is written anew (a folder, as
      on a phone) and compiled by the new py2asm; whether the fault is gone is to be seen.
- [x] Support (the page `donate`) showed Puffer's text: the page itself was lost. Written anew
      in v3.0.38; the Sentinel's line for it is made true by the build.

## 9. Lost, not on the stick

docs (ASMO_SPEC, GUIDELINES, MAINFRAME, SECURITY_REVIEW, V2_ASSESSMENT), lab/photon, lab/pse,
lab/py3d, Editor, the old tests' harness (test/harness.c), tools/asmo_gen.py, tools/make_font.py,
tools/relay/ninux_relay.py (Ask needs it). vDNA is safe in its own repository; the ancestors of
py2asm (up to v3.21) are in the repository PypyOS.
