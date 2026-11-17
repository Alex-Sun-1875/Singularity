"""Measure actual front-ring core colours; all screenshots remain unmodified."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]

def ring_colors(path,cx,cy,rx,ry):
 im=np.asarray(Image.open(path).convert('RGB'),dtype=float);samples=[]
 for deg in [15,25,35,45,55,125,135,145,155,165]:
  theta=np.deg2rad(deg);points=[]
  for rad in np.linspace(.91,1.055,81):
   x=round(cx+rx*np.cos(theta)*rad);y=round(cy+ry*np.sin(theta)*rad)
   p=im[y,x]
   if p[0]>180 and p[0]-p[2]>55 and p[1]>100:points.append(p)
  if points:
   points=np.asarray(points);samples.append(points[np.argmax(points[:,1])].tolist())
 if len(samples)<8:raise ValueError('Could not find front ring '+str(path))
 return {'count':len(samples),'medianRGB':np.median(samples,axis=0).tolist(),'meanRGB':np.mean(samples,axis=0).tolist(),'samplesRGB':samples}

if __name__=='__main__':
 ref=ring_colors(ROOT/'source-art/skills/fire-selected-reference-v18/user-selected-effect.jpg',497.5,425.5,55.5,26.5)
 before=ring_colors(ROOT/'src/.tmp/fire-seal-original-pixels-v25/036.jpg',554.6,1139,89,53)
 after=ring_colors(ROOT/'src/.tmp/fire-reference-colour-v26/036.jpg',554.6,1139,89,53)
 out={'method':'ten front outer-ring directions, local core peak sampled from original/native unedited RGB screenshots; original and native keep their own ground projection','reference':ref,'previousNative':before,'currentNative':after,'previousMedianAbsoluteChannelDifference':float(np.abs(np.asarray(ref['medianRGB'])-before['medianRGB']).mean()),'currentMedianAbsoluteChannelDifference':float(np.abs(np.asarray(ref['medianRGB'])-after['medianRGB']).mean()),'limits':'Core sampling only, not a claim that different ground colours or every moving flame pixel are identical.'}
 (HERE/'colour-review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
