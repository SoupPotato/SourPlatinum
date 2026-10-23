# Parses scrcmd.inc / movement.inc macro definitions and the opcode table for scrdis.py.
import re,os
def parse_macros(path):
    txt=open(path).read(); M={}
    for m in re.finditer(r'^\s*\.macro\s+(\w+)([^\n]*)\n(.*?)^\s*\.endm', txt, re.S|re.M):
        name=m.group(1); params=[p.strip() for p in m.group(2).split(',') if p.strip()]
        params=[p.split('=')[0].strip().split(':')[0] for p in params]
        body=[l.strip() for l in m.group(3).split('\n') if l.strip() and not l.strip().startswith('//')]
        M[name]=(params,body)
    return M
def opcodes(path, prefix='SCRCMD_'):
    return [m for m in re.findall(r'ScriptCommand\((\w+)', open(path).read())]
def primitives(macros, ops):
    opidx={o:i for i,o in enumerate(ops)}; prim={}; complex_=[]
    for name,(params,body) in macros.items():
        if not body: continue
        m=re.match(r'\.short\s+(\w+)$', re.sub(r'/\*.*?\*/|//.*','',body[0]).strip())
        if not m or m.group(1) not in opidx: continue
        op=opidx[m.group(1)]; fields=[]; ok=True
        for l in body[1:]:
            l=re.sub(r'/\*.*?\*/|//.*','',l).strip()
            mm=re.match(r'\.(byte|short|long)\s+\\(\w+)(\s*-\s*\.\s*-\s*4)?$', l)
            cc=re.match(r'\.(byte|short|long)\s+(-?\d+|0x[0-9a-fA-F]+)\s*(//.*)?$', l)
            if mm and mm.group(2) in params:
                fields.append((mm.group(1), mm.group(2), bool(mm.group(3))))
            elif cc: fields.append((cc.group(1), None, False))   # constant field, e.g. Warp's unused short
            else: ok=False; break
        if ok:
            # prefer the macro named closest to the opcode (first seen otherwise)
            if op not in prim: prim[op]=(name,params,fields)
        else: complex_.append((name,m.group(1)))
    return prim, complex_
