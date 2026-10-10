# NinuxOS - what is left to do

State on 10 October 2026, v2.9.60. Order = importance.

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
- [ ] The version in the kernel (v2.9.59 -> the real one) once the two checks above are solved.

## 2. The kernel source

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

## 3. Tools

- [ ] `tools/build_disk.py`: objects of another size and new objects; build the image from nothing
      (no base image); the nasm pin of the old build (`tools/nasm.sha256`).
- [ ] `Puffus.exe`: a fresh machine identity for every stick (now every stick written from Windows
      is the same machine: ID, generation, parent).
- [ ] The boot sector says "FAT12 diskette", so Windows mounts a NinuxOS stick and writes
      `System Volume Information` over sectors 19, 44, 45 of the kernel. Either a header Windows
      does not take for a file system, or keep those sectors free.
- [ ] PyTon outside the system: `py2asm.py` is lost; its ancestor `py2asmx64v3.21.py` is in the
      repository PypyOS. Inside the system the compiler works (`build`, Studio F5).
- [ ] The way a new program gets in: `files get NAME` from a FAT32 stick, then `build` - not tried
      yet with a real stick or with a USB stick in QEMU.

## 4. Known faults of v2.9.59 (not now)

- [ ] Bags: a page fault when it is closed with Esc (the shield catches it, the desktop goes on).
      It does not work as wanted anyway - to be redone.
- [ ] Support (the page `donate`) shows Puffer's text instead of the page with the QR code;
      probably the one object the Sentinel calls CHANGED.

## 5. Lost, not on the stick

docs (ASMO_SPEC, GUIDELINES, MAINFRAME, SECURITY_REVIEW, V2_ASSESSMENT), lab/photon, lab/pse,
lab/py3d, Editor, the old tests' harness (test/harness.c), tools/asmo_gen.py, tools/make_font.py,
tools/relay/ninux_relay.py (Ask needs it). vDNA is safe in its own repository.
