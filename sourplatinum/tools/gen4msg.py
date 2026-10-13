# Gen 4 text bank (de)cryption: raw() -> list of u16 char lists, build() re-encrypts, fix_dup() repairs the
# "FFFE FF00 FF00" control-code artifact written by the original hack tool.
import struct
def raw(data):
    n,seed=struct.unpack_from('<HH',data,0); out=[]
    for i in range(n):
        k=(seed*0x2FD*(i+1))&0xFFFF; k2=k|(k<<16)
        off,ln=struct.unpack_from('<II',data,4+8*i); off^=k2; ln^=k2
        key=(0x91BD3*(i+1))&0xFFFF; cs=[]
        for j in range(ln):
            c=struct.unpack_from('<H',data,off+2*j)[0]^key; key=(key+0x493D)&0xFFFF; cs.append(c)
        out.append(cs)
    return out
def build(strings, seed):
    n=len(strings); hdr=bytearray(struct.pack('<HH',n,seed)); body=bytearray()
    off=4+8*n
    for i,cs in enumerate(strings):
        k=(seed*0x2FD*(i+1))&0xFFFF; k2=k|(k<<16)
        hdr+=struct.pack('<II',(off+len(body))^k2,len(cs)^k2)
        key=(0x91BD3*(i+1))&0xFFFF
        for c in cs: body+=struct.pack('<H',c^key); key=(key+0x493D)&0xFFFF
    return bytes(hdr+body)
def seed(data): return struct.unpack_from('<H',data,2)[0]
def fix_dup(cs):
    # repair "FFFE FF00 FF00 nparams" artifact -> "FFFE FF00 nparams"
    out=[];i=0;fixed=0
    while i<len(cs):
        if cs[i]==0xFFFE and i+2<len(cs) and cs[i+1]==cs[i+2] and cs[i+1]>=0xFF00:
            out+= [cs[i],cs[i+1]]; i+=3; fixed+=1
        else: out.append(cs[i]); i+=1
    return out,fixed
