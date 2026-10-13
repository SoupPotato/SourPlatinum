# Decodes a zone_event.narc member (bg/object/warp/coord events) into dicts.
import struct
def dec(b):
    o=0
    def cnt():
        nonlocal o; n=struct.unpack_from('<I',b,o)[0]; o+=4; return n
    out={}
    n=cnt(); out['bg']=[]
    for _ in range(n):
        s,t,x,z,y,d=struct.unpack_from('<HHiiiH',b,o); o+=20; out['bg'].append(dict(script=s,type=t,x=x,z=z,y=y,dir=d))
    n=cnt(); out['obj']=[]
    for _ in range(n):
        v=struct.unpack_from('<14Hi',b,o); o+=32; out['obj'].append(v)
    n=cnt(); out['warp']=[]
    for _ in range(n):
        v=struct.unpack_from('<4H',b,o); o+=12; out['warp'].append(v)
    n=cnt(); out['coord']=[]
    for _ in range(n):
        v=struct.unpack_from('<8H',b,o); o+=16; out['coord'].append(v)
    out['tail']=b[o:]
    return out
