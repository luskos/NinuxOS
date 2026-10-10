# The conversation

`2026-10-11_recovery_to_v3.0.37.zip` is the export of the Claude Code session in which NinuxOS
v2.9.59 was brought back and v3 was started: the whole transcript with every command that was
run and its output. It is the record of how each file of this project was made. It ends shortly
before v3.0.37 was committed. One file holds the whole conversation; a later export replaces it
(the older ones stay in the history of git).

In short, in the order it happened:

1. The project folder turned out to be destroyed: recovered from a lost partition, 237 of 310
   files held foreign data (right names and sizes, wrong contents). Only files under ~700 bytes
   were real. A second copy (Desktop\ppp\Ninux) was the same, byte for byte.
2. A stick made with `puffer GO` was read sector by sector. The first reading was damaged:
   Windows had mounted the stick as FAT12 and written `System Volume Information` over sectors
   19, 44 and 45. With USB write protection on
   (`HKLM\SYSTEM\CurrentControlSet\Control\StorageDevicePolicies`, `WriteProtect` = 1) the second
   reading was clean -> `disk.img`, v2.9.59.
3. The format of an ASMO v4 object was read from the objects themselves, the 165 objects were
   taken out of the cabinet, the PyTon sources and the pages unwrapped.
4. The boot sector was written back by hand (`boot/Boot.kasm`); for the kernel a tool was made
   (`tools/kdis/kdis.py`) that follows the code, writes NASM source and compares the result with
   the original: the same 220000 bytes.
5. The image put together from the recovered parts was run in QEMU: the start, the shell commands,
   the desktop and 30 programs. Found: Bags faults when closed, Support shows Puffer's text,
   the Sentinel reports one changed object.
6. v2.9.60: the build script, Puffus for Windows, the documentation, the backup on GitHub.
7. v3.0.0: py2asm written anew (try / except, lambda, def inside def, *args, sets; no class),
   compared with real Python on Windows; the source container; TODO: winlolz / linlolz, Greek
   file endings.
8. v3.0.01: the folder NinuxOS_v3 and DIRECTIVE.md; the system's functions found in the old
   runtime and connected in py2asm; Calc and ASMONCRAFT compile for NinuxOS.
9. v3.0.02: the rest of the system's functions; 16 of the 20 programs compile.
10. v3.0.03: the build writes the version into the kernel's texts; Socials goes on the list.
11. v3.0.04: the seals of a build read from the image (the extension's SHA-256, the Sentinel's
    list and its key, the table of the cabinet); the build adds objects and signs; every
    compiled object as source.
12. v3.0.05: the kernel's tables found, its source without a byte left unread; the kernel suits
    as source and signed by the build.
13. v3.0.06: the list of system tests (docs/TESTS.md).
14. v3.0.07: the fonts; what the system still lacks as an operating system; the owner's notes.
15. v3.0.08: the system measured against macOS, Windows, Linux and Android.
16. v3.0.09: the owner's design written down (no installing, no permissions, no web; NET, relays, vDNA).
17. v3.0.10: the order of work - 35 things in six steps.
18. v3.0.11: the owner's work order - the boot sector, the build, the font tool, Bags, Files, Settings, Alt + *, five users, the protocols.
19. v3.0.12: the project inside the system (the drawer project); the other dialects as an idea.
20. v3.0.13: py2asm compiles all 20 programs; --compare.
21. v3.0.14: the build follows a changed kernel (Kernel.sym.inc); what the functions say; the multiplexer read.
22. v3.0.15: the quick test in QEMU - it starts and the new things work; Settings on the desk.
23. v3.0.16: programs live on when the desktop is left.
24. v3.0.17: can the kernel be moved - tried, not yet; what was found.
25. v3.0.18: the kernel read again; its extension can be moved.
26. v3.0.19: the command tasks.
27. v3.0.20: PyTon programs give memory back.
28. v3.0.21: cores solo and bench; the room for kernel code.
29. v3.0.22: the first real names in the kernel.
30. v3.0.23: the keyboard on the screen of the shell.
31. v3.0.24: the table of the cabinet twice; the keyboard by a click in the corner.
32. v3.0.25: the silent backup and its pool.
33. v3.0.26: the desktop read through and named (docs/DESKTOP.md).
34. v3.0.27: pictures in py2asm; Bags with the real icons.
35. v3.0.28: Desk2 - the desktop written anew in PyTon; desk NAME.
36. v3.0.29: Desk2 - the card, the menus, the start menu, moving icons.
37. v3.0.30: Desk2 - a bag over the desk, the curtain, more desktops.
38. v3.0.31: Desk2 - the system's own menu on an object.
39. v3.0.32: the screen split in 4 or 9.
40. v3.0.33: the dialects - c2asm, c++2asm, c#2asm, java2asm, js2asm.
41. v3.0.34: letters of other sizes; the USB-C link, NET Express, Fast Reels into TODO.
42. v3.0.35: the loader reads the copy of the table; what a program is handed; 91 names, New.kasm.
43. v3.0.36: Socials and the parcel in code; Zipper into TODO.
44. v3.0.37: where Photon, Puffer, Tuner and META really are; the Matrix screen saver into TODO.

The transcript holds what was on the screen of this PC during the work (paths, the account name,
the identity of the test machine). Keep the repository private.
