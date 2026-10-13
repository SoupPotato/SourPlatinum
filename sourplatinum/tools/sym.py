# Resolve addresses to symbols: sym.py build/main.nef.xMAP 0x2086590 ...
import re,sys
syms=[]
for l in open(sys.argv[1],encoding='latin1'):
    m=re.match(r'\s+([0-9A-F]{8}) ([0-9A-F]{8}) (\S+)\s+(\S+)\s+\((.*)\)',l)
    if m and m.group(4) not in ('$d','$t','$a') and not m.group(4).startswith('.'):
        syms.append((int(m.group(1),16),int(m.group(2),16),m.group(3),m.group(4),m.group(5)))
for a in sys.argv[2:]:
    a=int(a,16)
    c=[s for s in syms if s[0]<=a<s[0]+max(s[1],1)]
    print(hex(a), [(hex(s[0]),hex(s[1]),s[2],s[3],s[4]) for s in c])
