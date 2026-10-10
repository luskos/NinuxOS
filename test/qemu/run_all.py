#!/usr/bin/env python3
# run_all.py - every test script of test/qemu against the image just built; a line a script.
#
#   python test/qemu/run_all.py [part of a name ...]
#
# For each script: QEMU is driven by tools/qemu/qrun.py, the pictures and the serial log go to
# test/qemu/out_all/NAME/, and the log is read for what must not be there (a fault, a stop of
# the system, a refusal, a wrong seal) and for what must (the system started). The result is
# written to test/qemu/RESULTS.md. Some scripts want an image of their own: a copy of disk.img
# made bigger (the backup pool), with the table wiped (the copy of the table), or built with
# --compare (the old programs compiled by the new py2asm).

import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
OUT = os.path.join(HERE, 'out_all')
BAD = ('fault', 'NinuxOS stopped', 'refused', 'MISMATCH', 'is WRONG', 'not verified', 'read error', 'REFUSED',
       'could not', 'no memory', 'out of memory')
QUIET = {'q_v3_backup_small': ('read error',), 'q_v3_tablecopy': (), 'q_v2959_checks': ('refused',)}


def image(kind):
    base = os.path.join(ROOT, 'disk.img')
    path = os.path.join(OUT, 'img_%s.img' % kind)
    if kind == 'plain':
        return base
    data = bytearray(open(base, 'rb').read())
    if kind == 'big':
        data += bytes(70 * 1024 * 1024 - len(data))
    elif kind == 'notable':
        data[481 * 512:482 * 512] = bytes(512)
    elif kind == 'write':
        pass
    elif kind == 'compare':
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'build_disk.py'), '--compare', '--out', path],
                       capture_output=True, text=True)
        return path
    open(path, 'wb').write(data)
    return path


SPECIAL = {'q_v3_backup': ('big', True), 'q_v3_tablecopy': ('notable', False), 'q_v3_table': ('write', True),
           'q_v3_compare': ('compare', False)}


def main():
    os.makedirs(OUT, exist_ok=True)
    want = sys.argv[1:]
    scripts = sorted(f[:-4] for f in os.listdir(HERE) if f.startswith('q_') and f.endswith('.txt'))
    if want:
        scripts = [s for s in scripts if any(w in s for w in want)]
    rows = []
    for name in scripts:
        kind, write = SPECIAL.get(name, ('plain', False))
        out = os.path.join(OUT, name)
        shutil.rmtree(out, ignore_errors=True)
        cmd = [sys.executable, os.path.join(ROOT, 'tools', 'qemu', 'qrun.py'), os.path.join(HERE, name + '.txt'),
               '--img', image(kind), '--out', out] + (['--write'] if write else [])
        r = subprocess.run(cmd, capture_output=True, text=True)
        log = ''
        if os.path.exists(os.path.join(out, 'serial.log')):
            log = open(os.path.join(out, 'serial.log'), encoding='latin-1').read()
        notes = []
        if '[chain] the system started' not in log:
            notes.append('THE SYSTEM DID NOT START')
        for line in log.split('\n'):
            if any(b in line for b in BAD) and not any(q in line for q in QUIET.get(name, ())):
                notes.append(line.strip()[:150])
        for line in (r.stdout + r.stderr).split('\n'):
            if '!! not in the log' in line:
                notes.append(line.strip())
        seen = []
        for n in notes:
            if n not in seen:
                seen.append(n)
        rows.append((name, seen))
        print('%-22s %s' % (name, 'ok' if not seen else '; '.join(seen)[:400]))
    with open(os.path.join(HERE, 'RESULTS.md'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# What the test scripts said (version %s)\n\n' % open(os.path.join(ROOT, 'VERSION')).read().strip())
        f.write('Made by `python test/qemu/run_all.py`. "ok" means: the system started and the serial log holds no\n'
                'fault, stop, refusal or wrong seal. What the screen showed is in `test/qemu/out_all/NAME/` (not in git).\n\n')
        for name, notes in rows:
            f.write('- **%s**: %s\n' % (name, 'ok' if not notes else '; '.join('`%s`' % n for n in notes)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
