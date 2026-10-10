; ninux_system.inc - the functions of NinuxOS a PyTon program calls by name, second part (v3.0.02).
; Included by platform_ninux.inc; the first part (fill, text, window, poll ...) is there.
; Read from the runtime of the programs v2.9.59 was shipped with; not tried in the system yet.
;
; More places of the system's table:
;       +0x10  the screen: rax = width, rdx = height                  (spawn passes them on)
;       +0x58  ob_count()
;       +0x60  the object number rdi -> its address (0: none)
;       +0x68  the object named rdi -> its address (0: none); its DATA is at address + [address+0x10]
;       +0x90  random(n)
;       +0xA0  ticks()
;       +0xE0  save an object: rdi = name, rsi = address, rdx = size (identity 0: the system gives it)
;       +0x118 programs: edi = 0 open (rsi object, rdx 'open', rcx, r8 = the screen),
;              0x0A kill (rsi name), 0x0E key_send (rsi key, rdx modifiers)
;       +0x128 a text into a 64-byte buffer: edi = the number of a system() name, or 1000 + a log line
;       +0x138 sound: edi = 2 play (rsi hertz, rdx ms), 3 stop; 1 a sound object (not connected)
;       +0x150 the network: edi = 0 state, 2 the answer into a buffer; 1 likely ask (not connected)
;   meaning not known yet: +0x20 +0x80 +0xA8
; Not connected yet: load_image, save_image (Paint, Nest), sound_play (PyNamp),
;       net_ask, net_answer, net_state (Ask), time.

%macro NINUX_SYSTEM_CODE 0
sys_ticks:                              ; 100 a second
        NINUX_API 0xA0
sys_random:                             ; (n) -> 0 .. n-1
        NINUX_API 0x90
sys_ob_count:                           ; how many objects the cabinet has
        NINUX_API 0x58
sys_screen_w:
        NINUX_API 0x10
sys_screen_h:
        mov rax, [rel ninux_api]
        call [rax + 0x10]
        mov rax, rdx
        ret

sys_load_text:                          ; (name) -> the DATA of that object as a text, or 0
        mov rax, [rel ninux_api]
        call [rax + 0x68]
        test rax, rax
        jz ninux_nothing
        add rax, [rax + 0x10]
ninux_nothing:
        ret

sys_ob_meta:                            ; (number of the object, key) -> its META value, or 0
        push rsi
        mov rax, [rel ninux_api]
        call [rax + 0x60]
        jmp ninux_meta_value
sys_meta_of:                            ; (name of the object, key)
        push rsi
        mov rax, [rel ninux_api]
        call [rax + 0x68]
ninux_meta_value:
        pop rsi
        test rax, rax
        jz ninux_nothing
        mov rdi, rax
        NINUX_API 0x70

sys_system:                             ; (what) -> a text: "hour", "year", "cpu" ... (ninux_system_names)
        push rbx
        push r12
        push r13
        mov r12, rdi
        lea r13, [rel ninux_system_names]
        xor ebx, ebx
ninux_system_next:
        cmp byte [r13], 0
        je ninux_system_none
        mov rsi, r13
        mov rdi, r12
ninux_system_compare:
        mov al, [rsi]
        cmp al, [rdi]
        jne ninux_system_skip
        test al, al
        jz ninux_system_found
        inc rsi
        inc rdi
        jmp ninux_system_compare
ninux_system_skip:
        cmp byte [r13], 0
        lea r13, [r13 + 1]
        jne ninux_system_skip
        inc ebx
        jmp ninux_system_next
ninux_system_found:
        mov edi, 0x40
        call rt_alloc
        mov r12, rax
        mov edi, ebx
        mov rsi, r12
        mov rax, [rel ninux_api]
        call [rax + 0x128]
        mov rax, r12
        jmp ninux_system_out
ninux_system_none:
        xor eax, eax
ninux_system_out:
        pop r13
        pop r12
        pop rbx
        ret

sys_logline:                            ; (n) -> line n of the system's log, or an empty text
        push rbx
        push r12
        mov rbx, rdi
        mov edi, 0x40
        call rt_alloc
        mov r12, rax
        lea rdi, [rbx + 1000]
        mov rsi, r12
        mov rax, [rel ninux_api]
        call [rax + 0x128]
        test rax, rax
        jns ninux_logline_ok
        mov byte [r12], 0
ninux_logline_ok:
        mov rax, r12
        pop r12
        pop rbx
        ret

sys_spawn:                              ; (name): open that program in a window; -1: no such object
        push rbx
        push r12
        push r13
        mov rax, [rel ninux_api]
        call [rax + 0x68]
        test rax, rax
        jz ninux_spawn_none
        mov rbx, rax
        mov rax, [rel ninux_api]
        call [rax + 0x10]               ; the screen: width, height
        mov r12, rax
        mov r13, rdx
        xor edi, edi
        mov rsi, rbx
        lea rdx, [rel ninux_open]
        mov rcx, r12
        mov r8, r13
        mov rax, [rel ninux_api]
        call [rax + 0x118]
        jmp ninux_spawn_out
ninux_spawn_none:
        mov rax, -1
ninux_spawn_out:
        pop r13
        pop r12
        pop rbx
        ret

sys_kill:                               ; (name): close that program
        mov rsi, rdi
        mov edi, 0x0A
        NINUX_API 0x118
sys_key_send:                           ; (key, shift + ctrl*2 + alt*4): a key for the window underneath
        mov rdx, rsi
        mov rsi, rdi
        mov edi, 0x0E
        NINUX_API 0x118
sys_play:                               ; (hertz, milliseconds): a tone
        mov rdx, rsi
        mov rsi, rdi
        mov edi, 2
        NINUX_API 0x138
sys_sound_stop:
        mov edi, 3
        NINUX_API 0x138
sys_save_rating:                        ; (age): the rating the next saved object gets
        mov [rel ninux_rating], rdi
        ret

sys_save_text:                          ; (name, text): keep the text as an object of the cabinet
        lea r10, [rel ninux_meta_text]
        mov r11d, ninux_meta_text_end - ninux_meta_text
        jmp ninux_save
sys_save_page:                          ; (name, html): keep it as a page
        lea r10, [rel ninux_meta_page]
        mov r11d, ninux_meta_page_end - ninux_meta_page
ninux_save:                             ; the object is made here whole, as the old runtime made it:
        push rbx                        ; header, DATA, META, the end - the system gives the identity
        push r12
        push r13
        push r14
        push r15
        push rbp
        mov r12, rdi
        mov r13, rsi
        mov r15, r10
        mov rbp, r11
        xor r14d, r14d
ninux_save_length:
        cmp byte [r13 + r14], 0
        je ninux_save_make
        inc r14
        jmp ninux_save_length
ninux_save_make:
        lea rbx, [r14 + 0x70]
        and rbx, -8                     ; where META starts
        lea rdi, [rbp + rbx + 0x17]
        and rdi, -8                     ; the size of the object
        push rdi
        call rt_alloc
        pop rcx
        mov rdx, rax
        mov dword [rdx], 0x41534D4F     ; 'OMSA'
        mov dword [rdx + 0x04], 4
        mov [rdx + 0x08], rcx
        mov qword [rdx + 0x10], 0x68
        mov [rdx + 0x18], rbx
        mov qword [rdx + 0x38], 1
        mov dword [rdx + 0x48], 2
        mov eax, [rel ninux_rating]
        shl eax, 8
        mov [rdx + 0x50], eax
        mov [rdx + 0x58], r14
        lea rdi, [rdx + 0x68]
        mov rsi, r13
        push rcx
        mov rcx, r14
        rep movsb
        lea rdi, [rdx + rbx]
        mov rsi, r15
        mov rcx, rbp
        rep movsb
        pop rcx
        lea rax, [rdx + rcx - 0x10]
        mov [rax], rcx
        mov dword [rax + 8], 0x4F4D5341 ; 'ASMO'
        mov rdi, r12
        mov rsi, rdx
        mov rdx, rcx
        mov rax, [rel ninux_api]
        call [rax + 0xE0]
        pop rbp
        pop r15
        pop r14
        pop r13
        pop r12
        pop rbx
        ret

ninux_meta_text:
        db 'type:text', 0, 'kind:text', 0, 'data:text saved by a PyTon program', 0, 0
ninux_meta_text_end:
ninux_meta_page:
        db 'type:page', 0, 'kind:page', 0, 'lang:html', 0, 'data:a page made inside NinuxOS', 0, 0
ninux_meta_page_end:
ninux_open:     db 'open', 0
ninux_system_names:                     ; system(name): the number of the name is what the system is asked
        db 'cpu', 0, 'cores', 0, 'memory', 0, 'screen', 0, 'graphics', 0, 'disk', 0, 'version', 0
        db 'year', 0, 'month', 0, 'day', 0, 'hour', 0, 'minute', 0, 'second', 0, 'time', 0, 0
        align 8
ninux_rating:   dq 0
%endmacro
