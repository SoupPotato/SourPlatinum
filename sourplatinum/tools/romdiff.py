# Byte-level diff of two ROMs: arm9/overlays and every filesystem file, listing changed NARC members.
# usage: python3 romdiff.py A.nds B.nds
import sys, ndspy.rom, ndspy.narc, ndspy.lz10 as lz
a=ndspy.rom.NintendoDSRom.fromFile(sys.argv[1]); b=ndspy.rom.NintendoDSRom.fromFile(sys.argv[2])
print('arm9', len(a.arm9), len(b.arm9), a.arm9==b.arm9)
print('arm7', a.arm7==b.arm7, 'ov9tbl', a.arm9OverlayTable==b.arm9OverlayTable)
oa=a.loadArm9Overlays(); ob=b.loadArm9Overlays()
for i in sorted(set(oa)|set(ob)):
    x=oa.get(i); y=ob.get(i)
    if x is None or y is None or x.data!=y.data or x.ramAddress!=y.ramAddress or x.ramSize!=y.ramSize or x.bssSize!=y.bssSize:
        print('overlay',i, x and len(x.data), y and len(y.data), x and hex(x.ramAddress), y and hex(y.ramAddress))
na={a.filenames.filenameOf(i):i for i in range(len(a.files)) if a.filenames.filenameOf(i)}
nb={b.filenames.filenameOf(i):i for i in range(len(b.files)) if b.filenames.filenameOf(i)}
print('files only in A', sorted(set(na)-set(nb))); print('files only in B', sorted(set(nb)-set(na)))
for n in sorted(set(na)&set(nb)):
    fa=a.files[na[n]]; fb=b.files[nb[n]]
    if fa==fb: continue
    msg=f'{n}: {len(fa)} -> {len(fb)}'
    if fa[:4]==b'NARC' and fb[:4]==b'NARC':
        A=ndspy.narc.NARC(fa).files; B=ndspy.narc.NARC(fb).files
        ch=[i for i in range(max(len(A),len(B))) if i>=len(A) or i>=len(B) or A[i]!=B[i]]
        msg+=f'  members {len(A)}->{len(B)} changed {len(ch)}: {ch[:40]}{"..." if len(ch)>40 else ""}'
    print(msg)
