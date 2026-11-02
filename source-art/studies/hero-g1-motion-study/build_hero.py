"""Original editable character study. No downloaded assets or concept-image projection.
Run: blender -b -t 8 --python source-art/studies/hero-g1-motion-study/build_hero.py
"""
from pathlib import Path
import bpy, bmesh, math, random, json, os, numpy as np
from mathutils import Vector
from math import sin, cos, pi, exp
random.seed(261102)
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'assets/studies/hero-g1-motion-study'
SOURCE=Path(__file__).resolve().parent
for d in ['previews','frames','models','textures']: (OUT/d).mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for x in list(bpy.data.materials): bpy.data.materials.remove(x)
scene=bpy.context.scene
COL=bpy.data.collections.new('Hero / ORIGINAL STUDY / NOT APPROVED'); scene.collection.children.link(COL)
STUDIO=bpy.context.collection
parts=[]; bind={}; M={}
# Repeatable original UV textures. Multi-scale grain is deliberately restrained;
# silhouettes, folds, seams, hems, panel overlap and thickness are actual geometry.
def field(n,seed):
 rng=np.random.default_rng(seed); a=np.zeros((n,n),dtype=np.float32)
 yy,xx=np.mgrid[0:n,0:n]
 for scale,amp in [(5,.50),(13,.25),(37,.13),(97,.07)]:
  base=rng.random((scale,scale)); x=xx/n*scale; y=yy/n*scale
  ix=x.astype(int); iy=y.astype(int); fx=x-ix; fy=y-iy
  fx=fx*fx*(3-2*fx); fy=fy*fy*(3-2*fy)
  v=(base[iy%scale,ix%scale]*(1-fx)+base[iy%scale,(ix+1)%scale]*fx)*(1-fy)+(base[(iy+1)%scale,ix%scale]*(1-fx)+base[(iy+1)%scale,(ix+1)%scale]*fx)*fy
  a+=amp*v
 return a

def make_mat(name,color,kind='leather',metal=0,rough=.65):
 n=1024; yy,xx=np.mgrid[0:n,0:n]; f=field(n,100+len(M)); rng=np.random.default_rng(500+len(M)); grain=rng.random((n,n))-.5
 if kind=='cloth':
  weave=(np.sin(xx*pi*.52)*np.sin(yy*pi*.51))*.025
  height=.45*f+.08*grain+weave; mod=.80+.38*f+.03*grain
 elif kind=='steel':
  scratches=np.sin(yy*.13+np.sin(xx*.006)*2)**60
  height=.16*f+.03*grain-.08*scratches;mod=.80+.35*f-.05*scratches
 elif kind=='skin':
  height=.12*f+.025*grain;mod=.94+.12*f+.015*grain
 elif kind=='hair':
  height=.4*np.sin(xx*.28+np.sin(yy*.014))+.08*f;mod=.65+.6*f+.08*np.sin(xx*.28+np.sin(yy*.014))
 else:
  pores=(np.sin(xx*.64+f*12)*np.sin(yy*.81+f*9))**2
  height=.3*f+.09*grain+.06*pores;mod=.73+.48*f+.055*grain
 # Generated original image files, not painted concept cutouts.
 rgb=np.stack([np.clip(c*mod,0,1) for c in color],axis=2).astype(np.float32)
 rgb=np.where(rgb<=.0031308,12.92*rgb,1.055*np.power(rgb,1/2.4)-.055).astype(np.float32)
 rgba=np.concatenate([rgb,np.ones((n,n,1),np.float32)],axis=2)
 im=bpy.data.images.new(name+'_basecolor',width=n,height=n,alpha=True);im.pixels.foreach_set(rgba.ravel()); im.filepath_raw=str(OUT/'textures'/(name+'_basecolor.png'));im.file_format='PNG';im.save();im.pack()
 h=np.clip(height,0,1).astype(np.float32); hm=np.stack([h,h,h,np.ones_like(h)],axis=2)
 bump=bpy.data.images.new(name+'_height',width=n,height=n,alpha=True);bump.colorspace_settings.name='Non-Color';bump.pixels.foreach_set(hm.ravel());bump.filepath_raw=str(OUT/'textures'/(name+'_height.png'));bump.file_format='PNG';bump.save();bump.pack()
 mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.diffuse_color=(*color,1); nodes=mat.node_tree.nodes; links=mat.node_tree.links;p=nodes.get('Principled BSDF'); p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 tex=nodes.new('ShaderNodeTexImage');tex.image=im;links.new(tex.outputs['Color'],p.inputs['Base Color'])
 t=nodes.new('ShaderNodeTexImage');t.image=bump
 b=nodes.new('ShaderNodeBump');b.inputs['Strength'].default_value=.17 if kind not in ['steel','skin'] else .10;b.inputs['Distance'].default_value=.0015 if kind!='skin' else .0005;links.new(t.outputs['Color'],b.inputs['Height']);links.new(b.outputs['Normal'],p.inputs['Normal'])
 ramp=nodes.new('ShaderNodeMapRange');ramp.clamp=True;ramp.inputs['From Min'].default_value=.0;ramp.inputs['From Max'].default_value=.7;ramp.inputs['To Min'].default_value=max(.1,rough-.015);ramp.inputs['To Max'].default_value=min(.95,rough+.07);links.new(t.outputs['Color'],ramp.inputs['Value']);links.new(ramp.outputs['Result'],p.inputs['Roughness'])
 if kind=='skin':p.inputs['Subsurface Weight'].default_value=.07
 M[name]=mat
 return mat
for args in [('oiled_leather',(.19,.095,.046),'leather',0,.58),('worn_edges',(.29,.16,.075),'leather',0,.71),('dark_boots',(.095,.052,.030),'leather',0,.57),('linen',(.56,.49,.36),'cloth',0,.83),('charcoal_wool',(.095,.083,.069),'cloth',0,.85),('teal_wool',(.037,.125,.132),'cloth',0,.88),('forged_steel',(.27,.29,.285),'steel',.76,.52),('old_brass',(.34,.245,.11),'steel',.72,.5),('skin',(.48,.29,.19),'skin',0,.64),('brown_hair',(.050,.031,.018),'hair',0,.74)]: make_mat(*args)
def solid(name,c,metal=0,r=.5):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=r;M[name]=m
for a in [('eye',(.47,.44,.34)),('iris',(.085,.10,.071)),('pupil',(.009,.009,.006)),('mouth',(.17,.065,.039)),('steel_edge',(.47,.49,.46),.8,.29),('amber',(.26,.052,.009),.2,.24),('black',(.018,.014,.01))]:solid(*a)

def finish(o,n,m,bone='chest',smooth=True):
 o.name=n
 for c in list(o.users_collection): c.objects.unlink(o)
 COL.objects.link(o)
 o.data.materials.append(M[m]);parts.append(o);bind[o.name]=bone
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=smooth
 return o

def mesh(n,v,f,m,bone='chest',uv=None,smooth=True,sub=0):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);COL.objects.link(o);o=finish(o,n,m,bone,smooth)
 layer=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  coords=[]
  for vi in p.vertices:
   if uv is None:
    co=me.vertices[vi].co; coords.append((co.x*2+co.z*.3,co.z*2))
   else: coords.append(uv[vi])
  if uv and max(c[0] for c in coords)-min(c[0] for c in coords)>.7:
   coords=[(u+1 if u<.3 else u,v) for u,v in coords]
  for li,co in zip(p.loop_indices,coords):layer.data[li].uv=co
 if sub:
  md=o.modifiers.new('Sculpt surface smoothing','SUBSURF');md.levels=sub;md.render_levels=sub
 return o

def ell(n,loc,sc,m,bone='chest',seg=32,rings=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.scale=sc;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,m,bone)

def tube(n,points,radii,m,bone='chest',N=12,flatten=1,sub=0):
 v=[];f=[];uv=[]
 for j,p in enumerate(points):
  tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
  q=tangent.to_track_quat('Z','Y')
  for i in range(N):
   a=2*pi*i/N; v.append(Vector(p)+q@Vector((radii[j]*cos(a),radii[j]*sin(a)*flatten,0)));uv.append((i/N,j/(len(points)-1)))
 for j in range(len(points)-1):
  for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 f.extend([tuple(range(N-1,-1,-1)),tuple((len(points)-1)*N+i for i in range(N))]);return mesh(n,v,f,m,bone,uv,sub=sub)

def loft(n,rings,m,bone='chest',N=48,fold=0,sub=1):
 # rings z,center x, center y, radius x,radius y. Controlled garment tension folds.
 v=[];f=[];uv=[]
 for j,(z,x,y,rx,ry) in enumerate(rings):
  for i in range(N):
   a=2*pi*i/N
   k=1+fold*(.6*sin(a*7+j*.65)+.3*sin(a*11-j*.8))
   if 'trouser' in n:
    k+=.07*exp(-((z-.55)/.13)**2)*sin(j*2.9+a*2.2)
   if 'boot shaft' in n:
    k+=.055*exp(-((z-.19)/.08)**2)*sin(j*3+a*2)
   v.append((x+rx*sin(a)*k,y-ry*cos(a)*k,z));uv.append((i/N,j/(len(rings)-1)))
 for j in range(len(rings)-1):
  for i in range(N):f.append((j*N+i,(j+1)*N+i,(j+1)*N+(i+1)%N,j*N+(i+1)%N))
 f.extend([tuple(range(N-1,-1,-1)),tuple((len(rings)-1)*N+i for i in range(N))]);return mesh(n,v,f,m,bone,uv,sub=sub)

def panel(n,rows,m,bone='chest',th=.004,sub=1):
 # Ordered equal-length rows, not extruded flat rectangles.
 v=[p for row in rows for p in row];ny=len(rows);nx=len(rows[0]);f=[];uv=[]
 for j in range(ny):
  for i in range(nx):uv.append((i/(nx-1),j/(ny-1)))
 for j in range(ny-1):
  for i in range(nx-1):f.append((j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i))
 o=mesh(n,v,f,m,bone,uv,sub=sub)
 mod=o.modifiers.new('Material thickness','SOLIDIFY');mod.thickness=th;return o

def band(n,pts,w,m,bone='chest',th=.006):
 rows=[]
 for j,p in enumerate(pts):
  d=Vector(pts[min(j+1,len(pts)-1)])-Vector(pts[max(0,j-1)]);a=Vector((-d.z,0,d.x)).normalized()*w/2;rows.append([Vector(p)-a,Vector(p),Vector(p)+a])
 return panel(n,rows,m,bone,th,1)

def stitch(n,pts,bone='chest',r=.0011,mat='worn_edges'):
 # Sparse interrupted stitches, not continuous bright piping.
 for i in range(len(pts)-1):
  a=Vector(pts[i]);b=Vector(pts[i+1]);dist=(b-a).length;num=max(1,int(dist/.012))
  for j in range(num):
   tube(n,[a.lerp(b,(j+.15)/num),a.lerp(b,(j+.52)/num)],[r,r],mat,bone,N=5)

def rivet(p,bone='chest',r=.0038):return ell('peened brass rivet',p,(r,r*.45,r),'old_brass',bone,12,8)
def buckle(p,w,h,bone='pelvis'):
 x,y,z=p;pts=[(x-w/2,y,z-h/2),(x+w/2,y,z-h/2),(x+w/2,y,z+h/2),(x-w/2,y,z+h/2),(x-w/2,y,z-h/2)]
 tube('forged buckle frame',pts,[.0032]*5,'steel_edge',bone,10)
 tube('buckle pin',[(x-w*.4,y-.003,z),(x+w*.45,y-.003,z+.002)],[.0023,.0023],'steel_edge',bone,8)

# Lower body: anatomical hip, thigh and knee variation, compressive trouser folds.
loft('pelvis under layers',[(.84,0,.012,.165,.103),(.90,0,.012,.18,.113),(1.04,0,0,.17,.106)],'charcoal_wool','pelvis',fold=.018)
for s,side in [(-1,'R'),(1,'L')]:
 x=s*.106; thigh='thigh.'+side;shin='shin.'+side;foot='foot.'+side
 rr=[(.385,x,-.006,.057,.061),(.43,x,-.008,.071,.066),(.465,x,-.011,.075,.072),(.49,x,-.014,.065,.068),(.525,x,-.019,.076,.080),(.55,x,-.019,.073,.085),(.58,x,-.014,.080,.079),(.61,x,-.008,.075,.081),(.65,x,.005,.082,.09),(.72,x,.016,.092,.098),(.80,x,.019,.102,.103),(.88,x,.014,.109,.108),(.96,x,.01,.11,.105)]
 loft('tailored wool trouser '+side,rr,'charcoal_wool',('leg',side),N=64,fold=.12,sub=1)
 # Side seam and tension creases are integrated/subtle, not uniform sausages.
 tube('trouser outside seam '+side,[(x+s*.07,0,.45),(x+s*.08,.012,.56),(x+s*.09,.015,.7),(x+s*.10,.012,.87)],[.0022]*4,'charcoal_wool',('leg',side),8)
 # Foot last is longitudinal sectioned, squared toe and raised instep.
 v=[];f=[];uv=[];N=32
 sections=[(-.211,.002,.036,.029),(-.202,.006,.057,.034),(-.17,.008,.070,.042),(-.12,.015,.071,.053),(-.055,.027,.064,.07),(.005,.035,.055,.072),(.066,.015,.05,.045),(.078,.01,.035,.031)]
 for j,(y,zc,rx,rz) in enumerate(sections):
  for i in range(N):
   a=2*pi*i/N;v.append((x+rx*cos(a),y,.046+zc+rz*sin(a)));uv.append((i/N,j/(len(sections)-1)))
 for j in range(len(sections)-1):
  for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 f.extend([tuple(range(N-1,-1,-1)),tuple((len(sections)-1)*N+i for i in range(N))]);mesh('shaped leather boot last '+side,v,f,'dark_boots',foot,uv,sub=1)
 # Separate welt/sole follows same foot shape.
 outline=[(x+rx*cos(a),y,.028+.003*cos(a)) for y,zc,rx,rz in sections for a in []]
 pts=[]
 for a in np.linspace(0,2*pi,65):pts.append((x+.075*sin(a),-.063-.145*cos(a),.032))
 tube('stitched boot welt '+side,pts,[.006]*len(pts),'worn_edges',foot,10,flatten=.65)
 ell('hard leather sole '+side,(x,-.064,.018),(.076,.145,.014),'black',foot,40,12)
 loft('fitted boot shaft '+side,[(.085,x,.024,.053,.062),(.13,x,.016,.057,.06),(.18,x,.008,.052,.052),(.205,x,.009,.056,.052),(.23,x,.008,.052,.048),(.26,x,.004,.057,.054),(.31,x,0,.063,.062),(.36,x,-.005,.067,.065),(.41,x,-.006,.070,.068),(.43,x,-.007,.070,.067)],'dark_boots',shin,N=48,fold=.043,sub=1)
 # Sagging cuff and small shin guard panel.
 loft('folded boot cuff '+side,[(.38,x,-.006,.071,.069),(.40,x,-.006,.079,.075),(.435,x,-.005,.081,.074),(.44,x,-.005,.076,.070)],'oiled_leather',shin,fold=.024)
 for z in [.155,.295]:
  pts=[(x+.058*sin(a),.003-.059*cos(a),z+.006*sin(a)) for a in np.linspace(0,2*pi,25)];tube('thin boot strap '+side,pts,[.008]*25,'oiled_leather',shin,10,flatten=.4)
  buckle((x+s*.032,-.061,z),.025,.019,shin)
 for j in range(5):
  z=.115+j*.024;y=-.102+j*.008
  tube('crossed boot lacing '+side,[(x-.027,y,z),(x+.026,y-.005,z+.018)],[.0023]*2,'worn_edges',foot,6)
# Torso fitted leather with contoured upper chest/underarm and narrow waist.
torso=[(.95,0,.008,.169,.110),(1.00,0,.004,.165,.110),(1.075,0,.004,.154,.109),(1.14,0,.002,.160,.114),(1.22,0,0,.179,.120),(1.30,0,.003,.201,.124),(1.37,0,.008,.214,.115),(1.425,0,.012,.202,.094),(1.47,0,.018,.141,.074)]
loft('fitted leather jerkin',torso,'oiled_leather',('torso',),N=64,fold=.008,sub=2)
# Shaped lapel and irregular diagonal front panels, contour exactly to torso.
for s in [-1,1]:
 rows=[]
 for z,wide,depth in [(1.04,.14,.117),(1.11,.15,.121),(1.20,.17,.128),(1.30,.18,.132),(1.39,.13,.111)]:
  rows.append([(s*.008,-depth-.009,z),(s*wide*.5,-depth-.004,z+.009),(s*wide,-depth*.62,z+.023)])
 panel('curved sewn jerkin half '+str(s),rows,'oiled_leather',('torso',),.005,1)
 stitch('jerkin seam',[(s*.013,-.135,1.09),(s*.014,-.143,1.27),(s*.015,-.125,1.38)],('torso',),r=.0009)
for z in [1.08,1.15,1.22,1.29]:
 rivet((-.016,-.138,z),('torso',),.0028);tube('front lacing', [(-.018,-.141,z),(.019,-.141,z+.035)],[.0017,.0017],'worn_edges',('torso',),6)
# Overlapping tailored reinforcement panels follow the torso; no floating triangles.
def torsofront(x,z):
 rx=float(np.interp(z,[r[0] for r in torso],[r[3] for r in torso]));ry=float(np.interp(z,[r[0] for r in torso],[r[4] for r in torso]));cy=float(np.interp(z,[r[0] for r in torso],[r[2] for r in torso]))
 return cy-ry*math.sqrt(max(.05,1-(x/rx)**2))-.012
for s in [-1,1]:
 for j in range(3):
  rows=[]
  for t in [0,.08,.45,.92,1]:
   row=[]
   for i in range(12):
    u=i/11;x=s*(.017+(.125+j*.011)*u);z=1.065+j*.098+.067*t+.033*u
    row.append((x,torsofront(x,z)-.002*sin(pi*t),z))
   rows.append(row)
  panel('overlapping contoured leather reinforcement',rows,'oiled_leather',('torso',),.004,1)
  edge=[(x,y-.002,z+.004) for x,y,z in rows[0]];stitch('reinforcement saddle stitching',edge,('torso',),.0009)
  for idx in [0,10]:
   x,y,z=rows[1][idx];rivet((x,y-.004,z+.009),('torso',),.0027)
# Segmented tapered leather skirt with softened edges and worn stitching.
for i in range(11):
 a=2*pi*i/11;rows=[]
 for t in [0,.05,.5,.94,1]:
  z=.995-.235*t+(i%3)*.009; rad=.178+.035*t
  rows.append([(rad*sin(a+u),-rad*.68*cos(a+u),z+.013*sin(u*5+i)) for u in [-.225,-.10,0,.10,.225]])
 panel('shaped skirt tasset %02d'%i,rows,'oiled_leather' if i%3 else 'dark_boots','pelvis',.005,1)
 for k in [0,4]:
  pts=[(p[k][0],p[k][1]-.002,p[k][2]) for p in rows]
  stitch('tasset edge stitches',pts,'pelvis',.0008)
# Belt ellipse actual thickness and tailored diagonal single baldric.
loft('broad waist belt',[(.984,0,.0,.182,.123),(.990,0,0,.184,.125),(1.035,0,0,.177,.121),(1.042,0,0,.176,.119)],'dark_boots','pelvis',N=64,sub=1)
buckle((-.028,-.131,1.014),.047,.041)
band('diagonal sword baldric',[(-.154,-.085,1.439),(-.120,-.124,1.37),(-.052,-.151,1.285),(.037,-.146,1.20),(.119,-.123,1.105),(.163,-.093,1.047)],.037,'dark_boots',('torso',))
for p in [(-.101,-.138,1.345),(.037,-.153,1.204),(.125,-.13,1.104)]:rivet(p,('torso',),.003)
buckle((-.055,-.16,1.282),.032,.041, 'chest')
# Back pack harness only visible in back, following torso.
for s in [-1,1]:
 band('back pack shoulder strap',[(s*.13,-.07,1.43),(s*.14,.02,1.47),(s*.15,.113,1.38),(s*.14,.15,1.22),(s*.10,.125,1.08)],.027,'oiled_leather',('torso',))
# Arms with shirt under armour, bare elbow, bound forearms and natural smaller hands.
for s,side in [(-1,'R'),(1,'L')]:
 up='upper_arm.'+side;fore='forearm.'+side;hand='hand.'+side
 shoulder=Vector((s*.208,.004,1.408));elbow=Vector((s*.289,-.006,1.155));wrist=Vector((s*.323,-.060,.965))
 # Loose sleeve ends well above wrist with layered rolled cuff. Anatomical tapered volume.
 points=[shoulder,shoulder.lerp(elbow,.17),shoulder.lerp(elbow,.4),shoulder.lerp(elbow,.66),shoulder.lerp(elbow,.82),elbow]
 # Cross sections with wrinkles concentrated near cuff/armpit.
 v=[];f=[];uv=[];N=48
 for j,p in enumerate(points):
  q=(elbow-shoulder).to_track_quat('Z','Y');rr=[.076,.081,.078,.071,.069,.058][j]
  for i in range(N):
   a=2*pi*i/N;rrr=rr*(1+.105*sin(a*5+j*1.7)+.035*sin(a*9-j)); v.append(p+q@Vector((rrr*cos(a),rrr*sin(a)*.94,0)));uv.append((i/N,j/5))
 for j in range(5):
  for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 f.extend([tuple(range(N-1,-1,-1)),tuple(5*N+i for i in range(N))]);mesh('creased linen shirt sleeve '+side,v,f,'linen',up,uv,sub=2)
 p=shoulder.lerp(elbow,.89);q=(elbow-shoulder).to_track_quat('Z','Y')
 for off,rr in [(-.018,.064),(.0,.066),(.018,.061)]:
  center=p+(elbow-shoulder).normalized()*off
  pts=[center+q@Vector((rr*cos(a),rr*sin(a)*.97,0)) for a in np.linspace(0,2*pi,33)]
  tube('rolled linen cuff '+side,pts,[.009]*33,'linen',up,10,flatten=.7)
 tube('continuous forearm under cuff and bracer '+side,[shoulder.lerp(elbow,.76),shoulder.lerp(elbow,.9),elbow,elbow.lerp(wrist,.40),elbow.lerp(wrist,.8),wrist,Vector((s*.326,-.066,.925))],[.047,.048,.048,.043,.037,.033,.030],'skin',fore,32,sub=1)
 tube('leather under bracer '+side,[elbow.lerp(wrist,.26),elbow.lerp(wrist,.5),wrist],[.051,.047,.033],'dark_boots',fore,32,sub=1)
 # curved steel shell not flat patch
 rows=[]
 for t in [0,.06,.48,.94,1]:
  p=elbow.lerp(wrist,.32+.68*t);r=.054-.019*t
  rows.append([(p.x+r*sin(a),p.y-r*cos(a)-.004,p.z+.006*cos(a)) for a in [-1.2,-.9,-.5,0,.5,.9,1.2]])
 panel('fitted steel vambrace '+side,rows,'forged_steel',fore,.003,1)
 for t in [.43,.88]:
  p=elbow.lerp(wrist,t);r=.057-.022*t
  pts=[(p.x+r*sin(a),p.y-r*cos(a)-.005,p.z) for a in np.linspace(-1.3,1.3,20)]
  tube('vambrace rolled rim '+side,pts,[.0023]*20,'steel_edge',fore,8)
 for t in [.45,.85]:
  p=elbow.lerp(wrist,t);r=.057-.022*t;rivet((p.x+s*r*.8,p.y-r*.65-.006,p.z),fore,.0026)
 palm=Vector((s*.326,-.066,.914))
 ell('glove fitted palm '+side,palm,(.034,.024,.048),'dark_boots',hand,28,18)
 # Curled glove fingers, not visible flesh circles; correct opposite thumb.
 for j in range(4):
  x=s*(.303+j*.015);z=.913-(.009 if j in [0,3] else .002)
  pts=[(x,-.082,z),(x,-.095,z-.018),(x,-.088,z-.034),(x,-.071,z-.036)]
  tube('gloved finger '+side+str(j),pts,[.008,.0085,.008,.0055],'dark_boots',hand,10,sub=1)
  ell('glove knuckle '+side+str(j),(x,-.089,z+.003),(.008,.007,.009),'oiled_leather',hand,12,8)
 tube('opposed thumb '+side,[(s*.298,-.061,.937),(s*.287,-.079,.921),(s*.294,-.095,.906)],[.012,.011,.007],'dark_boots',hand,12,sub=1)
# Single left pauldron, complementary cloth right shoulder; no mirrored equipment.
for layer,(z,xc,rx,ry) in enumerate([(1.427,.215,.112,.105),(1.382,.25,.104,.099),(1.341,.269,.088,.09)]):
 v=[];f=[];uv=[];N=48;rows=10
 for j in range(rows):
  t=.06+j/9*1.50
  for i in range(N):
   a=2*pi*i/N;v.append((xc+rx*sin(t)*cos(a),.006+ry*sin(t)*sin(a),z+.065*cos(t)));uv.append((i/N,j/9))
 for j in range(rows-1):
  for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 o=mesh('articulated left shoulder plate '+str(layer),v,f,'forged_steel','upper_arm.L',uv,sub=1);o.modifiers.new('forged steel plate thickness','SOLIDIFY').thickness=.004
 tube('rolled shoulder edge',v[-N:]+[v[-N]],[.0026]*(N+1),'steel_edge','upper_arm.L',8)
 for k in [25,29,34,40]:rivet(Vector(v[-N+k])+Vector((0,-.002,.003)),'upper_arm.L',.003)
# Anatomical neck, a coherent sculpted head rather than assembled facial spheres.
loft('neck',[(1.43,0,.016,.057,.048),(1.50,0,.011,.050,.047),(1.56,0,.006,.046,.043),(1.62,0,.004,.051,.049)],'skin','neck',N=48,sub=2)
headrings=[(1.570,.020,.027,-.008),(1.581,.036,.037,-.004),(1.595,.049,.044,.0),(1.615,.060,.052,.006),(1.638,.067,.058,.012),(1.662,.070,.060,.015),(1.684,.073,.060,.017),(1.707,.074,.061,.018),(1.730,.073,.061,.018),(1.754,.071,.061,.019),(1.777,.067,.058,.020),(1.798,.054,.048,.022),(1.814,.032,.031,.021),(1.820,.004,.004,.021)]
def gauss(x,z,cx,cz,sx,sz):return exp(-((x-cx)/sx)**2-((z-cz)/sz)**2)
def sculpt_front(x,z):
 d=0
 # negative y pushes anatomy forward. Eye sockets inset under brow and above cheek.
 for s in [-1,1]:
  d+=.009*gauss(x,z,s*.029,1.707,.022,.013)
  d-=.007*gauss(x,z,s*.030,1.728,.026,.010)
  d-=.011*gauss(x,z,s*.048,1.677,.025,.017)
  d+=.006*gauss(x,z,s*.044,1.640,.018,.018)
 d-=.017*gauss(x,z,0,1.701,.010,.034)
 d-=.032*gauss(x,z,0,1.679,.014,.012)
 d-=.009*gauss(x,z,0,1.638,.029,.017)
 d-=.011*gauss(x,z,0,1.601,.028,.012)
 return d
oldhead=headrings;headrings=[]
for z in np.linspace(oldhead[0][0],oldhead[-1][0],65):
 headrings.append((z,*[float(np.interp(z,[r[0] for r in oldhead],[r[k] for r in oldhead])) for k in [1,2,3]]))
v=[];f=[];uv=[];N=96
for j,(z,rx,ry,cy) in enumerate(headrings):
 for i in range(N):
  a=2*pi*i/N;x=rx*sin(a);y=cy-ry*cos(a)
  y+=sculpt_front(x,z)*max(0,cos(a))**5
  v.append((x,y,z));uv.append((i/N,j/(len(headrings)-1)))
for j in range(len(headrings)-1):
 for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
mesh('continuous sculpted adult head',v,f,'skin','head',uv,sub=2)
# Deliberately modest eye apertures, subtle lids, no exposed eyeball spheres.
for s in [-1,1]:
 x=s*.029;y=-.0465;z=1.706
 rows=[[(x-.015,y+.002,z),(x-.007,y-.002,z+.004),(x+.005,y-.002,z+.004),(x+.015,y+.001,z)],[(x-.015,y+.002,z),(x-.007,y-.003,z-.003),(x+.005,y-.003,z-.003),(x+.015,y+.001,z)]]
 panel('almond eye aperture '+str(s),rows,'eye','head',.0002,1)
 ell('iris '+str(s),(x,-.050,1.706),(.0044,.0013,.0045),'iris','head',20,12)
 ell('pupil '+str(s),(x,-.0510,1.706),(.0018,.0005,.0023),'pupil','head',16,10)
 upper=[(x-.015,y,1.706),(x-.007,y-.003,1.712),(x+.005,y-.003,1.712),(x+.015,y+.001,1.706)]
 lower=[(x-.014,y+.001,1.705),(x,y-.003,1.701),(x+.014,y+.001,1.705)]
 tube('upper eyelid',upper,[.0016,.002,.002,.0013],'skin','head',10,sub=1);tube('lower eyelid',lower,[.0013,.0016,.0013],'skin','head',10,sub=1)
 tube('eyebrow',[(s*.014,-.049,1.726),(s*.028,-.052,1.73),(s*.047,-.042,1.727)],[.0025,.0034,.0016],'brown_hair','head',10,flatten=.45,sub=1)
 # Ear with helix contour and recessed inner cartilage.
 ell('ear '+str(s),(s*.073,.010,1.689),(.012,.018,.029),'skin','head',24,16)
 pts=[(s*(.078+.006*sin(a)),.009-.013*cos(a),1.691+.024*sin(a)) for a in np.linspace(-.3,pi*1.65,23)]
 tube('ear helix',pts,[.0024]*23,'skin','head',8)
 ell('ear concha',(s*.081,-.002,1.689),(.003,.008,.011),'mouth','head',16,10)
 # Tiny nostril aperture beneath continuous nose tip.
 ell('nostril '+str(s),(s*.010,-.071,1.671),(.0042,.0018,.0023),'mouth','head',16,10)
# Lips closely follow sculpted muzzle.
tube('closed mouth line',[(-.019,-.0535,1.642),(-.009,-.061,1.643),(0,-.062,1.642),(.01,-.060,1.643),(.019,-.053,1.642)],[.0008]*5,'mouth','head',8,sub=1)
tube('subtle lower lip',[(-.016,-.055,1.640),(0,-.0615,1.637),(.016,-.055,1.640)],[.001,.002,.001],'skin','head',10,sub=1)
# Stubble is fine individual hair, not a painted-on detached beard box.
for i in range(125):
 a=random.uniform(-1.10,1.10);z=random.uniform(1.598,1.659)
 if abs(a)<.29 and z>1.627:continue
 rx=.052+(z-1.60)*.28;ry=.047+(z-1.60)*.20;cy=.006+(z-1.60)*.16
 x=rx*sin(a);y=cy-ry*cos(a)+sculpt_front(x,z)*max(0,cos(a))**5-.0008
 tube('fine beard stubble',[(x,y,z),(x+.0003,y-.0005,z-.0020)],[.00032,.00014],'brown_hair','head',5)
# Hair: a continuous shaped scalp and short broad swept relief, not straight hanging rods.
v=[];f=[];uv=[];N=96;R=24
for j in range(R):
 for i in range(N):
  a=2*pi*i/N;t=.025+j/(R-1)*(1.70+.53*max(0,sin(a)))
  ridge=.0014*sin(a*14+t*4)+.0008*sin(a*25-t*7)
  x=(.077+ridge)*sin(t)*cos(a);y=.020+(.067+ridge)*sin(t)*sin(a);z=1.754+(.081+ridge)*cos(t)
  if j==R-1:z+=.003*sin(a*9)
  v.append((x,y,z));uv.append((i/N,j/(R-1)))
for j in range(R-1):
 for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
mesh('continuous swept brown hair sculpt',v,f,'brown_hair','head',uv,sub=1)
for i in range(24):
 a0=2*pi*i/24;start=.14+random.random()*.60;end=min(1.64,start+random.uniform(.45,.85));pts=[]
 for j in range(6):
  q=j/5;t=start+(end-start)*q;a=a0-.48*q
  pts.append((.079*sin(t)*cos(a),.020+.069*sin(t)*sin(a),1.754+.084*cos(t)))
 tube('short broad swept hair relief %02d'%i,pts,[.001,.009,.012,.010,.006,.0005],'brown_hair','head',12,flatten=.14,sub=1)
# Draped scarf: broad overlapping cloth planes, asymmetric fall and strain folds.
for k in range(3):
 rows=[]
 for j in range(25):
  a=2*pi*j/24
  p=Vector((.094*cos(a),.014+.078*sin(a),1.508+k*.017+.018*sin(a+.8)))
  rows.append([p+Vector((cos(a)*q,sin(a)*q,z)) for q,z in [(-.006,.007),(.008,0),(.012,-.012)]])
 panel('layered scarf wrap '+str(k),rows,'teal_wool','chest',.003,1)
rows=[]
for j in range(12):
 t=j/11;row=[]
 for i in range(16):
  u=i/15;x=-.155+u*.29-.025*t;z=1.535-.155*t-.025*sin(pi*u)+.012*t*cos(u*3*pi);y=-.056-.10*t-.028*sin(pi*u)-.019*sin(u*5*pi+t*.8)*t
  x=(-.145+u*.28)*(1-.38*t)-.025*t
  row.append((x,y,z))
 rows.append(row)
panel('heavy scarf front drape',rows,'teal_wool','chest',.003,1)
# Small shoulder flap on unarmoured right, controlled frayed hem (not teeth everywhere).
rows=[]
for j in range(12):
 t=j/11;row=[]
 for i in range(14):
  u=i/13;x=-.07-.24*u-.025*t;y=.005-.085*t+.025*sin(u*pi);z=1.495-.12*u-.085*t+.011*sin(u*6*pi+t)
  if j==11:z-=.006*sin(i*3.7)
  row.append((x,y,z))
 rows.append(row)
panel('asymmetric right shoulder cloth',rows,'teal_wool','chest',.002,1)
# Short back cape ends above knee, blown very slightly to right, behind pack.
rows=[]
for j in range(25):
 t=j/24;row=[]
 for i in range(32):
  u=i/31;x=(u-.5)*(.30+.19*t)-.035*t;y=.12+.078*t+.020*sin(u*7*pi+.5)*(.2+.8*t);z=1.48-.79*t-.02*sin(pi*u)
  if j==24:z+=.01*sin(i*2.7)+(.012 if i in [3,17,22] else 0)
  row.append((x,y,z))
 rows.append(row)
panel('short travel cape with weight folds',rows,'teal_wool',('cape',),.003,1)
# Pack built from contoured panel and hanging pockets, not rectangular cubes.
loft('leather travel pack',[(1.09,0,.16,.115,.048),(1.115,0,.175,.132,.060),(1.28,0,.182,.139,.064),(1.35,0,.18,.12,.05)],'oiled_leather','chest',N=48,fold=.018,sub=2)
for s in [-1,1]:
 rows=[[(s*.035,.235,1.29),(s*.077,.25,1.30),(s*.12,.236,1.29)],[(s*.03,.252,1.25),(s*.075,.266,1.24),(s*.12,.251,1.25)],[(s*.03,.251,1.21),(s*.075,.263,1.19),(s*.12,.25,1.21)]]
 panel('backpack shaped pocket flap '+str(s),rows,'dark_boots','chest',.004,1)
 band('pack fastening tab '+str(s),[(s*.075,.273,1.28),(s*.075,.276,1.21),(s*.075,.265,1.14)],.017,'worn_edges','chest')
 # outward facing buckle
 for z in [1.225]:
  p=(s*.075,.281,z);rivet(p,'chest',.004)
# Rolled wool blanket with cross-sectional spiral ends.
tube('soft rolled wool blanket',[(-.16,.158,1.39),(-.13,.167,1.399),(.12,.167,1.399),(.16,.158,1.39)],[.047,.055,.055,.047],'linen','chest',40,sub=2)
for s in [-1,1]:
 pts=[]
 for t in np.linspace(0,pi*5,85):
  r=.003+.003*t;pts.append((s*.163,.158+r*cos(t),1.390+r*sin(t)))
 tube('blanket spiral end '+str(s),pts,[.002]*len(pts),'worn_edges','chest',7)
for x in [-.102,.098]:
 pts=[(x,.167+.058*cos(a),1.399+.058*sin(a)) for a in np.linspace(0,2*pi,33)];tube('bedroll fastening strap',pts,[.008]*33,'dark_boots','chest',10,flatten=.45)
# Left amber oil flask and nearby leather pouch, fixed side across views.
ell('small amber oil flask',(.18,-.068,.942),(.034,.026,.043),'amber','pelvis',32,20)
tube('oil flask neck',[(.18,-.068,.97),(.18,-.068,1.007)],[.012,.010],'old_brass','pelvis',20)
ell('flask cork',(.18,-.068,1.009),(.011,.010,.008),'worn_edges','pelvis',16,10)
band('flask leather cradle',[(.18,-.091,.978),(.18,-.097,.94),(.18,-.082,.902)],.012,'dark_boots','pelvis')
loft('utility pouch',[(.89,-.185,.013,.037,.029),(.91,-.188,.008,.044,.037),(.99,-.182,.003,.044,.036),(1.01,-.179,.001,.039,.032)],'oiled_leather','pelvis',N=32,sub=2)
panel('pouch flap',[[(-.217,-.036,1.01),(-.182,-.044,1.014),(-.147,-.036,1.01)],[(-.216,-.04,.982),(-.181,-.048,.969),(-.148,-.04,.982)]],'dark_boots','pelvis',.003,1);rivet((-.182,-.051,.98),'pelvis',.0033)
# Sword attached to anatomical right hand. Grip fits curled finger arc.
hand=Vector((-.326,-.074,.915));axis=Vector((-.30,-.035,-.953)).normalized();right=Vector((axis.z,0,-axis.x)).normalized();front=Vector((0,-1,0))
def sp(x,y,z):return hand+right*x+front*y+axis*z
bone='hand.R'
tube('sword grip',[sp(0,0,-.065),sp(0,0,.066)],[.013,.014],'dark_boots',bone,20)
for j in range(9):
 pts=[sp(.014*cos(a),.014*sin(a),-.06+j*.014) for a in np.linspace(0,2*pi,17)];tube('sword leather binding',pts,[.0014]*17,'worn_edges',bone,6)
ell('sword pommel',sp(0,0,-.087),(.020,.017,.022),'forged_steel',bone,24,16)
tube('curved steel crossguard',[sp(-.085,0,.065),sp(-.055,0,.077),sp(0,0,.073),sp(.055,0,.077),sp(.085,0,.065)],[.008,.007,.010,.007,.008],'forged_steel',bone,16,sub=1)
verts=[sp(-.024,0,.09),sp(.024,0,.09),sp(.019,0,.62),sp(0,0,.78),sp(-.019,0,.62),sp(0,.005,.09),sp(0,.004,.62),sp(0,-.005,.09),sp(0,-.004,.62)]
mesh('forged sword bevel faces',verts,[(0,5,6,4),(5,1,2,6),(4,6,3),(6,2,3),(1,7,8,2),(7,0,4,8),(2,8,3),(8,4,3)],'forged_steel',bone,smooth=False)
tube('blade narrow fuller',[sp(0,.0055,.13),sp(0,.0048,.56)],[.0020,.0013],'steel_edge',bone,8)
# Apply modeling modifiers before armature weighting, preserving editable mesh + rig.
for o in parts:
 bpy.context.view_layer.objects.active=o
 for md in list(o.modifiers):
  bpy.ops.object.modifier_apply(modifier=md.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(o.data);bm.free()
# Actual 23-bone deform rig, rest pose anatomical and uncloned equipment.
arm=bpy.data.armatures.new('HeroStudy_Armature');rig=bpy.data.objects.new('HeroStudy_RIG',arm);COL.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
bones={}
def eb(n,h,t,p=None):
 b=arm.edit_bones.new(n);b.head=h;b.tail=t
 if p:b.parent=bones[p]
 bones[n]=b
 return b
eb('root',(0,0,0),(0,0,.2));eb('pelvis',(0,0,.92),(0,0,1.07),'root');eb('spine',(0,0,1.07),(0,0,1.29),'pelvis');eb('chest',(0,0,1.29),(0,0,1.48),'spine');eb('neck',(0,0,1.48),(0,0,1.61),'chest');eb('head',(0,0,1.61),(0,.01,1.84),'neck')
for s,side in [(-1,'R'),(1,'L')]:
 eb('clavicle.'+side,(0,0,1.43),(s*.208,.004,1.408),'chest');eb('upper_arm.'+side,(s*.208,.004,1.408),(s*.289,-.006,1.155),'clavicle.'+side);eb('forearm.'+side,(s*.289,-.006,1.155),(s*.323,-.060,.965),'upper_arm.'+side);eb('hand.'+side,(s*.323,-.060,.965),(s*.326,-.066,.883),'forearm.'+side)
 eb('thigh.'+side,(s*.106,.01,.95),(s*.106,-.018,.55),'pelvis');eb('shin.'+side,(s*.106,-.018,.55),(s*.106,.012,.125),'thigh.'+side);eb('foot.'+side,(s*.106,.012,.125),(s*.106,-.18,.045),'shin.'+side)
eb('cape',(0,.11,1.45),(0,.19,.75),'chest')
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
for o in parts:
 setting=bind[o.name];o.parent=rig
 for v in o.data.vertices:
  z=(o.matrix_world@v.co).z
  if isinstance(setting,tuple) and setting[0]=='torso':
   w=max(0,min(1,(z-1.1)/.23));weights={'spine':1-w,'chest':w}
  elif isinstance(setting,tuple) and setting[0]=='leg':
   side=setting[1];w=max(0,min(1,(z-.49)/.13));weights={'shin.'+side:1-w,'thigh.'+side:w}
  elif isinstance(setting,tuple) and setting[0]=='cape':
   w=max(0,min(1,(1.40-z)/.45));weights={'chest':1-w,'cape':w}
  else:weights={setting:1}
  for bn,w in weights.items():
   if w<=0:continue
   vg=o.vertex_groups.get(bn) or o.vertex_groups.new(name=bn);vg.add([v.index],w,'REPLACE')
 md=o.modifiers.new('Hero weighted deformation','ARMATURE');md.object=rig
# Quiet breathing idle. Root, feet and pelvis do not move; cloth and chest subtly breathe.
scene.render.fps=24;scene.frame_start=1;scene.frame_end=49
rig.animation_data_create();action=bpy.data.actions.new('hero_study__idle_breath__2s');rig.animation_data.action=action
for frame in range(1,50,6):
 t=(frame-1)/48*2*pi
 for pb in rig.pose.bones:pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.location=(0,0,0)
 rig.pose.bones['chest'].rotation_euler.x=math.radians(1.4)*sin(t)
 rig.pose.bones['head'].rotation_euler.x=math.radians(-.7)*sin(t)
 rig.pose.bones['head'].rotation_euler.y=math.radians(.8)*sin(t+.5)
 rig.pose.bones['cape'].rotation_euler.x=math.radians(2.1)*sin(t-.45)
 for side in ['L','R']:
  rig.pose.bones['upper_arm.'+side].rotation_euler.y=math.radians(.7)*sin(t+.3)
  rig.pose.bones['forearm.'+side].rotation_euler.x=math.radians(.20)*sin(t+.5)
 for bn in ['chest','head','cape','upper_arm.L','upper_arm.R','forearm.L','forearm.R']:
  rig.pose.bones[bn].keyframe_insert('rotation_euler',frame=frame,group=bn)
for fc in action.fcurves:
 for kp in fc.keyframe_points:kp.interpolation='BEZIER'
scene.frame_set(1)
# Studio: large directional soft key, modest fill, no baked long ground shadow.
world=bpy.data.worlds.new('cool studio ambient');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.15,.18,.21,1);world.node_tree.nodes['Background'].inputs[1].default_value=.32;scene.world=world
for name,loc,power,size,col in [('warm broad key',(-3.8,-4,6),560,4,(1,.85,.68)),('cool soft fill',(4,-2,3),190,3,(.67,.80,1)),('rim',(-1,3,4),420,3,(1,.91,.75))]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=col;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(2.6,-5.5,3.0));cam=bpy.context.object;cam.name='Locked orthographic art camera';cam.data.type='ORTHO';cam.data.ortho_scale=2.19;scene.camera=cam
scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=False;scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.render.resolution_percentage=100

def camera(az=25,elev=15,target=.935,scale=2.12):
 a=math.radians(az);el=math.radians(elev);cam.location=(5*sin(a),-5*cos(a),target+5*math.tan(el));cam.rotation_euler=(Vector((0,0,target))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
camera();scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.filepath=str(OUT/'previews/hero_study_front.png')
# Save before first render so interruption never loses source work.
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'hero_g1_motion_study.blend'))
bpy.ops.render.render(write_still=True)
if os.environ.get('HERO_PREVIEW_ONLY')=='1':
 print('PREVIEW_READY');raise SystemExit
# Back view for assembly continuity, camera identical elevation and scale.
camera(155);scene.render.filepath=str(OUT/'previews/hero_study_back.png');bpy.ops.render.render(write_still=True)
# Actual game camera. Target solves world root projection to (256,432).
# With 512/2.35 px/m, target z is 176/(512/2.35*cos32).
scale=2.35;target=176/(512/scale*cos(math.radians(32)))
scene.render.resolution_x=512;scene.render.resolution_y=512;scene.cycles.samples=64
for az,d in zip([45,135,225,315],['front_right','back_right','back_left','front_left']):
 camera(az,32,target,scale);scene.frame_set(1);scene.render.filepath=str(OUT/'frames'/('hero_study__idle__'+d+'__001.png'));bpy.ops.render.render(write_still=True)
# One direction 8 unique sampled idle frames. Last = first at source frame 49, not duplicate export.
camera(45,32,target,scale)
for i,fr in enumerate(range(1,49,6)):
 scene.frame_set(fr);scene.render.filepath=str(OUT/'frames'/('hero_study__idle__front_right__%03d.png'%(i+1)));bpy.ops.render.render(write_still=True)
scene.frame_set(1)
# Packed textures and relative filenames, procedural source preserved.
for im in bpy.data.images:
 if im.filepath and im.name!='Render Result':im.filepath='//../../../assets/studies/hero-g1-motion-study/textures/'+Path(im.filepath).name
scene.render.filepath='//../../../assets/studies/hero-g1-motion-study/frames/'
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/'hero_g1_motion_study.blend'))
# Interchange file is a real skinned model; Blender remains surface-authoritative.
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(OUT/'models/hero_g1_motion_study.glb'),export_format='GLB',use_selection=True,export_apply=False,export_animations=True,export_frame_range=True,export_nla_strips=False,export_force_sampling=True)
tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in parts)
manifest={'id':'hero_g1_motion_study','story_id':'char_player','status':'original procedural sculpt/material/weighted-idle study; NOT accepted final art','final_art_accepted':False,'gameplay_integrated':False,'created_utc':'2026-11-02','triangles':tri,'mesh_objects':len(parts),'deform_bones':len(arm.bones),'materials':len(M),'texture_resolution':1024,'textures':'original generated UV basecolor + height per principal material; packed in blend; not concept projection','animation':{'name':action.name,'duration_seconds':2,'fps':24,'source_frames_inclusive':[1,49],'unique_export_samples':8,'sample_duration_ms':250,'type':'quiet breathing idle only; no walk or attack'},'camera':{'type':'orthographic','elevation_degrees':32,'azimuths_degrees':[45,135,225,315],'ortho_scale':scale,'frame_size':[512,512],'root_anchor':[256,432]},'anatomical_right_hand':'-X in Blender; sword remains right-handed across views','oil_flask_side':'anatomical left +X','armored_shoulder':'anatomical left +X','source':'../../../source-art/studies/hero-g1-motion-study/hero_g1_motion_study.blend','model':'models/hero_g1_motion_study.glb','source_license':'No public license selected. No external meshes, textures, fonts, animation data or downloaded content.','reference_inputs':['../../concepts/character-direction-v1.png','../../concepts/player-four-view-v2.png'],'g1_gate':'NOT PASSED; style review and walk8/sword10 still required; idle is additional pipeline test not substitute','known_limits':['Procedural modeled face/hair not final hand sculpt','No tailored deformation topology/advanced facial rig','Idle only; no gait/contact/attack-window validation','GLB supports basecolor; node height/bump surface is Blender-authoritative','No runtime integration or device performance test']}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('HERO_STUDY_COMPLETE',tri,len(parts),len(arm.bones))
