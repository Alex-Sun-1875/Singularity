"""Feather the authored foot of each existing fire card so overlapping cards meet the ground."""
from math import sin
from pathlib import Path
import sys
from PIL import Image


def smooth(value):
    t = min(1.0, max(0.0, value))
    return t*t*(3-2*t)


def feather(src, dst, rows):
    with Image.open(src) as original:
        atlas = original.convert("RGBA")
    alpha = atlas.getchannel("A")
    width, height = atlas.width//4, atlas.height//rows
    for j in range(rows):
        for i in range(4):
            rect = (i*width, j*height, (i+1)*width, (j+1)*height)
            tile = alpha.crop(rect)
            bounds = tile.point(lambda a: 255 if a>12 else 0).getbbox()
            if not bounds:
                continue
            l,top,r,bottom = bounds
            w,h = max(1,r-l), max(1,bottom-top)
            pixels = tile.load()
            for x in range(width):
                u = 2*(x+.5-l)/w-1
                # One convex footprint, with a small coherent ripple along the ember edge.
                # The original vertical plume, hot core and painted colour are preserved.
                floor = bottom - h*(.015+.14*u*u+.018*sin(7*u+j*.3))
                sides = smooth((1.03-abs(u))/(.11 if rows==8 else .05))
                for y in range(height):
                    if pixels[x,y]:
                        foot = smooth((floor-y)/max(3,h*.25))
                        cap = smooth((y-top+2)/max(2,h*.05))
                        pixels[x,y] = round(pixels[x,y]*sides*foot*cap)
            alpha.paste(tile,rect[:2])
    atlas.putalpha(alpha)
    atlas.save(dst,format="PNG")


if __name__=="__main__":
    feather(Path(sys.argv[1]),Path(sys.argv[2]),int(sys.argv[3]))
