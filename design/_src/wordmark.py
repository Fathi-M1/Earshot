import sys
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.transformPen import TransformPen
NAME=sys.argv[1] if len(sys.argv)>1 else "earshot"
f=TTFont('../earshot-docs/design/fonts/HostGrotesk-VariableFont_wght.ttf')
f=instantiateVariableFont(f,{"wght":500})
gs=f.getGlyphSet(); cmap=f.getBestCmap(); hmtx=f['hmtx']; upm=f['head'].unitsPerEm
track=-0.025*upm
x=0; pen=SVGPathPen(gs); bp=BoundsPen(gs)
for ch in NAME:
    gn=cmap[ord(ch)]
    t=TransformPen(pen,(1,0,0,-1,x,0)); gs[gn].draw(t)
    t2=TransformPen(bp,(1,0,0,-1,x,0)); gs[gn].draw(t2)
    x+=hmtx[gn][0]+track
xmin,ymin,xmax,ymax=bp.bounds
asc=f['OS/2'].sCapHeight; xh=f['OS/2'].sxHeight
import json
json.dump({'d':pen.getCommands(),'bounds':[xmin,ymin,xmax,ymax],'upm':upm,'xh':xh,'cap':asc},open('wordmark.json','w'))
print(NAME,(xmin,ymin,xmax,ymax),upm,xh,asc)
