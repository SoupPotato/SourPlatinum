# Like romdiff, but ignores NARC padding, NCGR header dims and unused NCLR colours. usage: verify.py BUILT.nds TARGET.nds
import sys, ndspy.rom, ndspy.narc
a=ndspy.rom.NintendoDSRom.fromFile(sys.argv[1]); b=ndspy.rom.NintendoDSRom.fromFile(sys.argv[2])
na={a.filenames.filenameOf(i):i for i in range(len(a.files)) if a.filenames.filenameOf(i)}
def norm(x):
    if x[:4] in (b'RGCN',) and len(x)>0x30: return x[0x30:].rstrip(b'\0')   # ignore NCGR header dims
    if x[:4]==b'RLCN' and len(x)>0x28: return x[0x28:0x48]                    # 4bpp: first 16 colours
    return x.rstrip(b'\0')
for n in sorted(na):
    fa=a.files[na[n]]; fb=b.getFileByName(n)
    if fa==fb: continue
    if fa[:4]==b'NARC':
        A=ndspy.narc.NARC(fa).files; B=ndspy.narc.NARC(fb).files
        ch=[i for i in range(max(len(A),len(B))) if i>=len(A) or i>=len(B) or norm(A[i])!=norm(B[i])]
        if ch: print(n, f'members {len(A)}->{len(B)}', 'differ:', ch[:25], '...' if len(ch)>25 else '')
    else: print(n,'differs (non-NARC)')
