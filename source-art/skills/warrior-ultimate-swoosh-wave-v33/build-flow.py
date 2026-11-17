"""Deterministic tiling air-flow texture for the new code-native swoosh material."""
from pathlib import Path
from math import sin, cos, pi
from PIL import Image

base=Path(__file__).resolve().parent
size=256
data=bytearray()
for y in range(size):
 for x in range(size):
  a,b=x/size*2*pi,y/size*2*pi
  channels=[
   .5+.20*sin(3*a+2*b+.65*sin(2*a-b))+.12*cos(7*a-3*b)+.07*sin(11*a+5*b),
   .5+.19*cos(2*a-3*b+.8*sin(a+2*b))+.13*sin(6*a+5*b)+.06*cos(13*a-7*b),
   .5+.22*sin(9*a+2*b+.75*sin(2*a-3*b))+.12*cos(17*a+3*b)
  ]
  data.extend([round(max(0,min(1,c))*255) for c in channels]+[255])
(base/'swoosh-flow.rgba').write_bytes(data)
Image.frombytes('RGBA',(size,size),bytes(data)).save(base/'swoosh-flow.png')
print('Wrote 256x256 periodic flow texture; no model inference.')
