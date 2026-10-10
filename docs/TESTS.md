# NinuxOS v3 - пълен списък на системните тестове

За собственика. Прави се върху билда от `NinuxOS_v3` (версията е във файла `VERSION`; долу е
писана като `v3.0.06`; гледай `VERSION` за текущата; новото от v3.0.11 е в част K). Редът е важен: всяка част стъпва на предишната. До всеки тест пише какво
трябва да се види и какво значи, ако не се види.

Отбелязвай с `[x]` минал, `[!]` неминал, и запиши точния текст от екрана при `[!]`.

---

## A. На компютъра, преди флашката

- [ ] **A1. Билд.** `python tools\build_disk.py`
  Очаквано: `the version the system says (v3.0.06, 5 places)`, `added: pycalc`, `added: pyhello`,
  `4 kernel suits signed; the Sentinel list: 98 lines, 5 written anew, 1 left as they were; signed`.
  Ако спре с грешка: препиши ми я цялата.
- [ ] **A2. Езикът.** `python pyton\test.py`
  Очаквано: `basics ok`, `more ok`, `2 of 2 the same`.
  Ако Windows каже, че файлът съдържа вирус: Defender е спрял пробния `.exe`; кажи ми.
- [ ] **A3. Сорсът се асемблира до същото.** `python tools\kdis\kdis.py` и `python tools\kdis\odis.py`
  Очаквано: `assembles to the same bytes: YES`; при второто всеки ред съдържа `SAME`.
- [ ] **A4. Контейнерът със сорса.** `python tools\source_container.py check build\source\NinuxOS_source.nxc`
  Очаквано: `NinuxOS v3.0.06 ... whole`.
- [ ] **A5. Ключът.** Има ли файл `build\key\build.key`? Копирай го на сигурно място (не в git).

## B. Puffus и флашката

- [ ] **B1.** Затвори отворения Puffus и пусни `tools\puffus\make_puffus.cmd`.
  Очаквано: `Done: Puffus.exe is in the project folder`.
- [ ] **B2.** Защитата от запис по USB трябва да е изключена, иначе Puffus не може да пише:
  `reg query HKLM\SYSTEM\CurrentControlSet\Control\StorageDevicePolicies /v WriteProtect` -> `0x0`
  (ако е `0x1`: `reg add ... /v WriteProtect /t REG_DWORD /d 0 /f` и извади/сложи флашката).
- [ ] **B3.** Пусни `Puffus.exe` от `NinuxOS_v3`, избери флашката, `Write NinuxOS to the stick`.
  Очаквано в прозореца, по ред: редовете на билда; `Drive X: locked and dismounted`;
  `Writing 46136 sectors`; `Reading it back`; `Writing the source container`;
  `Done: the stick holds NinuxOS and was checked`; `It is ejected - take it out`.
- [ ] **B4.** НЕ включвай флашката обратно в Windows (ще я повреди). Ако се наложи: първо
  `WriteProtect` = 1 и рестарт.

## C. Зареждане (най-важният тест - решава дали подписването е вярно)

- [ ] **C1.** Стартирай тестовата машина от флашката.
  Очаквано: `NinuxOS boot`, после `NinuxOS v3.0.06 - loading cabinet`, после shell-ът с
  `NinuxOS v3.0.06 - Functional Objects (DATA + META + SOCKETS)` и `ninux>`.
- [ ] **C2.** На екрана НЕ трябва да има: `system operations off`, `SHA-256 MISMATCH`,
  `THE EXTENSION FAILED ITS SHA-256 CHECK`, `signature is WRONG`, `Kernel suit refused`.
- [ ] **C3.** `version`, `info`, `machine` - и трите трябва да казват v3.0.06.

**Ако C1 не мине** (не тръгва, черен екран, или текст от C2), билдвай поред и пробвай пак;
първият, който тръгне, показва коя част е грешна:

1. `python tools\build_disk.py --no-seal` -> ако тръгне: грешно е подписването.
2. `python tools\build_disk.py --keep-version` -> ако тръгне: грешно е записването на версията.
3. Махни файловете от `build\add\` и билдни -> ако тръгне: грешно е добавянето в кабинета.
4. `python tools\build_disk.py --keep-version --no-seal` без `build\add` = чистата v2.9.59.
   Ако и тя не тръгне, проблемът е в Puffus или във флашката, не в билда.

## D. Печатите (Sentinel и суитовете)

- [ ] **D1.** `sentinel`
  Очаквано: накрая `98 system objects checked - 1 CHANGED or MISSING` - точно както при v2.9.59
  (едното е страницата `donate`). `@kernel` трябва да е `genuine`.
  Ако пише повече от 1 CHANGED: запиши кои (червените редове; PgUp не работи, гледай края).
  Ако пише `the manifest's signature is WRONG`: подписът на списъка е грешен.
- [ ] **D2.** `kasm` - списъкът на суитовете. `k_tools` се слага сам при зареждането; другите
  с командите `sound` (-> `k_sound`), `net` (-> `k_net`), `usb` (-> `k_usb12`).
  Очаквано: работят както преди. Грешка `Kernel suit refused (bad signature or built for
  another kernel)` значи, че подписът на суита е грешен.
- [ ] **D3.** `shield test` - очаквано: `Shield test passed: an object that wrote into the kernel was stopped.`

## E. Кабинетът и добавените обекти

- [ ] **E1.** `ls` - в списъка трябва да има `pycalc` и `pyhello` (към края), и старите 47.
  Първият ред на зареждането в лога казва `cabinet objects: 109` (бяха 107).
- [ ] **E2.** `meta pyhello` - очаквано: `type:demo`, `name:pyhello`, `label:PyHello`,
  `sockets:run,numbers`, `lang:pyton`, `made:py2asm (v3.0.06)`.
- [ ] **E3.** `view pyhello` и `id pyhello` - да не гърмят. Запиши какво казва `id`
  (идентичността е оставена 0 - интересува ме какво показва системата).
- [ ] **E4.** `disk` и `room` - да показват обектите без грешка.

## F. Програмите от новия py2asm (нищо от това не е виждано досега)

- [ ] **F1.** `run pyhello`
  Очаквано ЕДНО от двете, и двете са полезен отговор:
  (а) `Hello from the new py2asm! I was run 1 time(s).` и ред `My type is demo, my name is pyhello`;
  (б) `This object's code is not verified by the Sentinel: it runs only as a program in a window`
  - тогава билдът трябва да добавя новите обекти в списъка на Sentinel (следваща стъпка за мен).
- [ ] **F2.** Ако F1 е (а): `run pyhello numbers`
  Очаквано: `no key 'three'` и ред `[1, 4, 9, 16, 25, 36, 49] 140 ['one', 'two'] 3.5 ff`.
- [ ] **F3.** `desktop` - има ли втора икона `Calc` (това е `pycalc`)? Отвори я.
  Очаквано: същият прозорец като стария Calc. Натисни `7*6=` -> `42`. Esc затваря.
  Запиши всяка разлика със стария Calc: цвят, място, липсващ текст, бутон, който не реагира.
- [ ] **F4.** Ако някоя от тях гръмне: `[shield] object fault: Page fault at ...` - запиши адреса.

## G. Всичко старо още работи (същото като v2.9.59)

Shell, по една команда; очаква се същото поведение като преди:

- [ ] **G1.** `help` (страници, Esc), `ls`, `whoami`, `uptime`, `machine`, `cores`, `cores test`
- [ ] **G2.** `mem`, `memtest` (`64 allocations ... OK`), `pci`, `disk`, `room`
- [ ] **G3.** `sources` (всички `compiled, up to date`, две `OUT OF DATE` както преди), `meta calc`, `view about`, `id calc`
- [ ] **G4.** `run hello`, `run hello shout`, `echo test`, `colors amber`, `colors classic`, `level`, `spaces`
- [ ] **G5.** `bench` (8 реда с числа), `sgpu test`
- [ ] **G6.** `maint` -> задай парола; `copy hello hello2`, `rename hello2 hello3`, `delete hello3`, `maint`

Десктоп (`desktop`, Esc затваря Setup):

- [ ] **G7.** Отвори и затвори с Esc всяка: Readme, Sunset, Mail, Copycat, PyNamp, NET, Studio,
  Search, Calc, Paint, Interfacer, Projector, Chronos, Notepad, Device, Console, Nest, Widgets
- [ ] **G8.** Чекмеджето `archive` -> Phone, Ask, Keys
- [ ] **G9.** На цял екран: Photon, ASMONCRAFT, Tuner, META; и Puffer
- [ ] **G10.** Task test, Core test
- [ ] **G11.** Известните дефекти още ли са същите: Bags гърми при Esc; Support показва текста на Puffer.

## H. Контейнерът със сорса на флашката

- [ ] **H1.** На Windows: `WriteProtect` = 1, рестарт, включи флашката, Administrator PowerShell:
  `python tools\source_container.py check \\.\PhysicalDriveN` (N от `Get-Disk`)
  Очаквано: `NinuxOS v3.0.06 ... whole`.
- [ ] **H2.** След това системата на флашката още ли тръгва? (Дали мястото на 1 GiB е свободно.)

## I. Доказателството, че в ядрото може да се добавя код

Чак след като C-G минат.

- [ ] **I1.** В `kernel\Kernel.kasm` намери реда `cmd_version:` и сложи под него нов ред
  `        nop`. Билдни. Билдът трябва да каже `the kernel (kernel/Kernel.kasm)` сред променените.
- [ ] **I2.** Запиши на флашка, стартирай, мини през C и G1-G5.
  Ако всичко работи: в ядрото може да се пише нов код.
  Ако не тръгне или команда гръмне: някъде адрес още е число - кажи ми коя команда и какво пише.
- [ ] **I3.** Махни реда `nop` и билдни пак (върни ядрото както беше).

## J. Вместо флашка: в QEMU

Същите тестове C-G могат да минат и на компютъра:

    python tools\qemu\qrun.py test\qemu\q_v2959_shell.txt --show
    python tools\qemu\qrun.py test\qemu\q_v2959_apps.txt --show

`--show` отваря прозореца на QEMU; снимките и `serial.log` отиват в `test\qemu\out`.
В `serial.log` търси: `SHA-256 ok`, `[sentinel] system objects checked`, `[kasm] on: k_tools`,
`[chain] the system started`, и да няма `refused`, `MISMATCH`, `fault`.

## K. Новото във v3.0.11 (нищо от него не е пускано)

Първо C1-C3 (тръгва ли). Ако не тръгне, билдвай поред и пробвай - първият, който тръгне, показва виновника:
`--plain-kernel` (без Alt + * в ядрото), после `--old-boot` (старият boot сектор), после и двете.

- [ ] **K1. Билд.** Очаквано сред редовете: `the boot sector`, `the kernel`, `Bags.Source.asmo (from apps/Bags.asmo)`,
  `Taskbar.asmo (from pages/Taskbar.asmo)`, `the suit k_tools`, `a new page: curtain`, `added: bags (in the place of the old one`,
  `added: files`, `added: socials`, `the Sentinel list: 103 lines (5 new)`.
- [ ] **K2. Boot секторът.** Тръгва ли от флашката на тестовата машина (някои BIOS-и гледат таблицата с дялове)?
  После, с `WriteProtect` = 1: включи флашката в Windows - не трябва да се появи буква на диск, нито въпрос за форматиране
  с възможност за запис. Кажи ми какво точно показва Windows.
- [ ] **K3. Alt + \*.** В shell: Alt + звездата на цифровата клавиатура (или Alt + Shift + 8) - екранът гасне; пак - светва.
  Същото на десктопа и в отворена програма. Кажи: гасне ли изобщо (на тази машина), връща ли се картината цяла,
  с USB клавиатура работи ли. В QEMU също.
- [ ] **K4. `sentinel`.** Очаквано: `103 system objects checked - 1 CHANGED or MISSING` (пак само `donate`).
  Ако спре, гръмне или каже по-малко от 103: ядрото има таван за редовете - кажи ми числото.
- [ ] **K5. Пет потребители.** `user add` до шестия: при шестия трябва да каже `Five people are known by now: ...`.
- [ ] **K6. Bags.** На десктопа иконата е папка (тъмно квадратче, празно). Клик: панел без рамка в средата.
  `+` -> списък -> избери Calc; пак за още 2-3. Затвори с Esc: гърми ли? Иконата показва ли цветни квадратчета за нещата вътре
  (може да трябва прерисуване на десктопа)? Клик на нещо вътре: стартира ли го и затваря ли се панелът? Десен бутон: вади ли го?
  `L`, парола, Enter -> иконата става ключалка; отвори пак: пита ли за парола?
  Ако панелът без рамка обърква десктопа (остава на екрана, не се затваря): в `apps/Bags.asmo` смени `FRAME = 0` на `FRAME = 1` и билдни.
- [ ] **K7. Files.** Икона шкаф. Списък с обекти, стрелки/PgUp/PgDn, долу описанието. Enter върху програма; `D` върху страница
  (напр. `taskbar`) -> `data dump: ... are now the object 'taskbar_data'`; после `ls` и `view taskbar_data` в shell. `T` - само един тип.
- [ ] **K8. Settings.** Бутон `Settings` в лентата долу вдясно -> страницата. Плочките сменят ли частта? Night/Day/Ocean? Името?
- [ ] **K9. Socials.** Икона с три човечета, прозорец с текст, Esc.
- [ ] **K10. `sources`.** Какво казва за `bags` (очаквам може би `OUT OF DATE` - хешът на сорса не се смята още).
- [ ] **K11. Шрифтът.** `python tools\make_font.py Exo-Medium` -> виж `build\font\preview.txt`. Ако ти харесва: същото с `--use`, билд,
  и кажи: смени ли се шрифтът в shell, или само на десктопа? Връщане: `python tools\make_font.py --back`.

## L. v3.0.12: проектът вътре в системата

- [ ] **L1.** Билдът казва `the drawer project: 5 texts (changelog, todo, directive, protocols, tests), 2 program sources`.
- [ ] **L2.** В shell: `ls` - има ли `project`? Как се влиза в чекмедже от shell (както в `archive`)? `view todo`, `view changelog` -
  чете ли се, върти ли се (42 KB текст)? На десктопа: чекмеджето `project` отваря ли се?
- [ ] **L3.** `sources` - показва ли `files` и `socials` и какво казва за тях.
- [ ] **L4. (по желание)** `python tools\build_disk.py --source-inside` - целият сорс и разговорите като обект `nxsource` (19 MB).
  Тръгва ли системата, колко се бави стартът, `mem` преди и след. Ако е наред - ще стане правило за всеки билд.

## M. v3.0.13: старите програми от новия py2asm

- [ ] **M1.** `python tools\build_disk.py --compare` - очаквано: `the drawer compare: 19 programs ...`.
- [ ] **M2.** На десктопа чекмеджето `compare`: отвори всяка `pyNAME` и я сравни със старата (същият прозорец, същите клавиши).
  Особено: pypaint и pynest (запис и зареждане на картинка), pypynamp (звук), pyask (мрежа), pynotepad (писане, запис).
  За всяка разлика или `[shield] object fault` - коя програма, какво направи, какво пише.

## N. v3.0.16: програмите остават живи

- [ ] **N1.** Отвори Files (или Notepad с написан текст), иди в shell (бутонът `>_` в лентата), напиши `mem`, после `desktop`.
  Очаквано: прозорецът е там, както си го оставил, и приема клавиши. В лога: `[mux] the desktop was left: the programs that run are kept`.
- [ ] **N1a. (v3.0.19)** Със запазена програма, в shell: `tasks` (номер и име), `tasks close 1` -> `Closed.`, пак `tasks`
  -> `No programs are kept...`, `mem` показва върнатата памет.
- [ ] **N2.** Същото с две-три програми наведнъж; с Photon или друга на цял екран; с `cores all`.
- [ ] **N3.** Докато има запазени програми: `shutdown`, `maint`, `update` - държат ли се нормално?

## O. v3.0.19 - v3.0.21

- [ ] **O1.** `cores solo` без `maint`: вече казва `(For this session...)` и `Solo: ...`. `bench` преди и след: ред 8 трябва да се
  промени (при споделена работа е няколко пъти по-малък от ред 7; при solo са почти равни). Ако на твоята машина ред 7 и 8
  са еднакви и БЕЗ solo: препиши ми какво казва `cores`.
- [ ] **O2.** `cores all`, после `desktop` с две-три програми - стабилно ли е на истинската машина?
- [ ] **O3.** Програмите от новия py2asm (Bags, Files) след дълга работа: `mem` в shell преди и след - паметта не трябва да расте постоянно.

## P. v3.0.23: клавиатура на екрана в shell

- [ ] **P1.** В shell: `keyboard` -> пет реда клавиши долу. С мишката: напиши `mem` и натисни Enter. Shift + буква -> главна.
  Back трие. Esc. Up/Down - предишни команди? `keyboard` пак я маха.
- [ ] **P1a. (v3.0.24)** Без да пишеш нищо: клик в долния десен ъгъл на екрана в shell -> клавиатурата излиза.
- [ ] **P2.** Същото с USB мишка и (ако имаш машина) със сензорен екран - идват ли кликовете?
- [ ] **P3.** С включена клавиатура: `ls` (дълъг списък с паузи), `help` - текстът не трябва да влиза под клавишите.

## Q. v3.0.24 - v3.0.25: таблицата два пъти и тихият backup

- [ ] **Q1.** На флашка или диск над 64 MB: запиши нещо от програма (текст в Notepad, нещо в Bags). В shell: `backup` -
  има ли ред за записа? `backup get 1` -> `Brought back as it was saved: ...`.
- [ ] **Q2.** Запиши текст в Notepad, промени го и го запиши пак; `backup` показва и двата; `backup get` на по-стария го връща.
- [ ] **Q3.** От Windows (флашката с `WriteProtect` = 1): `python tools\table_copy.py check \\.\PhysicalDriveN` ->
  `they are the same`.

---

## Какво да ми пратиш

1. Кои тестове са `[!]` и точния текст от екрана.
2. Отговорите на E3 (`id pyhello`), F1 (кое от двете) и F3 (разлики в Calc).
3. Ако е ползван резервен билд от част C - кой от четирите е тръгнал.
