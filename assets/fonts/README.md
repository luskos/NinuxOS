# The fonts of NinuxOS

`Exo,JetBrains_Mono,Russo_One.zip` - the three font families v2.9.59 was made with (from the
owner, 10 October 2026; all three under the SIL Open Font License, the texts are in the zip).

- **Exo** is the shell's font.
- JetBrains Mono and Russo One: where they were used is not known any more.

In the system the letters are one object, `font` (4376 bytes: 256 letters of 8 by 16 dots, Latin
and Cyrillic) - `build/objects/font.asmo` still holds the letters as they were drawn from Exo.
The tool that drew them from a .ttf (`tools/make_font.py`) was lost and has to be written again
before the letters can be changed or Greek ones added (TODO.md).
