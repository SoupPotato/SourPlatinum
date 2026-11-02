# Field-script support for dspre_writeback.py: patch res/field/scripts/<file>.s so it assembles to what DSPRE saved.
#
# DSPRE recompiles a whole script file, so its layout never matches the build's. Starting from each ScriptEntry, the
# straight-line runs of the baseline and DSPRE binaries are aligned with a sequence diff, which pairs up their
# instructions (and, through matching jumps, the code they lead to) even around inserted or removed instructions.
# Only source blocks (label to next label) that hold a changed instruction are rewritten, with primitive macros from
# scrdis and the file's own label, message, flag, var and local-ID names; code DSPRE added gets new
# <Prefix>_DSPRE_<addr> labels at the end of the file. The patched file is then assembled and checked to behave the
# same as DSPRE's binary before anything is written.
import difflib, os, re, subprocess, tempfile

STOP_NAMES = {'End', 'GoTo', 'Return', 'ReturnCommonScript'}
LOCALID_PLAYER = 0xFF   # include/constants/scrcmd.h

class Unsupported(Exception):
    pass

class Names:
    """How one source file spells message IDs, local IDs, vars and flags."""
    def __init__(self, patcher, text):
        self.text = text
        bank = re.search(r'#include\s+"res/text/bank/(\w+)\.h"', text)
        self.msgs = patcher.scrdis.bank_names(bank.group(1)) if bank else {}
        self.local_ids = {LOCALID_PLAYER: 'LOCALID_PLAYER'}
        ev = re.search(r'#include\s+"(res/field/events/\w+\.h)"', text)
        if ev and os.path.exists(os.path.join(patcher.clone, 'build', ev.group(1))):
            for n, v in re.findall(r'#define\s+(LOCALID_\w+)\s+(\d+)', open(os.path.join(patcher.clone, 'build', ev.group(1))).read()):
                self.local_ids.setdefault(int(v), n)

class ScriptPatcher:
    def __init__(self, clone):
        self.clone = clone
        os.environ['REPO'] = clone   # scrdis reads the macros and generated headers of a built tree
        import scrdis
        self.scrdis = scrdis
        # every name a var/flag value has (VAR_RESULT and VAR_0x800C are the same var), to prefer the file's own
        self.aliases = {}
        for f in (os.path.join(clone, 'include', 'constants', 'savedata', 'vars_flags.h'),
                  os.path.join(clone, 'build', 'generated', 'vars_flags.h')):
            if os.path.exists(f):
                for n, v in re.findall(r'^#define\s+((?:VAR|FLAG)_\w+)\s+\(?\s*(0x[0-9A-Fa-f]+|\d+)\s*\)?\s*$', open(f).read(), re.M):
                    self.aliases.setdefault((n[:4], int(v, 0)), []).append(n)

    # --- assembling, the same way tools/scripts/make_script_bin.sh does --------------------------------------------

    def assemble(self, text):
        """(binary, {offset: [label names]}) for a script source."""
        build = os.path.join(self.clone, 'build')
        with tempfile.TemporaryDirectory() as tmp:
            src, obj, out = (os.path.join(tmp, n) for n in ('script.s', 'script.o', 'script.bin'))
            open(src, 'w', encoding='utf-8', newline='\n').write(text)
            pp = subprocess.run(['arm-none-eabi-gcc', '-E', '-x', 'assembler-with-cpp', '-I../include', '-I../asm', '-I.', src],
                                cwd=build, capture_output=True, text=True)
            if pp.returncode:
                raise Unsupported(pp.stderr.strip()[:400])
            en = subprocess.run([os.path.join(build, 'tools', 'enumproc', 'enumproc')], input=pp.stdout, cwd=build,
                                capture_output=True, text=True)
            asm = subprocess.run(['arm-none-eabi-gcc', '-x', 'assembler-with-cpp', '-o', obj, '-c', '-'], input=en.stdout,
                                 cwd=build, capture_output=True, text=True)
            if en.returncode or asm.returncode:
                raise Unsupported((en.stderr + asm.stderr).strip()[:400])
            subprocess.run(['arm-none-eabi-objcopy', '-O', 'binary', '--file-alignment', '4', obj, out], check=True)
            labels = {}
            for line in subprocess.run(['arm-none-eabi-nm', obj], capture_output=True, text=True, check=True).stdout.splitlines():
                m = re.match(r'([0-9a-fA-F]+)\s+[tTdD]\s+(\w+)$', line)
                if m:
                    labels.setdefault(int(m.group(1), 16), []).append(m.group(2))
            return open(out, 'rb').read(), labels

    @staticmethod
    def canon(script, entry):
        """Layout-independent form of everything reachable from an entry. Falling through and GoTo both just continue
        the run, so moving code around (which DSPRE always does) doesn't change it; jump targets are numbered in
        visit order."""
        ids, queue, out = {}, [], []
        def lab(t):
            if t not in ids:
                ids[t] = len(ids); queue.append(t)
            return ids[t]
        lab(entry)
        while queue:
            a = start = queue.pop(0)
            if a in script.mov:
                out.append((ids[a], 'MOV', tuple(script.mov[a][0]))); continue
            run, seen = [], {}
            while a in script.code:
                if a in seen:
                    run.append(('LOOP', seen[a])); break
                seen[a] = len(run)
                name, args, nxt = script.code[a]
                if name == 'GoTo':
                    a = args[0][1]; continue
                run.append((name, tuple(('L', lab(x[1])) if x[0] == 'label' else (x[0], x[1]) for x in args)))
                if name in STOP_NAMES:
                    break
                a = nxt
            out.append((ids[start], 'RUN', tuple(run)))
        return out

    # --- emitting --------------------------------------------------------------------------------------------------

    def fmt(self, pn, v, names):
        if pn.lower() in ('localid', 'objectid') and v in names.local_ids:
            return names.local_ids[v]
        out = self.scrdis.fmtarg(pn, v, names.msgs)
        for prefix in ('VAR_', 'FLAG'):
            if out.startswith(prefix):
                for alias in self.aliases.get((prefix[:4], v), []):
                    if re.search(rf'\b{alias}\b', names.text):
                        return alias
        return out

    def instruction(self, script, a, label_for, names):
        """Macro call for the instruction at a, arguments in the macro's parameter order (a field can repeat one)."""
        name, args, _ = script.code[a]
        params = self.scrdis.PRIM[int.from_bytes(script.d[a:a + 2], 'little')][1]
        values = {}
        for x in args:
            if x[0] == 'label':
                values.setdefault(x[2], label_for(x[1]))
            else:
                values.setdefault(x[0], self.fmt(x[0], x[1], names))
        used = [p for p in params if p in values]
        if used != params[:len(used)]:
            raise Unsupported(f'{name} has parameters that aren\'t stored in the script')
        return name + (' ' + ', '.join(values[p] for p in used) if used else '')

    def compound_macros(self):
        """Two-line macros such as GoToIfEq (CompareVar + GoToIf 1), as (name, params, [(call, args), (call, args)])."""
        if not hasattr(self, '_compound'):
            self._compound = []
            for name, (params, body) in self.scrdis.MAC.items():
                calls = [re.match(r'(\w+)\s*(.*)$', l) for l in body]
                if len(body) != 2 or not params or not all(calls):
                    continue
                calls = [(m.group(1), [a.strip() for a in m.group(2).split(',')] if m.group(2).strip() else []) for m in calls]
                if all(any(a == '\\' + p for _, args in calls for a in args) for p in params):
                    self._compound.append((name, params, calls))
        return self._compound

    def sugar(self, lines, names):
        """Fold primitive pairs back into the compound macros the source uses (CompareVarToValue + GoToIf 1 -> GoToIfEq)."""
        alias = {'CompareVar': ('CompareVarToValue', 'CompareVarToVar')}
        parse = lambda l: (l.split()[0], [a.strip() for a in l.strip()[len(l.split()[0]):].split(',')] if len(l.split()) > 1 else [])
        out, i = [], 0
        while i < len(lines):
            match = None
            if i + 1 < len(lines):
                pair = (parse(lines[i]), parse(lines[i + 1]))
                options = []
                for name, params, calls in self.compound_macros():
                    bind = {}
                    ok = all(cn == en or en in alias.get(cn, ()) for (cn, _), (en, _) in zip(calls, pair)) and \
                        all(len(ca) == len(ea) for (_, ca), (_, ea) in zip(calls, pair))
                    for (_, ca), (_, ea) in zip(calls, pair) if ok else ():
                        for c, e in zip(ca, ea):
                            if c.startswith('\\'):
                                ok = ok and bind.setdefault(c[1:], e) == e
                            else:
                                ok = ok and c == e
                    if ok and all(p in bind for p in params):
                        options.append((not re.search(rf'\b{name}\b', names.text), f'    {name} ' + ', '.join(bind[p] for p in params)))
                match = min(options)[1] if options else None
            if match:
                out.append(match); i += 2
            else:
                out.append(lines[i]); i += 1
        return out

    def movement_lines(self, actions):
        out = []
        for act, n in actions:
            an = self.scrdis.MOVACT.get(act, str(act))
            mn = self.scrdis.MOVNAME.get(an, (None, None))[0]
            if mn is None:
                out.append(f'    .short {an}, {n}')
            elif self.scrdis.MOV[mn][0]:   # macros like WalkNormalNorth take a length (default 1); EndMovement doesn't
                out.append(f'    {mn}' + (f' {n}' if n != 1 else ''))
            else:
                out.append(f'    {mn}')
        return out

    # --- pairing the baseline and DSPRE binaries ---------------------------------------------------------------------

    @staticmethod
    def run(script, a):
        """Addresses of the code executed from a up to the first End/Return, following GoTo like falling through
        (the GoTos themselves are left out: DSPRE and the source place code differently, so they rarely match)."""
        out, seen = [], set()
        while a in script.code and a not in seen:
            seen.add(a)
            name, args, nxt = script.code[a]
            if name == 'GoTo':
                a = args[0][1]; continue
            out.append(a)
            if name in STOP_NAMES:
                break
            a = nxt
        return out

    @staticmethod
    def target(script, a):
        """Where a jump to a really goes, skipping GoTo chains."""
        seen = set()
        while a in script.code and script.code[a][0] == 'GoTo' and a not in seen:
            seen.add(a); a = script.code[a][1][0][1]
        return a

    @staticmethod
    def shape(script, a):
        name, args, _ = script.code[a]
        return (name,) + tuple(('L', x[2]) if x[0] == 'label' else (x[0], x[1]) for x in args)

    @staticmethod
    def kind(script, a):
        name, args, _ = script.code[a]
        return (name,) + tuple('L' if x[0] == 'label' else x[0] for x in args)

    def pair_up(self, old, new):
        """(pair: new addr -> old addr, changed: old addrs, start_for_old: old addr -> new addr to emit from)."""
        pair, changed, start_for_old, done = {}, set(), {}, set()
        work = list(zip(new.entries, old.entries))

        def link(na, oa):
            if pair.setdefault(na, oa) != oa:
                changed.add(oa)   # the same DSPRE code stands in for two different source spots
                return
            start_for_old.setdefault(oa, na)
            for x, y in zip(new.code[na][1], old.code[oa][1]):
                if x[0] == 'label':
                    work.append((x[1], y[1]))

        while work:
            na, oa = work.pop()
            if (na, oa) in done:
                continue
            done.add((na, oa))
            if na in new.mov or oa in old.mov:
                if na in new.mov and oa in old.mov:
                    pair.setdefault(na, oa); start_for_old.setdefault(oa, na)
                    if new.mov[na][0] != old.mov[oa][0]:
                        changed.add(oa)
                else:
                    changed.add(oa)
                continue
            rn, ro = self.run(new, na), self.run(old, oa)
            if not rn or not ro:
                changed.add(oa); continue
            start_for_old.setdefault(oa, rn[0])
            ops = difflib.SequenceMatcher(None, [self.shape(old, a) for a in ro], [self.shape(new, a) for a in rn],
                                          autojunk=False).get_opcodes()
            for tag, i1, i2, j1, j2 in ops:
                if tag == 'equal':
                    for k in range(i2 - i1):
                        link(rn[j1 + k], ro[i1 + k])
                    continue
                changed.update(ro[i1:i2])
                if i1 < len(ro) and j1 < len(rn):
                    start_for_old.setdefault(ro[i1], rn[j1])   # an insertion goes in front of the instruction it precedes
                if i1 == i2:
                    changed.add(ro[i1] if i1 < len(ro) else ro[-1])
                for k in range(min(i2 - i1, j2 - j1)):
                    if self.kind(old, ro[i1 + k]) == self.kind(new, rn[j1 + k]):
                        link(rn[j1 + k], ro[i1 + k])
        # an instruction whose jump now lands somewhere else (or on new code) has changed too
        for na, oa in pair.items():
            if na in new.code:
                for x, y in zip(new.code[na][1], old.code[oa][1]):
                    if x[0] == 'label' and pair.get(self.target(new, x[1])) != self.target(old, y[1]):
                        changed.add(oa)
        return pair, changed, start_for_old

    # --- the patch ---------------------------------------------------------------------------------------------------

    def patch(self, text, old_bin, new_bin, sugar=True):
        """The source text, changed so it assembles to new_bin's behaviour. Raises Unsupported if it can't."""
        Script = self.scrdis.Script
        built, labels_at = self.assemble(text)
        if built.rstrip(b'\0') != old_bin.rstrip(b'\0'):
            raise Unsupported('the source no longer assembles to the build DSPRE opened')
        old, new = Script(old_bin), Script(new_bin)
        if len(new.entries) < len(old.entries):
            raise Unsupported('scripts were removed; remove ScriptEntry lines in source instead')
        pair, changed, start_for_old = self.pair_up(old, new)
        if not changed and len(new.entries) == len(old.entries):
            return text

        lines = text.split('\n')
        label_line = {m.group(1): i for i, l in enumerate(lines) for m in [re.match(r'^(\w+):', l)] if m}
        starts = sorted(o for o, ns in labels_at.items() if any(n in label_line for n in ns))
        name_at = {o: next(n for n in labels_at[o] if n in label_line) for o in starts}
        prefix = re.search(r'ScriptEntry\s+([A-Za-z0-9]+)_', text)
        prefix = prefix.group(1) if prefix else 'Script'
        names = Names(self, text)

        new_names, queue = {}, []
        def label_for(nt):
            if nt not in new.mov:
                nt = self.target(new, nt)
            ot = pair.get(nt)
            if ot in name_at:
                return name_at[ot]
            # the source may label a GoTo that leads to this code rather than the code itself
            for o in starts:
                if self.target(old, o) == ot and o in name_at and ot is not None:
                    return name_at[o]
            if ot is not None:
                raise Unsupported(f'DSPRE jumps into the middle of a source block (offset {ot:#x})')
            if nt not in new_names:
                new_names[nt] = f'{prefix}_DSPRE_{nt:04X}'
                queue.append(nt)
            return new_names[nt]

        def emit_code(a, own, next_label_offset):
            """Code from a until it stops or runs into another source block (own: this block's old offset)."""
            out, seen = [], set()
            while True:
                if out and a in pair and pair[a] in name_at and pair[a] != own:
                    if pair[a] != next_label_offset:
                        out.append(f'    GoTo {name_at[pair[a]]}')
                    return self.sugar(out, names) if sugar else out
                if a in seen or a not in new.code:
                    raise Unsupported(f'unexpected control flow at {a:#x} in DSPRE\'s script')
                seen.add(a)
                out.append('    ' + self.instruction(new, a, label_for, names))
                name, _, nxt = new.code[a]
                if name in STOP_NAMES:
                    return self.sugar(out, names) if sugar else out
                a = nxt

        # rewrite changed source blocks in place, keeping the directives (.balign) between blocks
        replacements = []
        for k, s in enumerate(starts):
            e = starts[k + 1] if k + 1 < len(starts) else None
            if not any(s <= c and (e is None or c < e) for c in changed):
                continue
            ns = start_for_old.get(s)
            if ns is None:
                raise Unsupported(f'{name_at[s]} changed in a way that can\'t be traced back to the source')
            body = self.movement_lines(new.mov[ns][0]) if ns in new.mov else emit_code(ns, s, e)
            first = label_line[name_at[s]] + 1
            last = label_line[name_at[e]] if e is not None else len(lines)
            while last > first and (lines[last - 1].strip() == '' or lines[last - 1].strip().startswith(('.', '//'))):
                last -= 1
            replacements.append((first, last, body))

        # new scripts, then everything DSPRE added that the source has no label for
        extra_entries = []
        for k in range(len(old.entries), len(new.entries)):
            nt = new.entries[k]
            if new_names.get(nt) is None:
                new_names[nt] = f'{prefix}_DSPRE_Script{k + 1}'; queue.append(nt)
            extra_entries.append(f'    ScriptEntry {new_names[nt]}')
        appended = []
        while queue:
            nt = queue.pop(0)
            if nt in new.mov:
                appended += ['', '    .balign 4, 0', f'{new_names[nt]}:'] + self.movement_lines(new.mov[nt][0])
            else:
                appended += ['', f'{new_names[nt]}:'] + emit_code(nt, None, None)

        for first, last, body in sorted(replacements, reverse=True):
            lines[first:last] = body
        if extra_entries:
            end = next((i for i, l in enumerate(lines) if l.strip() == 'ScriptEntryEnd'), None)
            if end is None:   # some files have no ScriptEntryEnd; their entry list ends at the first blank line after it
                last_entry = max(i for i, l in enumerate(lines) if l.strip().startswith('ScriptEntry '))
                end = last_entry + 1
            lines[end:end] = extra_entries
        if appended:
            while lines and lines[-1] == '':
                lines.pop()
            lines += appended + ['']
        patched = '\n'.join(lines)

        try:
            rebuilt, _ = self.assemble(patched)
            rebuilt = Script(rebuilt)
            if len(rebuilt.entries) != len(new.entries):
                raise Unsupported('the patched source has a different number of scripts than DSPRE\'s')
            for k in range(len(new.entries)):
                if self.canon(rebuilt, rebuilt.entries[k]) != self.canon(new, new.entries[k]):
                    raise Unsupported(f'the patched source doesn\'t match DSPRE\'s script {k + 1}; edit it in source instead')
        except Unsupported:
            if sugar:   # a folded macro can pick a different primitive (CompareVar's var/value check); try without
                return self.patch(text, old_bin, new_bin, sugar=False)
            raise
        return patched
