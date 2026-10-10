# How the work on NinuxOS goes

The standing instructions of the owner (luskos) for Claude. Read this first in every session;
it stands until the owner changes it. Set on 10 October 2026.

## Who does what

- **Claude writes the code. The owner builds and tests it.** Claude does not run the system in
  QEMU, does not run test suites, does not build to "see if it works". Testing costs tokens and
  is the owner's part.
- If something is serious enough that it truly has to be checked before it is handed over,
  Claude **asks first**, says what would be run and why, and waits. An exception given once
  holds for that one piece of work.
- Reading is not testing: Claude may read sources, disassemble objects, search the image, and
  check that a file it wrote is valid syntax.
- When the owner reports an error, Claude fixes the code; it does not start testing on its own.

## What the system is (so that nothing is built against it)

- Programming with objects, **not** object-oriented programming: no `class` in PyTon, ever.
  A program is an ASMO object: Header + DATA + META + system sockets + named sockets (+ prockets).
- `.asmo` are objects of the system and of the user, `.kasm` are parts of the kernel.
- PyTon is the whole back end. Interfaces are HTML + CSS; where a web page would use JavaScript,
  NinuxOS uses PyTon. Everything written in PyTon goes through `pyton/py2asm.py` to assembly and
  becomes ASMO objects. No other language is added.
- No file system: the cabinet, drawers, objects.

## After every piece of work

1. `TODO.md` - what was done comes off, what was found goes on.
2. `CHANGELOG.md` - one entry for the version.
3. `docs/NinuxOS_Architecture.tex` - whatever became known or changed: formats, the start, the
   kernel, the shell and its commands, PyTon, the tools. It is the one full description.
4. `docs/chat/` - a copy of the conversation.
5. `VERSION`, a commit, a tag, a push to https://github.com/luskos/NinuxOS (private).

## Versions

`v3.x.xx`. A small update raises `xx` (v3.0.01, v3.0.02 ...); a big one raises `x` and starts
`xx` again (v3.1.00). The number the kernel itself says changes only when the kernel can be
rebuilt (TODO.md, part 1).

## Where the work is

`NinuxOS_v3` is the project. `NinuxOS_v2.9.59` beside it is the state before v3 and is left
alone; the folders above them (apps, boot, kernel ... recovered from the lost partition) hold
foreign data under the old names and are never read for facts.

## Answers

In Bulgarian, short, the result first. Say plainly what was not run and what is not known.
