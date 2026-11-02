# Field script disassembler driven by asm/macros/scrcmd.inc. Needs REPO=<repo root> and a built tree
# (build/generated, build/res/text/bank). Script(bytes).canon(entry) gives a layout-independent form for comparing scripts;
# emit() prints primitive macros. Run with python3 -I and REPO set.
import sys,os,re,struct
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import scrmacros
REPO=os.environ['REPO']
MAC=scrmacros.parse_macros(REPO+'/asm/macros/scrcmd.inc')
OPS=scrmacros.opcodes(REPO+'/include/data/scripts/scrcmd.h')
PRIM,_=scrmacros.primitives(MAC,OPS)
OP={o:i for i,o in enumerate(OPS)}
MOV=scrmacros.parse_macros(REPO+'/asm/macros/movement.inc')
def enumh(p):
    t=open(p).read(); return {int(v,0):n for n,v in re.findall(r'^#define\s+(\w+)\s+(\S+)\s*$',t,re.M) if re.match(r'^-?(0x[0-9a-fA-F]+|\d+)$',v)}
MOVACT=enumh(REPO+'/build/generated/movement_actions.h')
MOVNAME={}
for name,(params,body) in MOV.items():
    if body and re.match(r'\.short\s+MOVEMENT_ACTION_\w+$',body[0]):
        a=body[0].split()[1]; MOVNAME.setdefault(a,(name,len(body)>1))
STOP={OP['SCRCMD_END'],OP['SCRCMD_GOTO'],OP['SCRCMD_RETURN']}
if 'SCRCMD_RETURNCOMMONSCRIPT' in OP: STOP.add(OP['SCRCMD_RETURNCOMMONSCRIPT'])
SZ={'byte':1,'short':2,'long':4}
class Script:
    def __init__(s,data):
        s.d=data; s.entries=[]; o=0
        # the entry table ends with 0xFD13 (ScriptEntryEnd), or without it where the first entry's code starts
        while not (s.entries and o>=min(s.entries)) and struct.unpack_from('<H',data,o)[0]!=0xFD13:
            v=struct.unpack_from('<i',data,o)[0]; s.entries.append(o+4+v); o+=4
        s.hdr_end=o+2 if o<len(data)-1 and struct.unpack_from('<H',data,o)[0]==0xFD13 else o
        s.code={}; s.mov={}; s.labels={}
        work=list(s.entries)
        while work:
            a=work.pop()
            while a not in s.code:
                if a>=len(data): raise Exception(f'ran off end at {a:#x}')
                op=struct.unpack_from('<H',data,a)[0]
                if op not in PRIM: raise Exception(f'no primitive for op {op:#x} ({OPS[op] if op<len(OPS) else "?"}) at {a:#x}')
                name,params,fields=PRIM[op]; p=a+2; args=[]
                for kind,pn,rel in fields:
                    fmt={'byte':'<B','short':'<H','long':'<i' if rel else '<I'}[kind]
                    v=struct.unpack_from(fmt,data,p)
                    v=v[0]
                    if rel:
                        t=p+4+v; args.append(('label',t,pn))
                        if pn=='movementOffset': s.mov[t]=None
                        else: work.append(t)
                        s.labels[t]=None
                    elif pn is not None: args.append((pn,v,kind))
                    p+=SZ[kind]
                s.code[a]=(name,args,p)
                if op in STOP: break
                a=p
        for t in list(s.mov):
            acts=[]; p=t
            while True:
                act,n=struct.unpack_from('<HH',data,p); acts.append((act,n)); p+=4
                if act==254: break
            s.mov[t]=(acts,p)
        for e in s.entries: s.labels[e]=None
    def canon(s, start):
        # canonical form of everything reachable from start (labels renumbered in visit order)
        seen={}; out=[]; work=[start]
        def lab(t):
            if t not in seen: seen[t]=len(seen); work.append(t)
            return seen[t]
        lab(start); work=[start]; done=set()
        while work:
            a=work.pop(0)
            if a in done: continue
            done.add(a); blk=[]
            if a in s.mov: out.append(('MOV',seen[a],tuple(s.mov[a][0]))); continue
            while a in s.code:
                name,args,nxt=s.code[a]
                blk.append((name,tuple(('L',lab(x[1])) if x[0]=='label' else (x[0],x[1]) for x in args)))
                if OP.get('SCRCMD_'+name.upper()) in STOP or name in ('End','GoTo','Return'): break
                if nxt in s.labels and nxt!=a: blk.append(('FALL',lab(nxt))); break
                a=nxt
            out.append(('BLK',seen.get(a,-1),tuple(blk)))
        return out
if __name__=='__main__':
    sc=Script(open(sys.argv[1],'rb').read())
    print('entries',[hex(e) for e in sc.entries],'code instrs',len(sc.code),'mov',len(sc.mov))

VARS={}; FLAGS={}
def _load_varsflags():
    import glob
    for f in [REPO+'/include/constants/savedata/vars_flags.h']+glob.glob(REPO+'/build/generated/vars_flags.h'):
        if not os.path.exists(f): continue
        for n,v in re.findall(r'^#define\s+((?:VAR|FLAG)_\w+)\s+\(?\s*(0x[0-9A-Fa-f]+|\d+)\s*\)?\s*$',open(f).read(),re.M):
            (VARS if n.startswith('VAR_') else FLAGS).setdefault(int(v,0),n)
_load_varsflags()
def bank_names(bank):
    p=REPO+f'/build/res/text/bank/{bank}.h'
    return {int(v):n for n,v in re.findall(r'#define\s+(\w+)\s+(\d+)',open(p).read())} if os.path.exists(p) else {}
ITEMS=enumh(REPO+'/build/generated/items.h'); SPECIES=enumh(REPO+'/build/generated/species.h')
def fmtarg(pn,v,msgs):
    l=pn.lower()
    if 'message' in l and v in msgs: return msgs[v]
    if ('var' in l) and v in VARS and v>=0x4000: return VARS[v]
    if 'flag' in l and v in FLAGS: return FLAGS[v]
    if l in ('item','itemid') and v in ITEMS: return ITEMS[v]
    if 'species' in l and v in SPECIES: return SPECIES[v]
    return str(v)
def emit(sc, starts, names, msgs):
    # emit all code/mov reachable from starts, in address order, with labels from names (addr->label)
    reach=set(); work=list(starts); movs=set()
    while work:
        a=work.pop()
        if a in reach: continue
        if a in sc.mov: movs.add(a); reach.add(a); continue
        while a in sc.code and a not in reach:
            reach.add(a); name,args,nxt=sc.code[a]
            for x in args:
                if x[0]=='label': work.append(x[1])
            if name in ('End','GoTo','Return','ReturnCommonScript'): break
            a=nxt
    lab=lambda t: names.setdefault(t, f'_{t:04X}')
    out=[]
    for a in sorted(reach):
        if a in names or a in sc.labels or a in movs:
            out.append(''); out.append(f'{lab(a)}:')
        if a in movs:
            for act,n in sc.mov[a][0]:
                an=MOVACT.get(act,str(act)); mn,haslen=MOVNAME.get(an,(None,True))
                if mn is None: out.append(f'    .short {an}, {n}')
                elif haslen: out.append(f'    {mn}' + (f' {n}' if n!=1 else ''))
                else: out.append(f'    {mn}')
            continue
        name,args,nxt=sc.code[a]
        _,params,fields=PRIM[struct.unpack_from('<H',sc.d,a)[0]]
        s=[]
        for x in args:
            s.append(lab(x[1]) if x[0]=='label' else fmtarg(x[0],x[1],msgs))
        out.append(f'    {name}' + (' '+', '.join(s) if s else ''))
    return out
