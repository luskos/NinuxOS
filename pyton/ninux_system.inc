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
;       +0x80  call a socket of an object: rdi = object, rsi = the socket's name, rdx, rcx = two values
;              (read from Desktop, which asks a program's "draw" for its icon this way; not connected
;              yet - it is what a relay between two programs will stand on)
;   meaning not known yet: +0x20 +0xA8
; v3.0.11, from the same places: ob_size, ob_data (+0x60), own_len, own_code (+0x70, +0x68),
;       text_meta (+0x70, +0x30), data_dump (+0x68, +0xE0).
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

; ---- v3.0.11: for a folder on the desktop and for a file manager. None of these takes memory,
; ---- so the socket that draws an icon may call them every time the desktop is drawn.
sys_ob_size:                            ; (number of the object) -> its size in bytes
        mov rax, [rel ninux_api]
        call [rax + 0x60]
        test rax, rax
        jz ninux_nothing
        mov rax, [rax + 0x08]
        ret
sys_ob_data:                            ; (number of the object) -> the length of its DATA
        mov rax, [rel ninux_api]
        call [rax + 0x60]
        test rax, rax
        jz ninux_nothing
        mov rax, [rax + 0x58]
        ret

ninux_own:                              ; rdi = an ending -> rax = the object <my name><ending>, or 0
        push rbx                        ; (a name is 15 letters at most: what is over is cut)
        push r12
        mov r12, rdi
        mov rdi, [rel ninux_object]
        lea rsi, [rel ninux_key_name]
        mov rax, [rel ninux_api]
        call [rax + 0x70]
        lea rbx, [rel ninux_own_name]
        xor ecx, ecx
        test rax, rax
        jz ninux_own_ending
ninux_own_copy:
        mov dl, [rax + rcx]
        test dl, dl
        jz ninux_own_ending
        mov [rbx + rcx], dl
        inc ecx
        cmp ecx, 15
        jb ninux_own_copy
ninux_own_ending:
        cmp ecx, 15
        jae ninux_own_find
        mov dl, [r12]
        test dl, dl
        jz ninux_own_find
        mov [rbx + rcx], dl
        inc r12
        inc ecx
        jmp ninux_own_ending
ninux_own_find:
        mov byte [rbx + rcx], 0
        mov rdi, rbx
        mov rax, [rel ninux_api]
        call [rax + 0x68]
        pop r12
        pop rbx
        ret
sys_own_len:                            ; (ending) -> the length of the DATA of <my name><ending>; 0: none
        call ninux_own
        test rax, rax
        jz ninux_nothing
        mov rax, [rax + 0x58]
        ret
sys_own_code:                           ; (ending, i) -> the code of letter i of that DATA; 0: beyond it
        push rsi
        call ninux_own
        pop rsi
        test rax, rax
        jz ninux_nothing
        cmp rsi, [rax + 0x58]
        jae ninux_own_beyond
        add rax, [rax + 0x10]
        movzx eax, byte [rax + rsi]
        ret
ninux_own_beyond:
        xor eax, eax
        ret

sys_text_meta:                          ; (x of the middle, y, key, colour): a value of my META, drawn
        push rbx
        push r12
        push r13
        mov rbx, rdi
        mov r12, rsi
        mov r13, rcx
        mov rdi, [rel ninux_object]
        mov rsi, rdx
        mov rax, [rel ninux_api]
        call [rax + 0x70]
        test rax, rax
        jz ninux_text_meta_out
        xor ecx, ecx
ninux_text_meta_length:
        cmp byte [rax + rcx], 0
        je ninux_text_meta_draw
        inc ecx
        jmp ninux_text_meta_length
ninux_text_meta_draw:
        shl ecx, 2                      ; a letter is 8 dots wide: half of the width
        sub rbx, rcx
        mov rdi, rbx
        mov rsi, r12
        mov rdx, rax
        mov rcx, r13
        call sys_text
ninux_text_meta_out:
        pop r13
        pop r12
        pop rbx
        ret

sys_data_dump:                          ; (name of an object, a new name): its DATA out, as an object of
        push rsi                        ; its own; the object keeps them. -> 0 no such object or no DATA
        mov rax, [rel ninux_api]
        call [rax + 0x68]
        pop rdi
        test rax, rax
        jz ninux_nothing
        mov rcx, [rax + 0x58]
        test rcx, rcx
        jz ninux_dump_none
        mov rsi, rax
        add rsi, [rax + 0x10]
        lea r10, [rel ninux_meta_data]
        mov r11d, ninux_meta_data_end - ninux_meta_data
        push rcx
        call ninux_save_sized
        pop rax                         ; how many bytes went out
        ret
ninux_dump_none:
        xor eax, eax
        ret

sys_save_text:                          ; (name, text): keep the text as an object of the cabinet
        lea r10, [rel ninux_meta_text]
        mov r11d, ninux_meta_text_end - ninux_meta_text
        jmp ninux_save
sys_save_page:                          ; (name, html): keep it as a page
        lea r10, [rel ninux_meta_page]
        mov r11d, ninux_meta_page_end - ninux_meta_page
ninux_save:                             ; the object is made here whole, as the old runtime made it:
        mov rcx, -1                     ; header, DATA, META, the end - the system gives the identity
ninux_save_sized:                       ; rcx = the length of the DATA (-1: a text, up to its zero)
        push rbx
        push r12
        push r13
        push r14
        push r15
        push rbp
        mov r12, rdi
        mov r13, rsi
        mov r15, r10
        mov rbp, r11
        mov r14, rcx
        cmp rcx, -1
        jne ninux_save_make
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
ninux_meta_data:
        db 'type:data', 0, 'kind:data', 0, 'data:the DATA of an object, taken out by data dump', 0, 0
ninux_meta_data_end:
ninux_key_name: db 'name', 0
ninux_own_name: times 16 db 0
ninux_open:     db 'open', 0
ninux_system_names:                     ; system(name): the number of the name is what the system is asked
        db 'cpu', 0, 'cores', 0, 'memory', 0, 'screen', 0, 'graphics', 0, 'disk', 0, 'version', 0
        db 'year', 0, 'month', 0, 'day', 0, 'hour', 0, 'minute', 0, 'second', 0, 'time', 0, 0
        align 8
ninux_rating:   dq 0
%endmacro
