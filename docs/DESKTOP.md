# The desktop: what it is made of, and how it is to be written anew

Item 22 of the order of work (TODO.md). First step, v3.0.26: the object Desktop read through and
named. Nothing in the image changed.

## What the object is

`objects/Desktop.asmo.kasm`, 1 325 232 bytes - but 1.2 MB of that is its DATA, the wallpaper
(640 x 480 dots, 4 bytes each). The program itself is small: **47 functions, 2510 instructions**,
one socket (`run`), one procket ("lucky start", 30%). It was compiled from PyTon by the
transpiler that was lost; its source was never on the stick.

It is started by the shell's `desktop`: the multiplexer (`mux_run` in the kernel) makes it task 0
and gives it turns like any program. It draws the whole screen itself, by the system's functions.

`python tools/kdis/outline.py objects/Desktop.asmo.kasm` prints a line for every function: its
size, the system functions it calls, its own functions it calls, the texts it uses. The names
below were given from that (`tools/kdis/renames_desktop.txt`); seven functions are not
understood yet and keep their addresses.

## Its parts

| part | functions | what it does |
|---|---|---|
| the loop | `desk_run` (269 instructions) | needs a graphics mode; draws the desk; then keys and the mouse until ESC or the shell button; calls everything else |
| the desk | `desk_draw` (315), `desk_redraw`, `icon_label` | every object of the cabinet that is not hidden gets a place and an icon - the picture its META `icon` names, or what its socket `draw` draws - by its type: icon, script, cabinet (a drawer), page |
| places | `places_object`, `places_find`, `places_set`, `places_save` | where the user put each icon: the object `desk_places` (type:data), by the names of the objects |
| the mouse on icons | `icon_at`, `icon_hover`, `icon_drag` | which icon is under the mouse; moving one |
| the card | `card_draw` (242), `card_off` | the card that comes up over an icon: label, name, kind, a picture or the text of its DATA, its identity; what was under it is put back |
| opening | `object_open` (129), `studio_with` | a program is started (asked of the multiplexer), a drawer opened, a page or text shown, a locked object refused; edit and view go to Studio |
| the context menu | `context_menu` (130), `inject_cancel` | the right button: the page `context` as a popup, then what was chosen there (message, Inject, edit ...) |
| the taskbar | `taskbar_page` , `taskbar_values`, `taskbar_page_click`, `taskbar_page_hit`, `taskbar_object`, `taskbar_is_page` | the taskbar is the page `taskbar`, drawn by the kernel's page drawing with the values tasks=, title=, msg=, hint= and the clock filled in |
| the taskbar without a page | `taskbar_plain`, `tasks_count`, `tasks_buttons`, `tasks_at`, `taskbar_clock`, `taskbar_top`, `taskbar_click` | drawn by the desktop itself if the page is missing: buttons for the programs that run, the clock |
| actions | `action_do` (94) | what a clicked part of a page names: `start`, `system.shell`, `system.shutdown`, `system.restart`, `system.stone`, or the name of an object on the desk ("Not on the desk: ...") |
| the start menu | `start_menu` | the page `start` as a popup |
| messages | `message_set`, `message_time`, `procket_message` | the line of text on the taskbar and when it goes away |
| the first start | `first_start` | no object `settings` yet: the page `setup` is shown |
| not understood yet | `fn_12c668`, `fn_12c72c`, `fn_12c781`, `fn_12d428`, `fn_12e3d0`, `fn_12e508`, `fn_12e5c2` | probably: the wallpaper stretched to the screen (the first three), the cabinet changed - draw again, the menu drawn and taken off |

## The system functions it calls

The table a program is handed (the place in it, the kernel's function, what it does). The first
ten were known from the programs; the rest are read from the first lines of each function in
the kernel and from how the desktop uses them - **to be confirmed** when the function is read
whole.

| place | what |
|---|---|
| +10, +18, +30, +40, +48, +50 | screen_size, fill, text, poll, cursor_show, cursor_hide |
| +60, +68, +70, +80 | object by number, by name; a META value; call a socket of an object (`draw`, `open`) |
| +98 | are two words the same (`shell_same_word`) - the types `icon`, `script`, `cabinet`, `page` are told apart with it |
| +A0, +B0, +B8, +C0, +E0 | ticks, memory, give memory back, log, save an object |
| +20 | draw a picture: x, y, the picture (width, height, dots) |
| +28 | draw a picture into a rectangle of another size (the wallpaper, the icons) |
| +88 | a procket of an object: roll it |
| +C8 | the lines of an object's META, one after another (the card) |
| +D0, +D8 | keep what is on the screen in a rectangle; put it back (menus, the card) - `api_rect_save`, `api_rect_restore` |
| +E8 | power: off, restart (`api_power`) |
| +F0 | a number that grows with every change of the cabinet (`api_cabinet_changes`): the desk is drawn again when it changed |
| +100 | draw only inside a rectangle (`api_clip`) |
| +108 | the services of the kernel's extension: showing a page, the password window ... (one function, a number says which) |
| +110 | facts about the cabinet and an object, by a number (4: an object's rating) |
| +118 | the multiplexer: start a program, list them, close one, send a key (a number says which) |
| +128, +140, +148 | a text of the system (the clock); fill with round corners; the graphics adapter's part |

## How it is to be written anew

In PyTon, compiled by py2asm, with the pages it already uses. In this order, each step a
desktop that can be started and tried beside the old one:

   *v3.0.27:* read whole and connected: `image(x, y, name)`, `image_fit(x, y, w, h, name)`
   (+20, +28: a picture object is width, height, dots; 0xFF00FF is see-through), `clip`,
   `clip_off` (+100), `rect_save`, `rect_restore` (+D0, +D8: restore also frees it, so once),
   `cabinet_changes` (+F0), `power` (+E8), `ob_call(name, socket, a, b)` (+80). Seen working
   in Bags (the things' own pictures). Still to read: the page drawing (+108), the facts
   about the cabinet (+110), the multiplexer's numbers (+118), the META lines (+C8), the
   procket (+88), +148, and +F8 (five values; not the clip).

   *v3.0.28:* also `cabinet_top`, `drawer_first`, `drawer_count` (+110: the objects of a drawer
   are numbered after the cabinet's own), `ob_flags`, `ob_state`, `open_with(program, socket,
   object)`, `task_name`, `task_focus`, `tasks_changes`, `task_focused` (+118, numbers 2-5).
   How the shell starts the desktop was read: only the word `desktop` runs an object under
   the multiplexer - so `desk NAME` was added to the kernel, which runs any object that way.

   **Step 2 is done: `apps/Desk2.asmo`**, 230 lines of PyTon, seen in QEMU (`desk desk2`): the
   wallpaper, an icon for everything on the desk (its picture, or what its socket `draw`
   draws, or a coloured tile), drawers that open with a way back, programs in windows, pages
   in NET, a taskbar with a button a program and the clock, ESC or "shell" to leave.
   Of step 3 it already has opening things and the taskbar's buttons. Not yet: the start menu,
   the taskbar as a page, the card, the context menu, dragging and kept places, the system's
   messages. The old desktop is untouched and is still what `desktop` runs.

   **Steps 3 and 4 are done in v3.0.29** (`apps/Desk2.asmo`, 470 lines; seen in QEMU,
   `test/qemu/q_v3_desk2b.txt`): the mouse resting on an icon brings its card (label, name,
   what it is, its DATA, sockets, size); the right button a menu - on an icon: Open, View in
   Studio, Edit in Studio, Data dump, About it; on the desk: Settings, Files, Tidy the icons,
   The shell; the button N the start menu (Settings, Files, The shell, Restart, Shut down);
   an icon held and moved stays where it is let go (kept in the object `desk2_places`, by
   name). What lies over the desk keeps what was under it (`rect_save`) and puts it back.
   Still not there: the taskbar and the menus as pages; the system's own actions on an
   object (clone, rename, hide, lock, inject, erase, share - they are the extension's
   services, +108, not read yet); the system's messages on the taskbar. In QEMU the right
   button arrives as 4, not 2 - Desk2 takes both.

   **Step 5, a first form, v3.0.30** (seen in QEMU, `test/qemu/q_v3_desk2c.txt`):
   - *a bag over the desk*: an object whose META says `bag:yes` (Bags, and every clone of it)
     opens as a panel over the desk with the things' own pictures; a click starts one, a
     click beside closes it. An empty bag or a vault opens its own program; so does "Open" of
     the right button's menu - that is where things are put in and taken out.
   - *the curtain*: a click on the top edge of the screen brings it down - Settings, Files,
     Shell, Tidy, Restart, Off, and what the machine is. It is clicked, not pulled yet.
   - *more desktops*: up to nine. `< 1/2 >` on the taskbar and PgUp / PgDn change the
     desktop; an icon let go at the left or right edge goes to the desktop on that side (a
     new one if there is none). Kept with the places. No sliding picture, and not the film
     strip that scrolls.
   Not begun: the desktop split in 4 or 9 (it needs the multiplexer to draw a task into a
   part of the screen).

1. **py2asm gets the functions above** that it does not have (pictures, the rectangle kept and
   put back, clip, power, the cabinet's counter, the page drawing, the multiplexer's numbers,
   calling a socket). Each has to be read whole in the kernel first - guessing a function that
   draws on the screen is cheap, guessing one that writes the cabinet is not.
2. **The desk**: wallpaper, icons with labels, places kept in `desk_places`; ESC to leave.
   Needs to be startable beside the old one: how `desktop` finds its object (by the type
   `desktop`?) is to be read in the kernel, so that `desktop NAME` or a second command can
   start the new one.
3. **Opening things**, the taskbar page with its values and clicks, the start menu.
4. **The card, the context menu, dragging.**
5. Then what the old one cannot do and the owner asked for: a panel of a program over the desk
   (Bags), the settings pulled down from the top edge, `data dump` in the context menu, more
   desktops, the split desktop.

What makes this slow is step 1, not the PyTon: the desktop's own logic is about 600 lines of
PyTon; what it stands on has to be known exactly.
