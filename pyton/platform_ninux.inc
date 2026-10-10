; platform_ninux.inc - a PyTon program as an ASMO v4 object of NinuxOS (v2.9.60).
; NOT COMPLETE: read "what is known" below before relying on it.
;
; How the system calls a socket (read from the objects of v2.9.59, e.g. greet, keys, puffer):
;       rdi = the object itself        rsi = the table of the system's functions (8 bytes each)
;       rdx, rcx = the two values of the socket (draw: x, y; open: screen width, height)
;       the result comes back in rax; rbx, rbp, r12-r15 must be kept
;
; The table of functions - what is KNOWN from the old programs' runtime (offset: what, how called):
;       +0x00  write a zero-ended text to the screen       rdi = text
;       +0x08  write one letter                            edi = letter
;       +0x30  text(x, y, text, colour, background)        rdi, rsi, rdx, rcx, r8 (-1 = no background)
;       +0x40  a key, if one waits                         rax = 1 and the letter in dl
;       +0x70  the META value of an object                 rdi = object, rsi = key
;       +0xB0  memory                                      rdi = bytes -> rax   (ASSUMED from one call)
;       +0xC0  write a zero-ended text to the serial log   rdi = text
;       +0xE0  save an object                              rdi = name, rsi = address, rdx = size
;   used by the old runtime, meaning NOT known yet: +0x10 +0x20 +0x38 +0x58 +0x60 +0x68 +0x80 +0xA0
;       +0xA8 +0x118 +0x128 +0x138 +0x150.  Among them are fill, fill_round, window, poll, the mouse,
;       load_text / save_text, ticks, the sound, system() - they must be found before a program
;       with a window can be compiled (TODO.md). Until then only print() and input() work here.
;
; Also open: the identity in the header (0x4C) is left 0, and there is no way yet to put a new
; object into the cabinet from outside (TODO.md, part 1).

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
        mov rax, [rel ninux_api]
        jmp [rax + 0xB0]

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

        align 8
ninux_object:   dq 0
ninux_api:      dq 0
ninux_rsp:      dq 0
ninux_started:  db 0
        align 8
%endmacro
