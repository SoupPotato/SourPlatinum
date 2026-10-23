# Build Sour Platinum for the DSPRE fork (branch sourplatinum-offsets): sync this Windows tree into the WSL build
# clone, run make there, then publish the ROM, a baseline copy and its dspre_offsets.json to build/dspre/.
# Run in WSL from the Windows tree: python3 sourplatinum/tools/dspre_build.py [--clone ~/SourPlatinum] [-j 8]
#
# The sync only copies files whose content differs. CRLF and LF count as equal, and a copied text file keeps the line
# endings of the clone's copy (or its git eol attribute), since some files must stay CRLF (eol=crlf in .gitattributes).
# It never deletes anything in the clone, so a file removed on Windows has to be removed from the clone by hand.
# dspre_writeback.py compares DSPRE's edits against sourplatinum.baseline.nds, so DSPRE must open sourplatinum.nds
# from the same build.
import argparse, os, shutil, subprocess, sys, time

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(TOOLS))
SKIP_DIRS = {'.git', 'build', 'subprojects', '.cache', '__pycache__', '.vscode'}
TEXT_EXTS = {'.c', '.h', '.cpp', '.hpp', '.s', '.inc', '.sh', '.py', '.json', '.txt', '.order', '.md', '.build',
             '.ld', '.lsf', '.yaml', '.yml', '.csv', '.sha1', '.toml', '.ini', '.cfg', '.mk', '.wrap'}
STAMP = 'build/.dspre_sync_stamp'

def crlf_attr(clone, rel):
    out = subprocess.run(['git', 'check-attr', 'eol', '--', rel], cwd=clone, capture_output=True, text=True).stdout
    return out.strip().endswith(': crlf')

def sync(clone, full):
    stamp_path = os.path.join(clone, STAMP)
    since = 0 if full or not os.path.exists(stamp_path) else os.path.getmtime(stamp_path) - 2
    started = time.time()
    copied = []
    for d, dirs, files in os.walk(REPO):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not (d == REPO and x.startswith('.'))]
        for f in files:
            src = os.path.join(d, f)
            rel = os.path.relpath(src, REPO)
            dst = os.path.join(clone, rel)
            if os.path.getmtime(src) < since and os.path.exists(dst):
                continue
            data = open(src, 'rb').read()
            old = open(dst, 'rb').read() if os.path.exists(dst) else None
            if os.path.splitext(f)[1].lower() in TEXT_EXTS or f in ('Makefile',):
                # line endings are the checkout's business (some files are eol=crlf), so compare and write content only
                data = data.replace(b'\r\n', b'\n')
                if old is not None and old.replace(b'\r\n', b'\n') == data:
                    continue
                crlf = b'\r\n' in old if old is not None else crlf_attr(clone, rel)
                if crlf:
                    data = data.replace(b'\n', b'\r\n')
            if old == data:
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, 'wb') as out:
                out.write(data)
            copied.append(rel)
    os.makedirs(os.path.dirname(stamp_path), exist_ok=True)
    with open(stamp_path, 'w') as s:
        s.write('%f\n' % started)
    os.utime(stamp_path, (started, started))
    return copied

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--clone', default='~/SourPlatinum', help='WSL build clone (default ~/SourPlatinum)')
    ap.add_argument('-j', '--jobs', type=int, default=os.cpu_count() or 4)
    ap.add_argument('--full-sync', action='store_true', help='compare every file, not only ones changed since the last sync')
    args = ap.parse_args()
    clone = os.path.expanduser(args.clone)
    if os.path.realpath(clone) == os.path.realpath(REPO):
        sys.exit('the clone and this tree are the same folder; run this from the Windows tree')

    copied = sync(clone, args.full_sync)
    print(f'synced {len(copied)} file(s) into {clone}', *('  ' + c for c in copied[:50]), sep='\n')
    if len(copied) > 50:
        print(f'  ... and {len(copied) - 50} more')
    sys.stdout.flush()

    if subprocess.call(['make', f'-j{args.jobs}'], cwd=clone) != 0:
        sys.exit('make failed')

    out_dir = os.path.join(REPO, 'build', 'dspre')
    os.makedirs(out_dir, exist_ok=True)
    rom = os.path.join(out_dir, 'sourplatinum.nds')
    shutil.copyfile(os.path.join(clone, 'build', 'pokeplatinum.us.nds'), rom)
    shutil.copyfile(rom, os.path.join(out_dir, 'sourplatinum.baseline.nds'))
    if subprocess.call([sys.executable, os.path.join(TOOLS, 'dspre_offsets.py'),
                        '--map', os.path.join(clone, 'build', 'main.nef.xMAP'), '--rom', rom], cwd=clone) != 0:
        sys.exit('dspre_offsets.py failed')
    print(f'published {rom}')

if __name__ == '__main__':
    main()
