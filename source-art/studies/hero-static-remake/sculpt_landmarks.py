"""Original landmark-directed facial surface; NOT a model imported from a concept.
The 2-D control net is mapped into depth, with anatomical eye apertures and a
closed cranial rear. This feasibility study is not retopologized game topology.
"""
from pathlib import Path
import numpy as np
from scipy.interpolate import RBFInterpolator, PchipInterpolator
from scipy.spatial import Delaunay
P=Path(__file__).parent
# z, half width, side depth, center-to-side frontal depth landmarks
rows=[
(.0,.18,-.49,[(0,-.69),(.12,-.65)]),
(.10,.41,-.32,[(0,-.83),(.25,-.73)]),
(.23,.60,-.13,[(0,-.87),(.2,-.85),(.4,-.70)]),
(.38,.74,0,[(0,-.80),(.2,-.79),(.4,-.67),(.6,-.42)]),
(.50,.79,.035,[(0,-.81),(.18,-.83),(.35,-.73),(.57,-.48)]),
(.59,.81,.05,[(0,-.95),(.13,-.94),(.26,-.84),(.37,-.72),(.58,-.51)]),
(.65,.82,.055,[(0,-.94),(.1,-.96),(.24,-.87),(.34,-.74),(.57,-.53)]),
(.69,.825,.055,[(0,-.915),(.10,-.92),(.22,-.85),(.34,-.74),(.57,-.54)]),
(.735,.83,.06,[(0,-.92),(.10,-.97),(.23,-.85),(.34,-.73),(.57,-.55)]),
(.79,.84,.06,[(0,-.84),(.1,-.88),(.22,-.81),(.39,-.72),(.60,-.56)]),
(.87,.85,.06,[(0,-.90),(.11,-.86),(.22,-.86),(.36,-.76),(.60,-.59),(.78,-.26)]),
(.95,.87,.065,[(0,-1.20),(.08,-1.25),(.16,-1.14),(.22,-1.09),(.29,-.88),(.42,-.81),(.63,-.72),(.8,-.32)]),
(1.035,.89,.07,[(0,-1.38),(.09,-1.36),(.17,-1.21),(.23,-1.14),(.30,-.88),(.44,-.85),(.62,-.84),(.80,-.40)]),
(1.14,.92,.08,[(0,-1.32),(.11,-1.24),(.20,-.97),(.29,-.84),(.44,-.86),(.64,-.88),(.82,-.43)]),
(1.26,.96,.09,[(0,-1.22),(.11,-1.12),(.20,-.89),(.31,-.80),(.47,-.83),(.66,-.85),(.84,-.44)]),
(1.36,.97,.10,[(0,-1.13),(.11,-1.08),(.21,-.86),(.36,-.78),(.55,-.81),(.72,-.69),(.88,-.33)]),
(1.51,.96,.11,[(0,-1.04),(.10,-1.00),(.15,-.91),(.73,-.65),(.86,-.35)]),
(1.67,.945,.13,[(0,-.94),(.13,-.91),(.29,-.96),(.48,-.94),(.64,-.79),(.80,-.47)]),
(1.78,.94,.14,[(0,-.88),(.2,-.87),(.4,-.86),(.6,-.75),(.80,-.40)]),
(1.95,.945,.15,[(0,-.88),(.20,-.87),(.40,-.83),(.60,-.71),(.80,-.40)]),
(2.15,.925,.16,[(0,-.85),(.2,-.84),(.4,-.78),(.6,-.65),(.80,-.34)]),
(2.35,.86,.17,[(0,-.74),(.2,-.71),(.4,-.63),(.6,-.46),(.78,-.13)]),
(2.52,.72,.18,[(0,-.57),(.2,-.52),(.4,-.39),(.6,-.14)]),
(2.67,.48,.19,[(0,-.32),(.2,-.25),(.4,-.05)]),
(2.77,.16,.20,[(0,.03),(.1,.08)]),
(2.80,.01,.20,[(0,.19)])]
zr=np.array([r[0] for r in rows]); wr=np.array([r[1] for r in rows]); yr=np.array([r[2] for r in rows])
width=PchipInterpolator(zr,wr); side=PchipInterpolator(zr,yr)
ctrl=[]; vals=[]
def add(x,z,y):ctrl.append((x,z)); vals.append(y)
for z,w,y,cs in rows:
 for x,dep in cs:
  for s in ([1] if x==0 else [-1,1]):add(s*x,z,dep)
 add(-w,z,y);add(w,z,y)
# Anatomical inner lid boundary; full continuous skin surrounding true openings.
def eye_boundary(s=1,n=70):
 p=[]
 for a in np.linspace(0,2*np.pi,n,endpoint=False):
  u=(1-np.cos(a))/2;x=.195+.445*u
  z=1.505+.016*u+(.078 if a<np.pi else .051)*np.sin(a)
  xx=x-.414;zz=z-1.521
  y=-.675-np.sqrt(max(.001,.247**2-xx*xx-zz*zz))-.006
  p.append((s*x,z,y))
 return p
for s in [-1,1]:
 for x,z,y in eye_boundary(s):add(x,z,y)
 # Thin outer edge / upper lid crease. Controls are skin, not detached tubes.
 for u in np.linspace(.06,.94,20):
  x=.195+.445*u;z=1.505+.016*u+.078*np.sin(np.pi*u)
  zz=z+.034; yy=-.675-np.sqrt(max(.001,.247**2-(x-.414)**2-(z-1.521)**2))+.003
  add(s*x,zz,yy)
  add(s*x,zz+.035,yy+.024)
 # small alar notches (nostril apertures remain shadow inserts)
 add(s*.145,.925,-1.08);add(s*.23,.947,-1.08)
# unique controls to avoid degenerate RBF system
cd={tuple(np.round(p,7)):v for p,v in zip(ctrl,vals)}
ctrl=np.array(list(cd)); vals=np.array(list(cd.values()))
rbf=RBFInterpolator(ctrl,vals,kernel='thin_plate_spline',smoothing=.00006)
# Regular triangular skin with exact face/eye borders, no assembled cheek spheres.
points=[]
zs=np.linspace(0,2.8,241)
for z in zs:
 w=float(width(z))
 for x in np.linspace(-w,w,max(4,int(w*190))):
  points.append((x,z))
# Remove points inside eye opening or too close to exact border.
def ineye(x,z,pad=0):
 x=abs(x);u=(x-.195)/.445
 if not 0<u<1:return False
 mid=1.505+.016*u
 return mid-(.051+pad)*np.sin(np.pi*u)-pad < z < mid+(.078+pad)*np.sin(np.pi*u)+pad
points=[p for p in points if not ineye(*p,.010)]
for s in [-1,1]:points.extend([(x,z) for x,z,y in eye_boundary(s,96)])
# Explicit exact boundary used for rear closure.
left=[];right=[]
for z in zs:
 left.append((-float(width(z)),z));right.append((float(width(z)),z))
points.extend(left+right)
points=np.unique(np.round(points,8),axis=0)
depths=rbf(points);verts=np.column_stack((points[:,0],depths,points[:,1]))
d=Delaunay(points);faces=[]
for tri in d.simplices:
 c=points[tri].mean(axis=0)
 if abs(c[0])>width(c[1])+.0001 or ineye(*c):continue
 faces.append(tri.tolist())
# Close rear using same side boundary vertices. Vertex lookup exact to 8 decimals.
lookup={tuple(p):i for i,p in enumerate(points)}
verts=verts.tolist();rows_i=[]
for z in zs:
 w=float(width(z));sy=float(side(z));row=[]
 for j,a in enumerate(np.linspace(0,np.pi,65)):
  x=-w*np.cos(a)
  if j==0:idx=lookup[tuple(np.round((-w,z),8))]
  elif j==64:idx=lookup[tuple(np.round((w,z),8))]
  else:
   idx=len(verts);deep=(.36+.77*np.sin(np.pi*z/2.8)**.63)
   verts.append((x,sy+deep*np.sin(a),z))
  row.append(idx)
 rows_i.append(row)
for r0,r1 in zip(rows_i,rows_i[1:]):
 for a,b,c,d in zip(r0[:-1],r0[1:],r1[1:],r1[:-1]):faces.extend([(a,c,b),(a,d,c)])
verts=np.array(verts);faces=np.array(faces,dtype=np.int32)
# Physical scale: 21 cm head, natural adult proportions. Tilt/pose set in Blender.
np.savez(P/'face_landmark_surface.npz',vertices=verts,faces=faces,control_points=ctrl,control_depth=vals)
print('Landmark facial surface:',verts.shape,faces.shape,'RBF controls:',len(ctrl))
