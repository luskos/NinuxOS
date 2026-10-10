# NinuxOS - what each version brought

Newest first. v2.9.60 and later are written by hand; everything from v2.9.50 down is the text the v2.9.59
kernel carries in itself.

- **v3.0.37** (11 October 2026) - the image is the same but for the version
  - **Where Photon, Puffer, Tuner and META really are** - read from the desk down to the code:
    Puffer, Tuner and META are not in the kernel but in the kernel suit `k_tools` (an object of
    the cabinet with 21 entries); Photon is in the kernel's extension. `tools/kdis/own.py`
    measures what belongs to one entry only. TODO.md has the account and the order in which
    they can become objects of their own. Nothing was cut yet.
  - TODO.md: a screen saver as in The Matrix, the falling threads being the real processes.
  - Three more names in the kernel: `suit_load`, `photon_run`, `desk_asks`.
- **v3.0.36** (11 October 2026) - seen in QEMU
  - **Socials is a program**: it knows your handle (NAME@MACHINE), writes a message as a
    **parcel** - an object whose META is the envelope of docs/PROTOCOLS.md - and lists the
    parcels from you and for you. The first code of the protocols.
  - py2asm: `save_object(name, data, meta)`, `data_len`, `data_code`.
  - TODO.md: Zipper (everything kept packed, unpacked when asked for) - it can be done, the
    objects of the cabinet pack to 31%; the plan is there.
- **v3.0.35** (11 October 2026) - seen in QEMU
  - **A damaged table of the cabinet no longer stops the system**: the loader reads the copy.
    An image with the table's sector wiped starts with all its objects (it started with none).
    And every writer of the table now keeps the copy, not only `cabinet_save`.
    The start says "NinuxOS v3.0.35 ...." and "Video." - two texts of the loader were made
    shorter to make room for this in the part of the kernel that cannot grow.
  - **A program the Sentinel does not know is not handed everything**: power, the services of
    the extension, closing and typing into other programs are refused to it.
  - **Names**: 45 more in the kernel (91 now) - the disk, the console, the screen, the loader.
    What was written after the recovery lies in a file of its own, `kernel/New.kasm`.
- **v3.0.34** (11 October 2026) - seen in QEMU
  - **Letters of other sizes**: `text_big(x, y, text, colour, times)` draws the system's letters
    2, 3, 4 ... times as big (py2asm; no kernel change). The clock of Desk2's curtain and the
    title of Socials use it.
  - TODO.md, part 4f, from the owner: two laptops joined by a USB-C cable with a protocol that
    takes turns ("check-mate") and what the hardware allows; NET Express (making content for
    NET from templates: blog, vlog, shop); Fast Reels.
- **v3.0.33** (11 October 2026) - tried on Windows
  - **The other dialects: c2asm, c++2asm, c#2asm, java2asm, js2asm.** One reader for the five
    (`pyton/clike.py`) turns the text into PyTon and py2asm compiles it - one back end, the
    same assembly. Plain code only: no classes, structs, interfaces, inheritance.
    `pyton/test_dialects.py`: one program written six ways prints the same six times.
- **v3.0.32** (11 October 2026) - seen in QEMU
  - **The screen split in 4 or 9**: the desk and every program that runs, each in its part of
    the screen, made small, all live at once. A click on one makes the screen whole again with
    that one in front; ESC brings the screen back as it was. In the multiplexer of the kernel;
    "All at once: 4 / 9" in the menus of Desk2; `split(n)` in PyTon.
- **v3.0.31** (11 October 2026) - seen in QEMU
  - **Desk2 has the system's own menu on an object**: clone, rename, hide, inject, lock, park,
    drop, clean, erase, share, transfer, broadcast, subscribe - the same page the old desktop
    shows, through NET. With it Desk2 does all the old desktop does, save three small things.
  - py2asm: `ob_call_on` (call a socket with an object itself), `ob_text` (a socket's text).
- **v3.0.30** (11 October 2026) - seen in QEMU
  - **Desk2: what the old desktop could not do.** A bag opens as a panel *over the desk*, with
    the things' own pictures - a click starts one. A click on the top edge of the screen
    brings the **curtain** down (settings, files, shell, power, what the machine is). **More
    desktops**: `< 1/2 >` and PgUp / PgDn; an icon let go at the edge of the screen moves to
    the desktop on that side.
- **v3.0.29** (11 October 2026) - seen in QEMU
  - **Desk2 does what a desktop is expected to do**: the card of an object when the mouse rests
    on its icon; the right button's menu (Open, View, Edit, **Data dump**, About it - and on the
    desk itself Settings, Files, Tidy the icons, The shell); the start menu (N) with Restart and
    Shut down; icons can be moved and stay where they are put. 470 lines of PyTon.
- **v3.0.28** (11 October 2026) - seen in QEMU
  - **Desk2: the desktop written anew, in PyTon** (`apps/Desk2.asmo`, 230 lines - the source is
    there to be read and changed). `desk desk2` in the shell runs it; `desktop` still runs the
    old one. It has the wallpaper, the icons, drawers, programs in windows, pages, a taskbar
    with the running programs and the clock. Not yet: the start menu, the card, the context
    menu, dragging.
  - The kernel: `desk NAME` runs any object as the desktop (under the multiplexer).
  - py2asm: `cabinet_top`, `drawer_first`, `drawer_count`, `ob_flags`, `ob_state`, `open_with`,
    `task_name`, `task_focus`, `tasks_changes`, `task_focused`.
- **v3.0.27** (11 October 2026) - seen in QEMU
  - **py2asm: pictures and more of what the desktop stands on** - `image`, `image_fit`, `clip`,
    `clip_off`, `rect_save`, `rect_restore`, `cabinet_changes`, `power`, `ob_call` - each read
    whole in the kernel first.
  - **Bags shows the things' own pictures**: 48 x 48 in the panel, made small on its icon (nine
    of them, as on a phone). A thing without a picture of its own keeps the coloured tile.
  - `tools/kdis/show.py`: read one function compactly, or how a system function is called.
- **v3.0.26** (11 October 2026) - the image is the same but for the version
  - **The desktop read through** (the first step of writing it anew): it is 47 functions, 2510
    instructions - the 1.3 MB are the wallpaper. 36 of its functions have names now
    (`desk_run`, `desk_draw`, `object_open`, `card_draw`, `context_menu`, `taskbar_page`,
    `action_do` ...). `docs/DESKTOP.md`: its parts, the system functions it stands on, and the
    order in which it is to be written in PyTon.
  - `tools/kdis/outline.py`: a line a function for any recovered source. `rename.py` now also
    works on one object with its own list. Five more functions of the kernel named.
- **v3.0.25** (11 October 2026) - seen in QEMU
  - **The silent backup.** Every object a program saves is at once written a second time into
    a backup pool of 32 MB outside the cabinet - nothing asked, nothing said, no maintenance
    mode. `backup` lists what is kept, `backup get N` brings a save back into the cabinet,
    `backup clear` empties the pool. A disk under 64 MB has no pool; saving works as before.
- **v3.0.24** (11 October 2026) - seen in QEMU
  - **The table of the cabinet is written twice.** A copy lies right behind it and is written
    first; a cut of the power during a writing leaves one of the two whole.
    `tools/table_copy.py check|restore` looks at both and puts the copy back.
  - **A click in the bottom right corner of the screen brings the keyboard** in the shell: a
    machine without keys can call it.
  - `tools/qemu/qrun.py --write`: what the system writes reaches the image (for a copy).
- **v3.0.23** (11 October 2026) - seen in QEMU
  - **`keyboard`: a keyboard on the screen of the shell.** Five rows of keys on the bottom of
    the screen, typed with the mouse (or a finger, where the screen is a mouse to the system);
    the text keeps to the lines above; Shift holds for one key; `keyboard` again takes it away.
    In the kernel: a mouse event of api_poll passes `kb_mouse`, which turns a click on a key
    into that key - so everything that reads keys in the shell takes it.
- **v3.0.22** (11 October 2026) - the image is the same but for the version
  - **The first real names in the kernel**: 41 functions and variables of the multiplexer
    (`mux_run`, `mux_task`, `mux_turn`, `mux_free_task`, `mux_focus` ...), the shell
    (`shell_command`, `shell_commands`), objects and memory (`ob_find`, `ob_call`, `mem_free`,
    `cabinet_save`, `maint_check`), the keys (`key_next`, `key_alt` ...), each with a line
    that says what it does. `tools/kdis/rename.py` applies `tools/kdis/renames.txt` to the
    kernel, its symbols and the suits and checks that no byte changed.
- **v3.0.21** (11 October 2026) - seen in QEMU (4 cores)
  - **`cores solo`, `cores one`, `cores all` work outside maintenance mode**, for the session;
    only keeping the setting on the disk needs `maint`. They used to be refused, so `bench`
    gave the same numbers whatever was typed - that was the whole of "bench always the same".
    With 4 cores: shared work 130 ms, one core 420 ms; after `cores solo` 410 ms.
  - The room for new kernel code is about 24 KB, not 4.6: 0x78000 was only the crash screen's
    idea of where kernel code ends (now 0x80000). The build stops if the extension would reach
    the suits.
- **v3.0.20** (11 October 2026) - tried on Windows; the programs once in QEMU
  - **PyTon programs give memory back.** The runtime looks for the blocks nothing points at any
    more and uses them again (`rt_collect` in `pyton/runtime.inc`): a program that makes and
    drops 160 MB now asks the system for a few. `memory()` says how much was asked.
    `pyton/test.py --stress` checks it the hard way; `examples/garbage.py` is the new test.
  - Files: a line of the description came out as ", written in pyton".
- **v3.0.19** (11 October 2026) - seen in QEMU
  - **`tasks`** in the shell: the programs kept while the shell has the screen, a line each;
    **`tasks close N`** closes one (its memory comes back). The first command written since the
    recovery: the shell asks new code in the extension about a word its own table does not have.
- **v3.0.18** (11 October 2026) - the image is the same but for the version
  - **The extension of the kernel can be moved.** The compiled kernel was read again with the
    22 pointers and 77 code starts found since (the graphics drawing, a driver, the interrupt
    stubs had stayed rows of bytes): 58.8% of it is code now, was 55.6%. The source gives the
    same bytes. With one `nop` put at the start of the extension the system starts and runs
    the shell, the desktop and programs (QEMU, one run) - before, it drew garbage.
    New kernel code is no longer tied to the end of the extension. The core still is fixed.
  - `tools/kdis/kdis.py` takes `pointers.txt` and `names.txt`; `tools/kdis/handwork.py` carries
    the code written by hand (Alt + *, programs live on) into a freshly read source and checks
    the bytes; `seeds.txt`, `pointers.txt`, `names.txt` hold what was learned.
- **v3.0.17** (11 October 2026) - the image is the same but for the version
  - Tried in QEMU whether the kernel can be moved (one `nop`): not yet. Found and named on the
    way, the kernel staying the same bytes: 23 instructions that used addresses of the kernel
    as numbers, the multiplexer's table of 18 functions and 4 more pointers that lay as plain
    bytes. What is left is code never read as code. TODO.md has the whole account.
  - `tools/kdis/numbers.py` (numbers that are addresses), `tools/kdis/pointers.py` (pointers in
    rows of bytes get names).
  - The rule until then: new kernel code at the end of the extension only.
- **v3.0.16** (11 October 2026) - seen in QEMU
  - **Programs live on.** Leaving the desktop no longer closes the programs that run: they are
    kept as they are and the next `desktop` shows them again where they were, the keys going
    to the window that was on top. With nothing open the desktop ends as before. In the kernel:
    three places of the multiplexer call new code at the end of the extension (`mux_leave`,
    `mux_begin`, `mux_order`), each call exactly as long as what it stands for;
    `--plain-kernel` builds without it.
- **v3.0.15** (11 October 2026) - **the first version since v2.9.59 seen running** (QEMU)
  - Tried in QEMU with the owner's leave: the system starts with the new boot sector, the
    changed kernel and our key; the Sentinel takes all 103 lines but donate; pyhello, Alt + *,
    Bags (no page fault any more), Files with data dump, Socials work. TODO.md has the list.
  - Settings: the page is on the desk now (the taskbar opens only what is there; an object
    whose header has the lowest bit at 0x50 set is hidden from the desk), so the button works.
  - Bags: a shorter first line of help (it ran over the panel).
  - test/qemu/q_v3_quick.txt, q_v3_apps.txt, q_v3_settings.txt.
- **v3.0.14** (11 October 2026) - nothing in the image changed but the version
  - The build makes `kernel/Kernel.sym.inc` anew from the kernel it has just assembled: the
    suits follow when code is added anywhere in the kernel, not only at the end of the extension.
  - `tools/kdis/says.py`: comment lines above the functions of the kernel and the suits with the
    texts each points at (`; says: '...'`). The same bytes come out.
  - TODO.md: how the multiplexer runs programs, read from the kernel, and the three changes
    "programs live on" needs.
- **v3.0.13** (11 October 2026) - not run in the system
  - **py2asm: the last functions the programs of v2.9.59 call** - load_image, save_image
    (Paint, Nest), sound_play (PyNamp), net_ask, net_state, net_answer (Ask) - written after
    the runtime found in those four programs. All 20 programs of `apps/` now compile and
    assemble with the new py2asm (they were 16).
  - `python tools/build_disk.py --compare`: a drawer `compare` with those programs compiled by
    the new py2asm as `pyNAME`, to be tried beside the old ones. The old ones are not touched.
  - Read on the way: a picture object is width, height, then 4 bytes a dot; a sound object may
    be a WAV (its part `data` is played, at most 0xBB800 bytes a call).
- **v3.0.12** (11 October 2026) - not run in the system
  - **The project inside the system.** Every build makes a drawer `project` in the cabinet:
    the texts `changelog`, `todo`, `directive`, `protocols`, `tests` (read with `view`), and
    the sources of Files and Socials as source objects (Bags' source was there already). The
    last build carries the last state even if git is out of reach. `--source-inside` also puts
    the whole source with the conversations in as the object `nxsource` (19 MB; to be tried
    once before it is the rule); `--nothing-inside` builds without the drawer.
  - TODO.md, part 2a: the other dialects - c2asm, c++2asm, c#2asm, java2asm, js2asm - over the
    one back end of py2asm; plain code only, no classes, no OOP. An idea for now.
- **v3.0.11** (10 October 2026) - written to the owner's order; none of it has run in the system
  - **The boot sector** no longer looks like a FAT12 diskette: it says "no FAT" and carries a
    partition table with one partition of a kind no other system opens (0x7F). Windows should
    no longer write over the kernel. `--old-boot` builds with the old sector.
  - **The kernel: Alt + \*** (the star of the number keys, or Alt + Shift + 8) turns the display
    off and on, in the shell, on the desktop, in every program - the first code written into the
    kernel since the recovery (112 bytes at the end of the extension, nothing else moved).
    By the VGA registers of the display adapter. `--plain-kernel` builds without it.
  - **At most five people** (`user add`): was six. In k_tools.
  - **Bags, written anew**: a folder on the desktop as on a phone. The icon shows the first nine
    things inside; a click opens a panel without a frame; a click starts a thing, the right
    button takes it out; three pages; L makes it a vault that asks for a password. A clone with
    another name is another folder. The old Bags (and its page fault on Esc) is gone.
  - **Files**: the file manager - every object with its type and size, and what it says about
    itself; Enter opens; **D = data dump**: the DATA of an object out as an object of its own.
  - **Settings**: the page `curtain` (Screen, Sound, Network, People, Machine, Power), opened by
    "Settings" on the taskbar. **Socials**: the empty program.
  - **py2asm**: ob_size, ob_data, data_dump, own_len, own_code, text_meta. The build compiles
    the programs of `apps/py2asm.txt` itself.
  - **The build** (`tools/build_disk.py`): the sources are what counts now - a changed page,
    script or program text, a changed `objects/*.asmo.kasm`, a suit of another size are put in;
    an object that grew is moved behind the last one; a new file in `pages/` becomes a page;
    everything the build adds gets a line in the Sentinel's list (98 -> 103); an object put in
    the place of another keeps its identity.
  - **tools/make_font.py**: a .ttf -> the object `font`. **docs/PROTOCOLS.md**: the first
    writing of the protocols (messages, pictures, video, files between handles).
  - Found on the way: the system's table +0x80 calls a named socket of another object; the
    desktop draws the image named by `icon` in META, and asks the socket `draw` only if there is
    none; the kernel takes 0x50000-0x78000 for its extension.
- **v3.0.10** (10 October 2026)
  - TODO.md begins with "The order of work": 35 things in six steps - the gate (the owner's
    tests), what needs no kernel, the kernel, the desktop, machines, what NinuxOS is for - each
    with its size. Part 4e: Bags as folders, more desktops (slide or film strip), settings as a
    curtain, vDNA as the form for closed code with a universal constructor.
- **v3.0.09** (10 October 2026)
  - TODO.md, part 4d, and DIRECTIVE.md: the owner's design, where NinuxOS is not like the other
    systems - no installing (a program is a whole object), no permissions (relays instead), open
    by presumption (vDNA for the closed case), no web and no browser (NET of NinuxOS machines,
    protocols), the chain of machines that carries NET and META. To build: `data dump`, the silent
    backup and its pool, touchpads and touch, languages, the battery, settings, a file manager,
    the split desktop (multiboxing).
- **v3.0.08** (10 October 2026)
  - TODO.md, part 4c: NinuxOS measured against macOS, Windows, Linux and Android, area by area -
    what it has, what is missing, what must be there before anyone else can use it; the order
    that follows from it; Claude's notes on the owner's ideas (the governor, the wall between the
    desktop and the shell, 5 users).
- **v3.0.07** (10 October 2026)
  - `assets/fonts`: the three font families v2.9.59 was made with (Exo for the shell, JetBrains
    Mono, Russo One), from the owner.
  - TODO.md, part 4a: what an operating system needs and NinuxOS does not have yet - twelve
    points, the worst first. Part 4b: the owner's notes of today - kill and the desktop that
    closes everything, cores solo and bench, at most 5 users, an instance of the system on every
    disk with a governor, the wall between the desktop and the shell.
- **v3.0.06** (10 October 2026)
  - `docs/TESTS.md`: the full list of system tests for the owner, in the order they depend on each
    other, with what must be seen and what it means if it is not: the build, Puffus and the stick,
    the start, the seals, the cabinet, the programs of the new py2asm, everything old, the source
    container, and the proof that code can be added to the kernel.
- **v3.0.05** (10 October 2026) - a source for everything that is compiled
  - The kernel: the tables of addresses in its data found and followed (the shell's commands, the
    functions for programs, 369 addresses in all) - 55.6% of the kernel is code, the rest is
    texts, zeros and tables; no instruction is left as bytes; the variables in memory, the
    loader's addresses and the size of the extension are names. `cmd_*` and `api_*` are real
    names. Written so that lines can be added; not proven by running a changed kernel.
  - The four kernel suits as source (`kernel/suits/*.kasm`); the build assembles them and signs
    them. Their format: 64 bytes of signature, the slot, the size, the code.
  - Corrected: v3.0.04 changed the key but left the suits signed with the old one - the system
    would have refused k_tools. The build signs the suits now.
  - The build finds the places it fills in (the key, the hash) by what the source holds there,
    not by a fixed address.
  - Still the same bytes as v2.9.59 everywhere except the version, the key and the signatures.
- **v3.0.04** (10 October 2026) - the build can change the system
  - Read from the image and written into `tools/build_disk.py`: the SHA-256 the core keeps of the
    extension; the Sentinel's list (98 lines of name + SHA-256, signed with Ed25519) and the place
    of its public key in the kernel; the table of the cabinet at sector 481 and the drawers.
    The build now writes the version into the whole kernel, adds the objects of `build/add/` to
    the cabinet, seals the extension, writes the Sentinel's list anew and signs it with a key of
    its own (`build/key/build.key`, made at the first build, not in git).
  - `disk.img` v3.0.04 has two programs made by the new py2asm in its cabinet: pyhello, pycalc.
  - `tools/kdis/odis.py`: all 34 compiled objects as NASM source in `objects/` - Desktop, Studio,
    NET, the twenty programs - each assembling to the same bytes, with names for the header, the
    sockets and every relocation.
  - kdis corrected (`retq` ends a function); `kernel/Kernel.kasm` made anew: 41% recognised code.
  - The system has 107 objects, not 165: 58 in the image are old copies.
  - Nothing of this ran on a machine: the owner tests (TODO.md, part 1).
- **v3.0.03** (10 October 2026)
  - The system shows the version of the project: the build writes `VERSION` over `v2.9.59` in the
    texts of the kernel's core (the line of the loader, the top of the shell, `info`, the log) -
    four places, the same length, nothing moves. The extension is left as it is (its SHA-256 check),
    so `machine` and Setup still say v2.9.59. `--keep-version` builds without it. Not tried:
    the Sentinel will probably list @kernel as CHANGED.
  - `Puffus.exe` in the folder is still the one of v2.9.60 (it was open and could not be replaced):
    close it and run `tools\puffus\make_puffus.cmd`. It builds before it writes, so the stick gets
    the new number either way; only the source container on the stick needs the new Puffus.
  - DIRECTIVE.md: VERSION goes up with every update. TODO.md: Socials, the social network of the system.
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
