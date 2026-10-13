# Compare every text bank in two ROMs after decryption (ignores per-bank key differences).
# usage: python3 cmptext.py BUILT.nds TARGET.nds build/res/text/text_banks.order
import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import gen4msg, ndspy.rom, ndspy.narc
a=ndspy.narc.NARC(ndspy.rom.NintendoDSRom.fromFile(sys.argv[1]).getFileByName('msgdata/pl_msg.narc')).files
b=ndspy.narc.NARC(ndspy.rom.NintendoDSRom.fromFile(sys.argv[2]).getFileByName('msgdata/pl_msg.narc')).files
order=open(sys.argv[3]).read().split()
bad=0
for i,n in enumerate(order):
    x=gen4msg.raw(a[i]); y=[gen4msg.fix_dup(s)[0] for s in gen4msg.raw(b[i])]
    if x!=y:
        ks=[k for k in range(max(len(x),len(y))) if k>=len(x) or k>=len(y) or x[k]!=y[k]]
        print('DIFF',i,n,len(x),len(y),len(ks),ks[:8]); bad+=1
print('banks differing',bad)
