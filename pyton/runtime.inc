; runtime.inc - what every PyTon program made by py2asm needs under it (NinuxOS v2.9.60).
; The small, fast part is here in assembly; everything else (texts, lists, dicts, fractions,
; str(), methods ...) is written in PyTon itself, in prelude.py, and compiled with the program.
;
; A VALUE is 64 bits:
;   a whole number n   -> n*2 + 1            (the lowest bit is 1; 63 bits of number)
;   anything else      -> the address of a block (the lowest bit is 0); its first 8 bytes say what it is:
;       1 text    [1][length][the bytes ..., 0]
;       2 list    [2][length][room][address of the items]
;       3 dict    [3][0][the list of keys][the list of values]
;       4 float   [4][the 8 bytes of a double]
;       5 tuple   like a list
;       6 None    rt_none          7 bool   rt_true / rt_false   [7][0 or 1]
;       8 function [8][code][values it takes][values it keeps][values it needs][kept values, default values]
;       9 set     like a list, every value once
;
; Calling:  the functions here take their values in rdi, rsi, rdx, rcx and give the result in rax;
;           they keep rbx, rbp, r12-r15.  A compiled PyTon function (f_NAME) takes its values on the
;           stack, pushed first to last, and the caller takes them off again.
; The platform file gives:  plat_alloc (rdi bytes -> rax), plat_write (rdi address, rsi length),
;           plat_read (rdi address, rsi room -> rax length), plat_exit (rdi code), plat_abort.
; Memory is never given back yet (as before): a block lives until the program is unloaded.

T_INT   equ 0
T_STR   equ 1
T_LIST  equ 2
T_DICT  equ 3
T_FLOAT equ 4
T_TUPLE equ 5
T_NONE  equ 6
T_BOOL  equ 7
T_FUNC  equ 8
T_SET   equ 9

RT_CHUNK equ 0x100000                   ; memory is asked from the system 1 MB at a time

%macro RT_BOOL 0                        ; al = 0 / 1  ->  rax = rt_false / rt_true, and back
        test al, al
        lea rax, [rel rt_true]
        lea rcx, [rel rt_false]
        cmovz rax, rcx
        ret
%endmacro

%macro RT_BOTH_INT 1                    ; go to %1 unless rdi and rsi are both whole numbers
        mov eax, edi
        and eax, esi
        test al, 1
        jz %1
%endmacro

%macro RT_SLOW2 1                       ; the PyTon function %1 (a, b) does the work
        push rdi
        push rsi
        call %1
        add rsp, 16
        ret
%endmacro

; ---------------------------------------------------------------- start, memory, errors

rt_start:                               ; run the lines at the top of the program
        call f___main__
        ret

rt_alloc:                               ; rdi = bytes -> rax = a zeroed block
        add rdi, 15
        and rdi, -16
.again:
        mov rax, [rel rt_heap_ptr]
        test rax, rax
        jz .more
        lea rdx, [rax + rdi]
        cmp rdx, [rel rt_heap_end]
        ja .more
        mov [rel rt_heap_ptr], rdx
        mov rdx, rax
        mov rcx, rdi
        shr rcx, 3
        mov rdi, rax
        xor eax, eax
        rep stosq
        mov rax, rdx
        ret
.more:
        push rdi
        mov rax, RT_CHUNK
        cmp rdi, rax
        cmova rax, rdi
        push rax
        mov rdi, rax
        call plat_alloc
        pop rcx
        pop rdi
        test rax, rax
        jz .none
        mov [rel rt_heap_ptr], rax
        add rax, rcx
        mov [rel rt_heap_end], rax
        jmp .again
.none:
        lea rdi, [rel rt_msg_memory]
        jmp rt_fail

rt_fail:                                ; rdi = a zero-ended text: say it and stop the program
        push rdi
        lea rdi, [rel rt_msg_error]
        mov esi, rt_msg_error_len
        call plat_write
        pop rdi
        xor esi, esi
.len:
        cmp byte [rdi + rsi], 0
        je .say
        inc rsi
        jmp .len
.say:
        call plat_write
        lea rdi, [rel rt_msg_nl]
        mov esi, 1
        call plat_write
        jmp plat_abort

rt_err_type:
        lea rdi, [rel rt_k_type]
        lea rsi, [rel rt_m_type]
        jmp rt_raise
rt_err_index:
        lea rdi, [rel rt_k_index]
        lea rsi, [rel rt_m_index]
        jmp rt_raise
rt_err_index_type:
        lea rdi, [rel rt_k_type]
        lea rsi, [rel rt_m_index_type]
        jmp rt_raise
rt_err_zero:
        lea rdi, [rel rt_k_zero]
        lea rsi, [rel rt_m_zero]
        jmp rt_raise
rt_err_call:
        lea rdi, [rel rt_k_type]
        lea rsi, [rel rt_m_call]
        jmp rt_raise
rt_err_count:
        lea rdi, [rel rt_k_type]
        lea rsi, [rel rt_m_count]
        jmp rt_raise

; ---------------------------------------------------------------- try / except
; A try keeps four values in its function's frame: [0] rsp, [8] rbp, [16] where its except
; starts, [24] the try around it. rt_handler points at the innermost one.

rt_raise:                               ; rdi = the kind (a text: 'ValueError'), rsi = the message (a text)
        mov [rel rt_exc_kind], rdi
        mov [rel rt_exc_msg], rsi
rt_reraise:
        mov rax, [rel rt_handler]
        test rax, rax
        jz .nobody
        mov rcx, [rax + 24]
        mov [rel rt_handler], rcx
        mov rsp, [rax]
        mov rbp, [rax + 8]
        jmp [rax + 16]
.nobody:                                ; no try around it: say it and stop the program
        lea rdi, [rel rt_msg_error]
        mov esi, rt_msg_error_len
        call plat_write
        mov rax, [rel rt_exc_kind]
        lea rdi, [rax + 16]
        mov rsi, [rax + 8]
        call plat_write
        lea rdi, [rel rt_msg_colon]
        mov esi, 2
        call plat_write
        mov rax, [rel rt_exc_msg]
        lea rdi, [rax + 16]
        mov rsi, [rax + 8]
        call plat_write
        lea rdi, [rel rt_msg_nl]
        mov esi, 1
        call plat_write
        jmp plat_abort

; ---------------------------------------------------------------- functions as values

rt_func_new:                            ; rdi = code, rsi = values it takes, rdx = kept, rcx = defaults
        push rdi
        push rsi
        push rdx
        push rcx
        lea rdi, [rdx + rcx]
        shl rdi, 3
        add rdi, 40
        call rt_alloc
        pop rcx
        pop rdx
        pop rsi
        pop rdi
        mov qword [rax], T_FUNC
        mov [rax + 8], rdi
        mov [rax + 16], rsi
        mov [rax + 24], rdx
        sub rsi, rcx
        mov [rax + 32], rsi
        ret

rt_call_check:                          ; r10 = the function, rdi = how many values were pushed
        test r10b, 1                    ; -> rax = how many default values to push, rdx = the first of them
        jnz rt_err_call
        cmp qword [r10], T_FUNC
        jne rt_err_call
        mov rcx, [r10 + 16]
        cmp rdi, rcx
        ja rt_err_count
        mov rax, rcx
        sub rax, rdi
        sub rcx, [r10 + 32]
        cmp rax, rcx
        ja rt_err_count
        sub rcx, rax
        add rcx, [r10 + 24]
        lea rdx, [r10 + 40 + rcx*8]
        ret

; ---------------------------------------------------------------- true or not

rt_truth:                               ; rdi = a value -> rax = 1 if it counts as true, else 0
        test dil, 1
        jz .block
        xor eax, eax
        cmp rdi, 1
        setne al
        ret
.block:
        mov rax, [rdi]
        cmp rax, T_NONE
        je .no
        cmp rax, T_BOOL
        je .bool
        cmp rax, T_FLOAT
        je .float
        cmp rax, T_DICT
        jne .length
        mov rdi, [rdi + 16]
.length:
        xor eax, eax
        cmp qword [rdi + 8], 0
        setne al
        ret
.bool:
        mov rax, [rdi + 8]
        ret
.no:
        xor eax, eax
        ret
.float:
        pxor xmm0, xmm0
        ucomisd xmm0, [rdi + 8]
        setne al
        setp cl
        or al, cl
        movzx eax, al
        ret

rt_not:
        call rt_truth
        test al, al
        lea rax, [rel rt_false]
        lea rcx, [rel rt_true]
        cmovz rax, rcx
        ret

; ---------------------------------------------------------------- arithmetic

rt_add:
        RT_BOTH_INT .slow
        lea rax, [rdi + rsi - 1]
        ret
.slow:  RT_SLOW2 f__add

rt_sub:
        RT_BOTH_INT .slow
        mov rax, rdi
        sub rax, rsi
        inc rax
        ret
.slow:  RT_SLOW2 f__sub

rt_mul:
        RT_BOTH_INT .slow
        mov rax, rdi
        sar rax, 1
        lea rcx, [rsi - 1]
        imul rax, rcx
        inc rax
        ret
.slow:  RT_SLOW2 f__mul

rt_div:
        RT_SLOW2 f__truediv

rt_pow:
        RT_SLOW2 f__pow

rt_floordiv:                            ; as in Python: rounds down, towards minus infinity
        RT_BOTH_INT .slow
        mov rax, rdi
        sar rax, 1
        mov rcx, rsi
        sar rcx, 1
        test rcx, rcx
        jz rt_err_zero
        cqo
        idiv rcx
        test rdx, rdx
        jz .done
        mov r8, rdx
        xor r8, rcx
        jns .done
        dec rax
.done:
        lea rax, [rax*2 + 1]
        ret
.slow:  RT_SLOW2 f__floordiv

rt_mod:                                 ; as in Python: the sign of the divisor
        RT_BOTH_INT .slow
        mov rax, rdi
        sar rax, 1
        mov rcx, rsi
        sar rcx, 1
        test rcx, rcx
        jz rt_err_zero
        cqo
        idiv rcx
        test rdx, rdx
        jz .done
        mov r8, rdx
        xor r8, rcx
        jns .done
        add rdx, rcx
.done:
        lea rax, [rdx*2 + 1]
        ret
.slow:  RT_SLOW2 f__mod

rt_neg:
        test dil, 1
        jz .slow
        mov eax, 2
        sub rax, rdi
        ret
.slow:
        push rdi
        call f__neg
        add rsp, 8
        ret

rt_invert:
        test dil, 1
        jz rt_err_type
        mov rax, rdi
        neg rax
        ret

rt_and:
        RT_BOTH_INT rt_bits_and
        mov rax, rdi
        and rax, rsi
        ret

rt_or:
        RT_BOTH_INT rt_bits_or
        mov rax, rdi
        or rax, rsi
        ret

rt_xor:
        RT_BOTH_INT rt_bits_xor
        mov rax, rdi
        xor rax, rsi
        or rax, 1
        ret

%macro RT_BITS 2                        ; sets and True / False: prelude.py does it
rt_bits_%1:
        push rdi
        push rsi
        push %2
        call f__bitop
        add rsp, 24
        ret
%endmacro
        RT_BITS and, 1
        RT_BITS or, 3
        RT_BITS xor, 5

rt_shl:
        RT_BOTH_INT rt_err_type
        mov rcx, rsi
        sar rcx, 1
        lea rax, [rdi - 1]
        shl rax, cl
        or rax, 1
        ret

rt_shr:
        RT_BOTH_INT rt_err_type
        mov rcx, rsi
        sar rcx, 1
        mov rax, rdi
        sar rax, cl
        or rax, 1
        ret

; ---------------------------------------------------------------- comparing

rt_eq:
        cmp rdi, rsi
        je .yes
        RT_BOTH_INT .slow
        lea rax, [rel rt_false]
        ret
.yes:
        lea rax, [rel rt_true]
        ret
.slow:  RT_SLOW2 f__eq

rt_ne:
        call rt_eq
        lea rcx, [rel rt_true]
        cmp rax, rcx
        lea rax, [rel rt_false]
        cmovne rax, rcx
        ret

rt_lt:
        RT_BOTH_INT .slow
        cmp rdi, rsi
        setl al
        RT_BOOL
.slow:  RT_SLOW2 f__lt

rt_le:
        RT_BOTH_INT .slow
        cmp rdi, rsi
        setle al
        RT_BOOL
.slow:  RT_SLOW2 f__le

rt_gt:
        xchg rdi, rsi
        jmp rt_lt

rt_ge:
        xchg rdi, rsi
        jmp rt_le

rt_is:
        cmp rdi, rsi
        sete al
        RT_BOOL

rt_isnot:
        cmp rdi, rsi
        setne al
        RT_BOOL

rt_in:                                  ; rdi = what is looked for, rsi = where
        push rsi
        push rdi
        call f__contains
        add rsp, 16
        ret

rt_notin:
        call rt_in
        mov rdi, rax
        jmp rt_not

; ---------------------------------------------------------------- texts, lists, dicts

rt_len:                                 ; -> a whole number (as a value)
        test dil, 1
        jnz rt_err_type
        mov rax, [rdi]
        cmp rax, T_DICT
        jne .check
        mov rdi, [rdi + 16]
.check:
        cmp rax, T_FLOAT
        je rt_err_type
        cmp rax, T_SET
        je .ok
        cmp rax, T_NONE
        jae rt_err_type
.ok:
        mov rax, [rdi + 8]
        lea rax, [rax*2 + 1]
        ret

rt_str_new:                             ; rdi = length (a plain number) -> a text of zero bytes
        push rdi
        add rdi, 17
        call rt_alloc
        pop rcx
        mov qword [rax], T_STR
        mov [rax + 8], rcx
        ret

rt_getitem:                             ; rdi = the thing, rsi = the index or the key
        test dil, 1
        jnz rt_err_type
        mov rax, [rdi]
        cmp rax, T_DICT
        je .dict
        test sil, 1
        jz rt_err_index_type
        mov rcx, rsi
        sar rcx, 1
        mov rdx, [rdi + 8]
        test rcx, rcx
        jns .from_start
        add rcx, rdx
.from_start:
        cmp rcx, rdx
        jae rt_err_index
        cmp rax, T_STR
        je .text
        cmp rax, T_LIST
        je .list
        cmp rax, T_TUPLE
        jne rt_err_type
.list:
        mov rax, [rdi + 24]
        mov rax, [rax + rcx*8]
        ret
.text:
        movzx r8d, byte [rdi + 16 + rcx]
        push r8
        mov edi, 1
        call rt_str_new
        pop r8
        mov [rax + 16], r8b
        ret
.dict:  RT_SLOW2 f__dict_get

rt_setitem:                             ; rdi = the thing, rsi = the index or the key, rdx = the value
        test dil, 1
        jnz rt_err_type
        mov rax, [rdi]
        cmp rax, T_DICT
        je .dict
        cmp rax, T_LIST
        jne rt_err_type
        test sil, 1
        jz rt_err_index_type
        mov rcx, rsi
        sar rcx, 1
        mov r8, [rdi + 8]
        test rcx, rcx
        jns .from_start
        add rcx, r8
.from_start:
        cmp rcx, r8
        jae rt_err_index
        mov rax, [rdi + 24]
        mov [rax + rcx*8], rdx
        lea rax, [rel rt_none]
        ret
.dict:
        push rdi
        push rsi
        push rdx
        call f__dict_set
        add rsp, 24
        ret

rt_list_new:                            ; rdi = room (a plain number) -> an empty list
        cmp rdi, 4
        jae .room
        mov edi, 4
.room:
        push rdi
        shl rdi, 3
        call rt_alloc
        push rax
        mov edi, 32
        call rt_alloc
        pop rdx
        pop rcx
        mov qword [rax], T_LIST
        mov qword [rax + 8], 0
        mov [rax + 16], rcx
        mov [rax + 24], rdx
        ret

rt_list_push:                           ; rdi = the list, rsi = a value -> rax = the list
        mov rcx, [rdi + 8]
        cmp rcx, [rdi + 16]
        jb .fits
        push rdi
        push rsi
        mov rdi, [rdi + 16]
        shl rdi, 4                      ; twice the room, 8 bytes each
        call rt_alloc
        pop rsi
        pop rdi
        mov rcx, [rdi + 8]
        mov r8, [rdi + 24]
        xor edx, edx
.copy:
        cmp rdx, rcx
        jae .copied
        mov r9, [r8 + rdx*8]
        mov [rax + rdx*8], r9
        inc rdx
        jmp .copy
.copied:
        mov [rdi + 24], rax
        shl qword [rdi + 16], 1
.fits:
        mov rcx, [rdi + 8]
        mov rax, [rdi + 24]
        mov [rax + rcx*8], rsi
        inc qword [rdi + 8]
        mov rax, rdi
        ret

rt_dict_new:
        xor edi, edi
        call rt_list_new
        push rax
        xor edi, edi
        call rt_list_new
        push rax
        mov edi, 32
        call rt_alloc
        pop rdx
        pop rcx
        mov qword [rax], T_DICT
        mov [rax + 16], rcx
        mov [rax + 24], rdx
        ret

rt_float_new:                           ; xmm0 -> a float value
        sub rsp, 8
        movsd [rsp], xmm0
        mov edi, 16
        call rt_alloc
        movsd xmm0, [rsp]
        add rsp, 8
        mov qword [rax], T_FLOAT
        movsd [rax + 8], xmm0
        ret

; ---------------------------------------------------------------- what prelude.py is built on
; (called from PyTon by their names with a "_": _type(x) is i_type, and so on)

i_type:                                 ; 0 number, 1 text, 2 list, 3 dict, 4 float, 5 tuple, 6 None, 7 bool
        test dil, 1
        jz .block
        mov eax, 1
        ret
.block:
        mov rax, [rdi]
        lea rax, [rax*2 + 1]
        ret

i_str_new:
        sar rdi, 1
        jmp rt_str_new

i_sget:                                 ; (text, i) -> the byte
        sar rsi, 1
        movzx eax, byte [rdi + 16 + rsi]
        lea rax, [rax*2 + 1]
        ret

i_sset:                                 ; (text, i, byte)
        sar rsi, 1
        sar rdx, 1
        mov [rdi + 16 + rsi], dl
        lea rax, [rel rt_none]
        ret

i_lget:                                 ; (list, i) with no checks
        sar rsi, 1
        mov rax, [rdi + 24]
        mov rax, [rax + rsi*8]
        ret

i_lset:
        sar rsi, 1
        mov rax, [rdi + 24]
        mov [rax + rsi*8], rdx
        lea rax, [rel rt_none]
        ret

i_lsetlen:
        sar rsi, 1
        mov [rdi + 8], rsi
        lea rax, [rel rt_none]
        ret

i_list_new:
        sar rdi, 1
        jmp rt_list_new

i_dkeys:
        mov rax, [rdi + 16]
        ret

i_dvals:
        mov rax, [rdi + 24]
        ret

i_settype:                              ; (block, kind): a list becomes a tuple
        sar rsi, 1
        mov [rdi], rsi
        mov rax, rdi
        ret

i_bval:                                 ; True / False -> 1 / 0
        mov rax, [rdi + 8]
        lea rax, [rax*2 + 1]
        ret

i_fadd:
        movsd xmm0, [rdi + 8]
        addsd xmm0, [rsi + 8]
        jmp rt_float_new
i_fsub:
        movsd xmm0, [rdi + 8]
        subsd xmm0, [rsi + 8]
        jmp rt_float_new
i_fmul:
        movsd xmm0, [rdi + 8]
        mulsd xmm0, [rsi + 8]
        jmp rt_float_new
i_fdiv:
        movsd xmm0, [rdi + 8]
        divsd xmm0, [rsi + 8]
        jmp rt_float_new
i_fsqrt:
        sqrtsd xmm0, [rdi + 8]
        jmp rt_float_new
i_flt:
        movsd xmm0, [rdi + 8]
        ucomisd xmm0, [rsi + 8]
        setb al
        RT_BOOL
i_feq:
        movsd xmm0, [rdi + 8]
        ucomisd xmm0, [rsi + 8]
        sete al
        setnp cl
        and al, cl
        RT_BOOL
i_i2f:
        sar rdi, 1
        cvtsi2sd xmm0, rdi
        jmp rt_float_new
i_f2i:                                  ; towards zero
        cvttsd2si rax, [rdi + 8]
        lea rax, [rax*2 + 1]
        ret

i_write:                                ; (text): out it goes
        mov rsi, [rdi + 8]
        lea rdi, [rdi + 16]
        call plat_write
        lea rax, [rel rt_none]
        ret

i_readline:                             ; -> a text, without the end of the line
        mov edi, 512
        call rt_str_new
        push rax
        lea rdi, [rax + 16]
        mov esi, 511
        call plat_read
        pop rdx
        test rax, rax
        jns .trim
        xor eax, eax
.trim:
        test rax, rax
        jz .done
        movzx ecx, byte [rdx + 16 + rax - 1]
        cmp cl, 10
        je .cut
        cmp cl, 13
        jne .done
.cut:
        dec rax
        mov byte [rdx + 16 + rax], 0
        jmp .trim
.done:
        mov [rdx + 8], rax
        mov rax, rdx
        ret

i_exit:
        sar rdi, 1
        jmp plat_exit

i_error:                                ; (text): raise Exception(text)
        mov rsi, rdi
        lea rdi, [rel rt_k_exception]
        jmp rt_raise

; ---------------------------------------------------------------- the fixed values and the texts

RT_DATA
        align 16
rt_none:        dq T_NONE, 0
rt_true:        dq T_BOOL, 1
rt_false:       dq T_BOOL, 0
rt_heap_ptr:    dq 0
rt_heap_end:    dq 0
rt_msg_error:   db 'PyTon: '
rt_msg_error_len equ $ - rt_msg_error
rt_msg_nl:      db 10
rt_msg_colon:   db ': '
rt_msg_memory:  db 'no memory left', 0
rt_handler:     dq 0
rt_exc_kind:    dq 0
rt_exc_msg:     dq 0
%macro RT_TEXT_OBJ 2                    ; a text value that is always there
        align 8
%1:     dq T_STR, %%end - %%start
%%start: db %2
%%end:  db 0
%endmacro
        RT_TEXT_OBJ rt_k_exception, 'Exception'
        RT_TEXT_OBJ rt_k_type, 'TypeError'
        RT_TEXT_OBJ rt_k_index, 'IndexError'
        RT_TEXT_OBJ rt_k_zero, 'ZeroDivisionError'
        RT_TEXT_OBJ rt_m_type, 'this cannot be done with a value of this kind'
        RT_TEXT_OBJ rt_m_index, 'the index is outside the list or the text'
        RT_TEXT_OBJ rt_m_index_type, 'an index must be a whole number'
        RT_TEXT_OBJ rt_m_zero, 'division by zero'
        RT_TEXT_OBJ rt_m_call, 'this is not a function'
        RT_TEXT_OBJ rt_m_count, 'the function is called with the wrong number of values'
        align 8
RT_TEXT
