; platform_win64.inc - a PyTon program as a Windows console program: to try the language on the
; PC, next to real Python, without NinuxOS. Linked with gcc (MSYS2 MINGW64):
;   python pyton/py2asm.py prog.py
;   nasm -f win64 -I pyton/ prog.asm -o prog.obj
;   gcc prog.obj -o prog.exe
; Only print() and input() reach the outside here; fill(), window() and the rest are NinuxOS.

%define RT_DATA section .data
%define RT_TEXT section .text

extern malloc
extern _write
extern _read
extern exit
global main

%macro WIN_CALL 1                       ; a C function: stack on 16, 32 bytes of room, as Windows wants
        push rbp
        mov rbp, rsp
        and rsp, -16
        sub rsp, 32
        call %1
        mov rsp, rbp
        pop rbp
%endmacro

section .text

main:
        sub rsp, 40
        call rt_start
        xor ecx, ecx
        call exit

plat_alloc:                             ; rdi = bytes -> rax (0: none)
        mov rcx, rdi
        WIN_CALL malloc
        ret

plat_write:                             ; rdi = address, rsi = length
        mov ecx, 1
        mov rdx, rdi
        mov r8, rsi
        WIN_CALL _write
        ret

plat_read:                              ; rdi = address, rsi = room -> rax = how many bytes came
        xor ecx, ecx
        mov rdx, rdi
        mov r8, rsi
        WIN_CALL _read
        movsxd rax, eax
        ret

plat_exit:                              ; rdi = the code
        mov rcx, rdi
        WIN_CALL exit

plat_abort:                             ; after "PyTon: ..." was said
        mov ecx, 1
        WIN_CALL exit
