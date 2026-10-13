# Dump NARC members from a ROM: extract.py ROM OUTDIR path/in/rom.narc ... -> OUTDIR/<path__with__underscores>/<index>.bin
# dump selected NARCs from a ROM into dir/<narcname>/<idx>.bin
import sys, os, ndspy.rom, ndspy.narc
rom=ndspy.rom.NintendoDSRom.fromFile(sys.argv[1]); out=sys.argv[2]
for path in sys.argv[3:]:
    d=rom.getFileByName(path); n=ndspy.narc.NARC(d)
    od=os.path.join(out,path.replace('/','__')); os.makedirs(od,exist_ok=True)
    for i,f in enumerate(n.files): open(f'{od}/{i}.bin','wb').write(f)
