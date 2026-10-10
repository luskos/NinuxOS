; platform_ninux.inc - a PyTon program as an ASMO v4 object of NinuxOS (v3).
; Not tried in the system yet (TODO.md). Everything here was read from the programs v2.9.59
; was shipped with: their runtime (the same code in all twenty) shows how the system is called.
;
; How the system calls a socket:
;       rdi = the object itself        rsi = the table of the system's functions (8 bytes each)
;       rdx, rcx = the two values of the socket (draw: x, y; open: screen width, height)
;       the result comes back in rax; rbx, rbp, r12-r15 must be kept
;
; The table of functions (offset: what; the values go in rdi, rsi, rdx, rcx, r8, r9):
;   sure - the old runtime's function for it was matched with the PyTon name by counting the calls
;       +0x00  write a zero-ended text to the screen (the shell)        rdi = text
;       +0x08  write one letter                                         edi = letter
;       +0x18  fill(x, y, w, h, colour)
;       +0x30  text(x, y, text, colour, background)                     r8 = -1: no background
;       +0x38  window(x, y, w, h, title)
;       +0x40  poll(): rax = 0 nothing, 1 a key, 2 the mouse;  rdx, rcx, r8 = what came:
;              a key: rdx = the key;  the mouse: rdx = x, rcx = y, r8 = the buttons
;       +0x50  cursor_hide()
;       +0x70  the META value of an object                              rdi = object, rsi = key -> text or 0
;       +0xC0  write a zero-ended text to the serial log                rdi = text
;       +0x140 fill_round(x, y, w, h, colour, radius)
;   likely - read from the code, not matched by counting
;       +0x10  the clock: rax = ticks (100 a second), rdx = a second value (the time?)
;       +0x48  cursor_show(x, y)
;       +0xB0  memory: rdi = bytes -> rax
;       +0xE0  save an object: rdi = name, rsi = address, rdx = size
;       +0x128 the list of what system() may run
;   used by the old runtime, meaning not known yet: +0x20 +0x58 +0x60 +0x68 +0x80 +0xA0 +0xA8
;       +0x118 +0x138 +0x150.  Among them: load_text, save_text, load_image, save_image, ob_count,
;       ob_meta, spawn, kill, the sound, the network, random, time.
;
; Also open: the identity in the header (0x4C) is left 0, and how a new object gets into the
; cabinet (TODO.md).

%define RT_DATA
%define RT_TEXT

%macro NINUX_SOCKET_ENTER 0
        push rbx
        push rbp
        push r12
        push r13
        push r14
        push r15
        mov [rel ninux_object], rdi
        mov [rel ninux_api], rsi
        mov [rel ninux_rsp], rsp
        mov qword [rel rt_handler], 0
        cmp byte [rel ninux_started], 0
        jne %%ready
        mov byte [rel ninux_started], 1
        push rdx
        push rcx
        call rt_start                   ; the lines at the top of the program run once
        pop rcx
        pop rdx
%%ready:
%endmacro

%macro NINUX_API 1                      ; go to the system's function at this place of the table
        mov rax, [rel ninux_api]
        jmp [rax + %1]
%endmacro

%macro NINUX_PLATFORM_CODE 0
ninux_socket_leave:                     ; rax = what the socket's function gave: a number goes back as it is
        test al, 1
        jz ninux_no_number
        sar rax, 1
        jmp ninux_out
ninux_no_number:
        xor eax, eax
ninux_out:
        pop r15
        pop r14
        pop r13
        pop r12
        pop rbp
        pop rbx
        ret

plat_abort:                             ; an error was said: leave the socket with -1
        mov rsp, [rel ninux_rsp]
        mov rax, -1
        jmp ninux_out

plat_exit:
        mov rsp, [rel ninux_rsp]
        mov rax, rdi
        jmp ninux_out

plat_alloc:                             ; rdi = bytes -> rax
        NINUX_API 0xB0

plat_write:                             ; rdi = address, rsi = length
        push rbx
        push r12
        mov rbx, rdi
        mov r12, rsi
ninux_write_next:
        test r12, r12
        jz ninux_write_done
        movzx edi, byte [rbx]
        mov rax, [rel ninux_api]
        call [rax + 0x08]
        inc rbx
        dec r12
        jmp ninux_write_next
ninux_write_done:
        pop r12
        pop rbx
        ret

plat_read:                              ; rdi = address, rsi = room -> rax = length; a line, shown as typed
        push rbx
        push r12
        push r13
        mov rbx, rdi
        mov r12, rsi
        xor r13d, r13d
ninux_read_key:
        mov rax, [rel ninux_api]
        call [rax + 0x40]
        cmp rax, 1
        jne ninux_read_key
        cmp dl, 13
        je ninux_read_done
        cmp dl, 10
        je ninux_read_done
        cmp r13, r12
        jae ninux_read_key
        mov [rbx + r13], dl
        inc r13
        movzx edi, dl
        mov rax, [rel ninux_api]
        call [rax + 0x08]
        jmp ninux_read_key
ninux_read_done:
        mov edi, 10
        mov rax, [rel ninux_api]
        call [rax + 0x08]
        mov rax, r13
        pop r13
        pop r12
        pop rbx
        ret

; ---- the functions a PyTon program calls by name (py2asm: SYSTEM)
sys_fill:                               ; (x, y, w, h, colour)
        NINUX_API 0x18
sys_fill_round:                         ; (x, y, w, h, colour, radius)
        NINUX_API 0x140
sys_text:                               ; (x, y, text, colour)
        mov r8, -1
        NINUX_API 0x30
sys_window:                             ; (x, y, w, h, title)
        NINUX_API 0x38
sys_cursor_show:                        ; (x, y)
        NINUX_API 0x48
sys_cursor_hide:
        NINUX_API 0x50
sys_ticks:
        NINUX_API 0x10

sys_poll:                               ; -> 0 nothing, 1 a key, 2 the mouse; what came is kept
        mov rax, [rel ninux_api]
        call [rax + 0x40]
        test rax, rax
        jz ninux_poll_nothing
        mov [rel ninux_event + 0], rdx
        mov [rel ninux_event + 8], rcx
        mov [rel ninux_event + 16], r8
ninux_poll_nothing:
        ret
sys_key:                                ; the key of the last poll()
sys_mouse_x:
        mov rax, [rel ninux_event + 0]
        ret
sys_mouse_y:
        mov rax, [rel ninux_event + 8]
        ret
sys_key_mods:                           ; Shift, Ctrl, Alt of the last key
sys_mouse_buttons:
        mov rax, [rel ninux_event + 16]
        ret

sys_log:                                ; (text): a line in the serial log
        mov rax, [rel ninux_api]
        call [rax + 0xC0]
        lea rdi, [rel ninux_newline]
        NINUX_API 0xC0

sys_meta:                               ; (key) -> the value from this object's META, or an empty text
        mov rsi, rdi
        mov rdi, [rel ninux_object]
        mov rax, [rel ninux_api]
        call [rax + 0x70]
        ret

        align 8
ninux_object:   dq 0
ninux_api:      dq 0
ninux_rsp:      dq 0
ninux_event:    dq 0, 0, 0
ninux_started:  db 0
ninux_newline:  db 10, 0
        align 8
%endmacro
