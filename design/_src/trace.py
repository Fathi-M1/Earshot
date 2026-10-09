import numpy as np, potrace, json
from PIL import Image, ImageFilter
from scipy import ndimage
a=np.array(Image.open('flat.png').convert('RGBA')).astype(float)
r,g,b,al=[a[...,i] for i in range(4)]
opaque=al>128
beige=opaque&(r>150)
green=opaque&(r<120)
S=2
def up(m):
    im=Image.fromarray((m*255).astype(np.uint8)).resize((m.shape[1]*S,m.shape[0]*S),Image.BICUBIC).filter(ImageFilter.GaussianBlur(S*1.0))
    return np.array(im)>127
def tr(m):
    p=potrace.Bitmap(~m).trace(turdsize=300,alphamax=1.33,opticurve=True,opttolerance=1.0)
    d=[]
    for c in p:
        s=c.start_point; d.append(f"M{s.x/S:.1f} {s.y/S:.1f}")
        for seg in c.segments:
            if seg.is_corner: d.append(f"L{seg.c.x/S:.1f} {seg.c.y/S:.1f}L{seg.end_point.x/S:.1f} {seg.end_point.y/S:.1f}")
            else: d.append(f"C{seg.c1.x/S:.1f} {seg.c1.y/S:.1f} {seg.c2.x/S:.1f} {seg.c2.y/S:.1f} {seg.end_point.x/S:.1f} {seg.end_point.y/S:.1f}")
        d.append("Z")
    print([len(c.segments) for c in p]); return "".join(d)
O=up(opaque); G=up(green); B=up(beige)
Bd=ndimage.binary_dilation(B,iterations=3)&O
json.dump({'sil':tr(O),'green':tr(G),'beige':tr(Bd)},open('paths.json','w'))
ys,xs=np.where(opaque); print('bbox',xs.min(),ys.min(),xs.max(),ys.max())
