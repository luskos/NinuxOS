; platform_win64.inc - a PyTon program as a Windows console program: to try the language on the
; PC, next to real Python, without NinuxOS. Only NASM is needed - the .exe is written whole:
;   python pyton/py2asm.py prog.py
;   nasm -f bin -I pyton/ prog.asm -o prog.exe
; Only print() and input() reach the outside here; fill(), window() and the rest are NinuxOS.

%define RT_DATA section .data
%define RT_TEXT section .text

; the file: the headers, then the code (read, run), then the data (read, write) - each from a new page
section .hdr start=0
section .text follows=.hdr align=0x1000
section .data follows=.text align=0x1000
section .hdr

PE_BASE equ 0x140000000
PE_PAGE equ 0x1000

pe_start:
        db 'MZ'
        times 0x3C - 2 db 0
        dd pe_header
pe_header:
        db 'PE', 0, 0
        dw 0x8664                       ; x86-64
        dw 2                            ; two sections: code, data
        dd 0, 0, 0
        dw pe_optional_end - pe_optional
        dw 0x0023                       ; runs at its own address, executable, 64-bit addresses
pe_optional:
        dw 0x20B                        ; PE32+
        db 0, 0
        dd pe_text_end - pe_text, pe_end - pe_data, 0
        dd pe_entry
        dd pe_text
        dq PE_BASE
        dd PE_PAGE                      ; in memory as in the file: one page steps
        dd PE_PAGE
        dw 6, 0
        dw 0, 0
        dw 6, 0
        dd 0
        dd pe_end            ; the size in memory
        dd PE_PAGE                      ; the size of these headers
        dd 0
        dw 3                            ; a console program
        dw 0x0100                       ; data is not run
        dq 0x800000, 0x10000            ; stack: 8 MB
        dq 0x100000, 0x1000
        dd 0
        dd 16
        dq 0                            ; exports: none
        dd pe_imports, pe_imports_end - pe_imports
        times 14 dq 0
pe_optional_end:
        db '.text', 0, 0, 0
        dd pe_text_end - pe_text
        dd pe_text
        dd pe_text_end - pe_text
        dd pe_text
        dd 0, 0
        dw 0, 0
        dd 0x60000020                   ; code: read, run
        db '.data', 0, 0, 0
        dd pe_end - pe_data
        dd pe_data
        dd pe_end - pe_data
        dd pe_data
        dd 0, 0
        dw 0, 0
        dd 0xC0000040                   ; data: read, write
        align PE_PAGE, db 0

section .data
pe_data:
pe_imports:                             ; what is asked from KERNEL32.dll
        dd pe_lookup, 0, 0, pe_kernel32, pe_address
        times 5 dd 0
pe_imports_end:
pe_kernel32:    db 'KERNEL32.dll', 0
        align 8, db 0
pe_lookup:
        dq pe_n_GetStdHandle, pe_n_WriteFile, pe_n_ReadFile
        dq pe_n_VirtualAlloc, pe_n_ExitProcess, 0
pe_address:
GetStdHandle:   dq pe_n_GetStdHandle
WriteFile:      dq pe_n_WriteFile
ReadFile:       dq pe_n_ReadFile
VirtualAlloc:   dq pe_n_VirtualAlloc
ExitProcess:    dq pe_n_ExitProcess
        dq 0
pe_n_GetStdHandle: db 0, 0, 'GetStdHandle', 0
        align 2, db 0
pe_n_WriteFile: db 0, 0, 'WriteFile', 0
        align 2, db 0
pe_n_ReadFile:  db 0, 0, 'ReadFile', 0
        align 2, db 0
pe_n_VirtualAlloc: db 0, 0, 'VirtualAlloc', 0
        align 2, db 0
pe_n_ExitProcess: db 0, 0, 'ExitProcess', 0
        align 16, db 0

%macro PE_END 0                         ; the last line of the program
section .text
        align PE_PAGE, db 0xCC
pe_text_end:
section .data
        align PE_PAGE, db 0
pe_end:
%endmacro

section .text
pe_text:
pe_entry:
        sub rsp, 40
        call rt_start
        xor ecx, ecx
        call [rel ExitProcess]

plat_alloc:                             ; rdi = bytes -> rax (0: none)
        push rbp
        mov rbp, rsp
        and rsp, -16
        sub rsp, 32
        xor ecx, ecx
        mov rdx, rdi
        mov r8d, 0x3000                 ; reserve and commit
        mov r9d, 4                      ; read and write
        call [rel VirtualAlloc]
        mov rsp, rbp
        pop rbp
        ret

plat_write:                             ; rdi = address, rsi = length
        push rbp
        mov rbp, rsp
        push rbx
        push r12
        and rsp, -16
        sub rsp, 48
        mov rbx, rdi
        mov r12, rsi
        mov ecx, -11                    ; the standard output
        call [rel GetStdHandle]
        mov rcx, rax
        mov rdx, rbx
        mov r8, r12
        lea r9, [rsp + 40]
        mov qword [rsp + 32], 0
        call [rel WriteFile]
        lea rsp, [rbp - 16]
        pop r12
        pop rbx
        pop rbp
        ret

plat_read:                              ; rdi = address, rsi = room -> rax = how many bytes came
        push rbp
        mov rbp, rsp
        push rbx
        push r12
        and rsp, -16
        sub rsp, 48
        mov rbx, rdi
        mov r12, rsi
        mov ecx, -10                    ; the standard input
        call [rel GetStdHandle]
        mov rcx, rax
        mov rdx, rbx
        mov r8, r12
        lea r9, [rsp + 40]
        mov qword [rsp + 40], 0
        mov qword [rsp + 32], 0
        call [rel ReadFile]
        mov eax, [rsp + 40]
        lea rsp, [rbp - 16]
        pop r12
        pop rbx
        pop rbp
        ret

plat_exit:                              ; rdi = the code
        mov rcx, rdi
        and rsp, -16
        sub rsp, 32
        call [rel ExitProcess]

plat_abort:                             ; after "PyTon: ..." was said
        mov ecx, 1
        and rsp, -16
        sub rsp, 32
        call [rel ExitProcess]
