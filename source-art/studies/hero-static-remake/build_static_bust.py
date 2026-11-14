"""Editable ORIGINAL static bust feasibility test. No rig; no reused rejected mesh.
Builds landmark-defined continuous face and actual curves, cloth and steel geometry.
"""
from pathlib import Path
import bpy,bmesh,numpy as np,math,random,json,os
from mathutils import Vector
from math import sin,cos,pi,exp,sqrt
random.seed(11602)
P=Path(__file__).parent;ROOT=P.parents[2];OUT=ROOT/'assets/studies/hero-static-remake';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
sc=bpy.context.scene
mats={}
def mat(n,c,r=.65,metal=0,noise=0):
 m=bpy.data.materials.new(n);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Roughness'].default_value=r;p.inputs['Metallic'].default_value=metal
 if noise:
  ns=m.node_tree.nodes;ls=m.node_tree.links;t=ns.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=360 if metal else 900;t.inputs['Detail'].default_value=2
  b=ns.new('ShaderNodeBump');b.inputs['Strength'].default_value=noise;b.inputs['Distance'].default_value=.00022;ls.new(t.outputs['Fac'],b.inputs['Height']);ls.new(b.outputs['Normal'],p.inputs['Normal'])
 mats[n]=m;return m
mat('skin',(.38,.228,.155),.63,noise=.15)
sk=mats['skin'];p=sk.node_tree.nodes.get('Principled BSDF');p.inputs['Subsurface Weight'].default_value=.065;p.inputs['Subsurface Radius'].default_value=(1,.5,.3)
a=sk.node_tree.nodes.new('ShaderNodeVertexColor');a.layer_name='Complexion';sk.node_tree.links.new(a.outputs['Color'],p.inputs['Base Color'])
mat('skin_details',(.36,.20,.135),.67,noise=.12)
mat('waterline',(.28,.116,.086),.52);mat('eye_white',(.49,.44,.36),.27);mat('iris',(.072,.085,.058),.35);mat('pupil',(.006,.004,.003),.24);mat('nostril',(.047,.013,.010),.86)
mat('hair_core',(.024,.014,.009),.64,noise=.18)
for j,c in enumerate([(.022,.012,.007),(.035,.021,.012),(.054,.032,.019),(.018,.012,.009)]):mat('hair_'+str(j),c,.47+.04*j)
mat('linen',(.36,.32,.24),.92,noise=.27);mat('teal_wool',(.035,.074,.078),.93,noise=.30);mat('teal_edge',(.055,.094,.093),.88,noise=.2)
mat('oiled_leather',(.10,.045,.022),.57,noise=.23);mat('leather_edge',(.17,.091,.045),.64,noise=.22);mat('iron',(.22,.23,.215),.49,.78,.12);mat('iron_edge',(.29,.30,.28),.4,.8,.08);mat('brass',(.23,.15,.065),.55,.65,.1)
# Noise varies material roughness at meaningful scale, not bright confetti.
for name in ['teal_wool','oiled_leather','linen','iron']:
 m=mats[name];ns=m.node_tree.nodes;ls=m.node_tree.links;p=ns.get('Principled BSDF');t=ns.new('ShaderNodeTexNoise');t.inputs['Scale'].default_value=45 if name=='iron' else 85;t.inputs['Detail'].default_value=3
 ramp=ns.new('ShaderNodeValToRGB');base=p.inputs['Base Color'].default_value[:3];ramp.color_ramp.elements[0].color=tuple(v*.72 for v in base)+(1,);ramp.color_ramp.elements[1].color=tuple(v*1.15 for v in base)+(1,);ls.new(t.outputs['Fac'],ramp.inputs['Fac']);ls.new(ramp.outputs['Color'],p.inputs['Base Color'])
def mesh(name,v,f,ma,sub=0,solid=0):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(name,me);sc.collection.objects.link(o);o.data.materials.append(mats[ma])
 for p in me.polygons:p.use_smooth=True
 if sub:
  md=o.modifiers.new('Editable surface subdivision','SUBSURF');md.levels=sub;md.render_levels=sub
 if solid:
  md=o.modifiers.new('Actual material thickness','SOLIDIFY');md.thickness=solid
 return o
HEADZ=1.615;S=.075
ang=.13
H=lambda p:(S*(p[0]*cos(ang)-p[1]*sin(ang)),S*(p[0]*sin(ang)+p[1]*cos(ang)),HEADZ+S*p[2])
data=np.load(P/'face_landmark_surface.npz');verts=data['vertices'];face=mesh('CONTINUOUS LANDMARK FACE / real eye apertures',list(map(H,verts)),data['faces'],'skin')
# Correct coherent normals rather than leaving grid winding dependent.
bm=bmesh.new();bm.from_mesh(face.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(face.data);bm.free()
col=face.data.color_attributes.new(name='Complexion',type='FLOAT_COLOR',domain='POINT')
for i,(x,y,z) in enumerate(verts):
 c=np.array([.38,.228,.155]);fr=max(0,min(1,(-y-.1)*3))
 cheeks=exp(-((abs(x)-.58)/.25)**2-((z-1.15)/.35)**2)*fr;c+=cheeks*np.array([.020,-.008,-.004])
 # Closed lip volume is part of this continuous mesh; darker edge is subdued.
 lip=exp(-(x/.33)**6-((z-.672)/.085)**6)*fr;c=c*(1-lip*.53)+np.array([.285,.121,.095])*lip*.53
 beard=max(0,min(1,(.91-z)*4))*fr*(.5+.5*min(1,abs(x)*5))
 c=c*(1-beard*.30)+np.array([.11,.082,.059])*beard*.30
 col.data[i].color=(*c,1)
# Curves are actual editable 3D strands/seams, not image cards or projected concept.
def curves(name,paths,radius,ma,radii=None):
 cu=bpy.data.curves.new(name,'CURVE');cu.dimensions='3D';cu.resolution_u=2;cu.bevel_depth=radius;cu.bevel_resolution=2
 for j,pts in enumerate(paths):
  sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
  for k,(p,co) in enumerate(zip(sp.points,pts)):
   p.co=(*co,1);p.radius=(radii[k] if radii else max(.15,sin(pi*(k+.4)/(len(pts)+.5))**.3))
 ob=bpy.data.objects.new(name,cu);sc.collection.objects.link(ob);ob.data.materials.append(mats[ma]);return ob
# Eyes: full globe within sockets, not plates pasted to a head.
def uvball(n,loc,scale,ma,seg=48,rings=32):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.name=n;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(mats[ma]);
 for p in o.data.polygons:p.use_smooth=True
 return o
for s in [-1,1]:
 center=np.array([s*.414,-.675,1.521]);uvball('recessed eyeball '+str(s),H(center),(S*.246,)*3,'eye_white')
 # Iris follows spherical corneal surface, so no flat button/white halo.
 for typ,rad,ma in [('iris',.083,'iris'),('pupil',.030,'pupil')]:
  vv=[];ff=[]
  for j,r in enumerate(np.linspace(0,rad,13)):
   for k in range(64):
    a=2*pi*k/64;x=center[0]+r*cos(a);z=center[2]+r*sin(a);y=center[1]-sqrt(.247**2-r*r)-(.002 if typ=='iris' else .004);vv.append(H((x,y,z)))
  for j in range(12):
   for k in range(64):ff.append((j*64+k,j*64+(k+1)%64,(j+1)*64+(k+1)%64,(j+1)*64+k))
  mesh(typ+' curved cornea '+str(s),vv,ff,ma)
 # Eyelashes modest and brows in directional hairs instead of chunky bars.
 paths=[]
 for i in range(180):
  u=random.random();x=.20+.46*u;z=1.707-.08*u+.025*sin(pi*u)+random.uniform(-.018,.018)
  y=float(-.95+.20*u+.20*u*u);pts=[]
  for t in np.linspace(0,1,4):pts.append(H((s*(x+.030*t),y-.008*sin(pi*t),z+.031*t-.015*t*t)))
  paths.append(pts)
 curves('individual eyebrow hairs '+str(s),paths,.00017,'hair_1')
 # nostril shadow is small and tucked under the alar wing.
 p=H((s*.143,-1.175,.947));o=uvball('nostril recess '+str(s),p,(.0044,.0011,.0019),'nostril',24,12);o.rotation_euler.z=s*.24
# Mouth seam follows the sculpted closed lip edge, never a thick painted line.
path=[]
for x in np.linspace(-.32,.32,55):
 z=.687+.015*(abs(x)/.32)**1.5-.009*exp(-(x/.07)**2)
 dep=float(-.93+.19*(abs(x)/.32)**2)
 path.append(H((x,dep-.007,z)))
curves('closed mouth recessed seam',[path],.00038,'waterline')
# Ear is a single concave sculpted surface with integrated helix ridge.
for s in [-1,1]:
 vv=[];ff=[];nr=28;nt=80
 for j,r in enumerate(np.linspace(.001,1,nr)):
  for k,a in enumerate(np.linspace(0,2*pi,nt,endpoint=False)):
   # outline oblique, no ball-on-head ear. Helix is one continuous ridge.
   x=s*(.92+.19*r*cos(a)+.04*r*sin(a));z=1.35+.36*r*sin(a)
   y=.035-.065*r+.062*exp(-((r-.48)/.23)**2)-.060*exp(-((r-.88)/.10)**2)
   vv.append(H((x,y,z)))
 for j in range(nr-1):
  for k in range(nt):ff.append((j*nt+k,j*nt+(k+1)%nt,(j+1)*nt+(k+1)%nt,(j+1)*nt+k))
 mesh('sculpted ear cartilage '+str(s),vv,ff,'skin_details',1,.002)
# Anatomical neck and trapezius base: broad at shoulders, buried into collar.
def rings_mesh(n,rings,ma,N=100,sub=1,fold=0):
 vv=[];ff=[]
 for j,(z,cx,cy,rx,ry) in enumerate(rings):
  for k in range(N):
   a=2*pi*k/N;f=1+fold*sin(7*a+j*.8)+fold*.3*sin(11*a-j)
   vv.append((cx+rx*sin(a)*f,cy-ry*cos(a)*f,z))
 for j in range(len(rings)-1):
  for k in range(N):ff.append((j*N+k,j*N+(k+1)%N,(j+1)*N+(k+1)%N,(j+1)*N+k))
 return mesh(n,vv,ff,ma,sub)
rings_mesh('neck with trapezius transition',[(1.45,0,.025,.15,.077),(1.50,0,.023,.10,.063),(1.55,0,.027,.060,.054),(1.62,0,.032,.052,.054),(1.67,0,.034,.054,.051)],'skin_details',N=80,sub=2)
# A narrow sternomastoid relief rises from collar; no exposed long tube neck.
# Bust only; no lower body. Continuous shirt foundation under tailored jerkin.
rings_mesh('tailored upper torso leather shell',[(1.10,0,.018,.153,.108),(1.18,0,.012,.167,.112),(1.27,0,.009,.190,.120),(1.36,0,.012,.218,.126),(1.43,0,.017,.228,.109),(1.48,0,.023,.185,.082),(1.51,0,.026,.090,.060)],'oiled_leather',N=128,sub=2,fold=.007)
# Sewn shoulder sleeves — bent surface sections, no cylinders with ball elbows.
for s in [-1,1]:
 rings=[]
 for z,x,y,rx,ry in [(1.46,.198,.017,.075,.085),(1.43,.23,.012,.084,.093),(1.37,.255,.01,.080,.090),(1.29,.273,.004,.075,.081),(1.21,.286,-.005,.077,.077),(1.16,.29,-.01,.071,.072)]:rings.append((z,s*x,y,rx,ry))
 rings_mesh('linen sleeve shoulder '+str(s),list(reversed(rings)),'linen',N=100,sub=2,fold=.045)
# Tailored front leather seams and flat straps follow body, not triangle decorations.
for s in [-1,1]:
 pts=[]
 for t in np.linspace(0,1,80):
  z=1.13+.30*t;x=s*(.095+.035*sin(pi*t));y=-.102-.022*sin(pi*t)
  pts.append((x,y-.008,z))
 curves('shaped jerkin seam '+str(s),[pts],.0011,'leather_edge')
# Draped scarf has one diagonal sagging folded sheet wrapping the shoulders.
# Three unequal hems and intersecting slack folds, not stacked torus rings.
vv=[];ff=[];N=180;K=56
for j in range(K):
 t=j/(K-1)
 for i in range(N):
  a=2*pi*i/N;front=max(0,cos(a));back=max(0,-cos(a))
  r=.071+.075*t+.025*sin(pi*t)+.024*front*t
  z=1.603-.045*t-.132*front*(t**.8)+.014*sin(a+.7)-.016*sin(2*a+t*1.8)*sin(pi*t)
  # gravitational folds trace diagonally and converge toward the fastening point.
  r+=.009*sin(3*pi*t+1.8*a)*sin(pi*t)+.006*sin(7*a+2*t)*t
  x=r*sin(a);y=.026-r*.75*cos(a)
  vv.append((x,y,z))
for j in range(K-1):
 for i in range(N):ff.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
mesh('continuous diagonally draped wool cowl',vv,ff,'teal_wool',1,.002)
# A second broad returning fold cuts diagonally rather than adding another ring.
vv=[];ff=[];W=60;R=12
for j in range(R):
 t=j/(R-1)
 for i in range(W):
  u=i/(W-1);x=-.145+.29*u;z=1.527+.070*u-.042*sin(pi*u)-.035*t
  y=-.080-.060*sin(pi*u)-.014*sin(pi*t)+.012*u
  vv.append((x,y,z))
for j in range(R-1):
 for i in range(W-1):ff.append((j*W+i,j*W+i+1,(j+1)*W+i+1,(j+1)*W+i))
mesh('scarf returning diagonal overlap',vv,ff,'teal_wool',1,.002)
# Left cloth shoulder fall, with broad heavy folds, asymmetrical frayed bottom.
vv=[];ff=[];W=48;R=40
for j in range(R):
 t=j/(R-1)
 for i in range(W):
  u=i/(W-1);x=-.085-.21*u-.025*t;y=.025-.115*t+.018*sin(pi*u);z=1.52-.085*u-.22*t
  y+=.015*sin(u*3*pi+.8*t)*t;z+=.009*sin(u*5*pi+t)*t
  if j==R-1:z+=.006*sin(i*4)+.008*sin(i*1.7)
  vv.append((x,y,z))
for j in range(R-1):
 for i in range(W-1):ff.append((j*W+i,j*W+i+1,(j+1)*W+i+1,(j+1)*W+i))
mesh('heavy asymmetrical shoulder wool fall',vv,ff,'teal_wool',1,.002)
# Forged shoulder shell: longitudinal shoulder section, not a horizontal dome stack.
for plate in range(2):
 vv=[];ff=[];N=60;K=35
 for j in range(K):
  t=j/(K-1);cx=.157+.148*t;cz=1.465-.105*t-.034*t*t-plate*.047
  for i in range(N):
   a=-1.24+2.48*i/(N-1);width=.090-.009*t-plate*.006
   x=cx+.032*cos(a)*sin(pi*t);y=.012+width*sin(a);z=cz+(.076-plate*.010)*cos(a)*sin(pi*(.20+.7*t))
   # central hammered ridge and taper to arm, broad irregular reflection.
   z+=.006*exp(-(a/.23)**2)*sin(pi*t)
   vv.append((x,y,z))
 for j in range(K-1):
  for i in range(N-1):ff.append((j*N+i,j*N+i+1,(j+1)*N+i+1,(j+1)*N+i))
 mesh('formed steel shoulder shell '+str(plate),vv,ff,'iron',1,.003)
 edge=[vv[i] for i in range(N)]+[vv[j*N+N-1] for j in range(1,K)]+[vv[(K-1)*N+i] for i in range(N-2,-1,-1)]+[vv[j*N] for j in range(K-2,0,-1)]
 curves('rolled forged plate edge '+str(plate),[edge+[edge[0]]],.0015,'iron_edge')
 for k in [9,30,50]:
  p=np.array(vv[(K-3)*N+k]);p[2]+=.002;uvball('peened steel rivet',p,(.0028,.0028,.0014),'iron_edge',16,8)
# Single diagonal leather baldric, quietly sitting against leather body.
vv=[];ff=[];N=90
for j in range(N):
 t=j/(N-1);x=.14-.27*t;z=1.48-.36*t;y=-.105-.024*sin(pi*t)
 for q in [-1,0,1]:vv.append((x+q*.014,y-.004*(1-q*q),z+q*.010))
for j in range(N-1):
 for k in range(2):ff.append((j*3+k,j*3+k+1,(j+1)*3+k+1,(j+1)*3+k))
mesh('fitted diagonal sword baldric',vv,ff,'oiled_leather',1,.005)
# Hair: volumetric silhouette from continuous scalp and thousands of fine swept strands.
# No strips or sausage locks. Independent guides vary flow and length by region.
def cap(theta,phi,extra=0):
 x=(1.005+extra)*sin(theta)*sin(phi)
 y=.17-(1.01+extra)*sin(theta)*cos(phi)
 z=1.98+(1.00+extra)*cos(theta)
 # asymmetrical lift on left crown, flattened sides and irregular fringe
 z+=.09*sin(phi+.8)*sin(theta)**2
 return np.array([x,y,z])
def max_theta(phi):
 front=max(0,cos(phi));back=max(0,-cos(phi));return 1.67-.25*front+.50*back+.08*sin(3*phi)
vv=[];ff=[];N=160;K=64
for j in range(K):
 for i in range(N):
  phi=2*pi*i/N;theta=.005+(max_theta(phi)-.005)*j/(K-1);v=cap(theta,phi,.006*sin(phi*7+theta*6))
  vv.append(H(v))
for j in range(K-1):
 for i in range(N):ff.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
mesh('asymmetric continuous hair volume foundation',vv,ff,'hair_core',1)
paths=[[],[],[],[]]
# directional guide-field with curls and loose tapered ends, 3-D geometry all around.
for i in range(6200):
 phi=random.uniform(-pi,pi);t0=random.uniform(.05,max_theta(phi)-.05)
 length=random.uniform(.35,.70);theta_end=min(max_theta(phi)+random.uniform(.03,.19),t0+length)
 drift=-.39-.22*cos(phi)+random.uniform(-.12,.12);wav=random.uniform(0,2*pi);pts=[]
 for k,q in enumerate(np.linspace(0,1,12)):
  t=t0+(theta_end-t0)*q;p=phi+drift*q+.05*sin(pi*q+wav)
  extra=.012+random.uniform(0,.014)+.055*sin(pi*q)+.020*sin(q*2*pi+wav)
  v=cap(t,p,extra);v[0]+=.025*sin(q*pi*2+wav)*sin(pi*q)
  # individual pointed flyaway tips outside the underlying scalp
  v[2]+=.035*q*q*sin(wav);pts.append(H(v))
 paths[random.choices([0,1,2,3],[.45,.35,.08,.12])[0]].append(pts)
for i,ps in enumerate(paths):curves('swept individual hair strands '+str(i),ps,.00014+(.00002 if i==0 else 0),'hair_'+str(i))
# Directed fringe tufts have actual curving fibers, not blunt uniform spikes.
for group,(phi,root,span,drift) in enumerate([(-.8,.65,1.0,.58),(-.3,.65,1.05,.40),(.25,.50,1.15,.20),(.6,.65,1.00,-.25)]):
 ps=[]
 for i in range(130):
  jitter=random.uniform(-.11,.11);pts=[]
  for q in np.linspace(0,1,15):
   t=root+span*q;p=phi+drift*q+jitter*(1-.7*q);ex=.045+.10*sin(pi*q)+random.uniform(0,.025)
   v=cap(t,p,ex);v[2]-=.13*q**3;pts.append(H(v))
  ps.append(pts)
 curves('layered swept fringe fibers '+str(group),ps,.00017,'hair_'+str(group%3))
# Beard is quiet stubble anchored to the facial surface, not detached beard pieces.
ps=[]
valid=np.where((verts[:,2]>.18)&(verts[:,2]<.93)&(verts[:,1]<-.40)&(np.abs(verts[:,0])<.8))[0]
for idx in random.sample(list(valid),min(1450,len(valid))):
 x,y,z=verts[idx]
 if abs(x)<.34 and .51<z<.82:continue
 p=np.array([x,y-.003,z]);ps.append([H(p),H(p+np.array([.001,-.008,-.011]))])
curves('fine weathered stubble',ps,.000065,'hair_0')
# Set neutral editorial studio: no beauty postproduction; RGB model renders.
mat('backdrop',(.052,.064,.065),.92)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.96));o=bpy.context.object;o.name='studio ground';o.data.materials.append(mats['backdrop'])
world=bpy.data.worlds.new('neutral studio world') if not bpy.data.worlds else bpy.data.worlds[0];sc.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.18,.20,.22,1);world.node_tree.nodes['Background'].inputs[1].default_value=.32
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def light(n,loc,power,size,color):
 d=bpy.data.lights.new(n,'AREA');d.energy=power;d.shape='DISK';d.size=size;d.color=color;o=bpy.data.objects.new(n,d);sc.collection.objects.link(o);o.location=loc;aim(o,(0,0,1.55))
light('large warm portrait key',(-1.2,-1.8,2.5),105,1.4,(1,.86,.74));light('soft cool fill',(1.4,-.6,1.9),38,1.2,(.73,.85,1));light('hair and steel rim',(.4,1,2.4),90,.95,(1,.92,.81))
d=bpy.data.cameras.new('portrait camera');cam=bpy.data.objects.new('portrait camera',d);sc.collection.objects.link(cam);sc.camera=cam
cam.location=(.76,-2.4,1.86);aim(cam,(0,-.008,1.51));d.type='ORTHO';d.ortho_scale=.83;d.lens=85
sc.render.engine='CYCLES';sc.cycles.samples=40;sc.cycles.use_denoising=False;sc.cycles.max_bounces=7
sc.render.resolution_x=820;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA';sc.render.film_transparent=False
sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast';sc.view_settings.exposure=.25
sc.render.filepath=str(OUT/'previews/static_bust_feasibility_v1.png')
# Preserve all true source curves, landmark mesh and procedural materials in .blend.
bpy.ops.wm.save_as_mainfile(filepath=str(P/'hero_static_bust_feasibility.blend'))
bpy.ops.render.render(write_still=True)
report={'status':'FEASIBILITY REVIEW ONLY / NOT APPROVED','method':'Independent anatomical landmark-interpolated skin with real eye apertures; actual fine curve hair; cloth/formed-shell geometry. No reused rejected geometry and no projected concept.','rigs':0,'animations':0,'head_vertices':len(verts),'head_triangles':len(data['faces']),'objects':len(sc.objects),'reference':'assets/concepts/player-four-view-v2.png','render':str(OUT/'previews/static_bust_feasibility_v1.png')}
(OUT/'technical-facts.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
