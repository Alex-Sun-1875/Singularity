from pathlib import Path
import bpy,math,random,json,os
from mathutils import Vector
from math import sin,cos,pi
random.seed(17)
BASE=str(Path(__file__).resolve().parents[2] / 'assets/studies/player-refined')
for folder in ['models','props','sprites','previews']:
 (Path(BASE)/folder).mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
M={}
def mat(n,c,met=0,r=.7):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=met;p.inputs['Roughness'].default_value=r;M[n]=m
for a in [('skin',(.48,.285,.17),0,.68),('skin_hi',(.60,.37,.23)),('lip',(.31,.14,.10)),('eye',(.63,.60,.48)),('iris',(.09,.13,.12)),('hair',(.045,.03,.02)),('hair_hi',(.075,.046,.025)),('leather',(.105,.055,.027)),('leather_hi',(.18,.095,.04)),('edge',(.27,.16,.075)),('steel',(.26,.30,.31),.8,.38),('steel_edge',(.42,.45,.44),.75,.42),('darksteel',(.10,.13,.14),.65,.5),('cloth',(.35,.30,.21)),('pants',(.095,.088,.073)),('teal',(.045,.14,.155)),('teal_hi',(.065,.19,.20)),('bronze',(.32,.20,.085),.65,.5),('amber',(.37,.105,.025),.15,.3),('black',(.025,.023,.02))]:mat(*a)
root=bpy.data.objects.new('model_player_refined',None);bpy.context.collection.objects.link(root)
def finish(o,n,m,smooth=True):
 o.name=n;o.parent=root;o.data.materials.append(M[m])
 if o.type=='MESH':
  for p in o.data.polygons:p.use_smooth=smooth
 return o
def mesh(n,v,f,m,smooth=True):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.update();o=bpy.data.objects.new(n,me);bpy.context.collection.objects.link(o);return finish(o,n,m,smooth)
def ell(n,loc,sc,m,seg=16,rings=10):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=loc);o=bpy.context.object;o.scale=sc;return finish(o,n,m)
def box(n,loc,sc,m,b=.01,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.scale=sc;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.rotation_euler=rot;mod=o.modifiers.new('rounded worn edges','BEVEL');mod.width=b;mod.segments=3;o.modifiers.new('weighted normals','WEIGHTED_NORMAL');return finish(o,n,m,False)
def tube(n,points,radii,m,segs=8):
 v=[];f=[]
 for j,p in enumerate(points):
  tangent=Vector(points[min(j+1,len(points)-1)])-Vector(points[max(0,j-1)])
  q=tangent.to_track_quat('Z','Y')
  for i in range(segs):v.append(Vector(p)+q@Vector((radii[j]*cos(2*pi*i/segs),radii[j]*sin(2*pi*i/segs),0)))
 for j in range(len(points)-1):
  for i in range(segs):f.append((j*segs+i,j*segs+(i+1)%segs,(j+1)*segs+(i+1)%segs,(j+1)*segs+i))
 f.extend([tuple(range(segs-1,-1,-1)),tuple((len(points)-1)*segs+i for i in range(segs))]);return mesh(n,v,f,m)
def loft(n,rings,m,N=20):
 # z, xcenter,ycenter,xradius,yradius, wrinkle amplitude
 v=[];f=[]
 for j,(z,x,y,rx,ry,w) in enumerate(rings):
  for i in range(N):
   a=2*pi*i/N;k=1+w*sin(i*2.7+j*1.8);v.append((x+rx*cos(a)*k,y+ry*sin(a)*k,z))
 for j in range(len(rings)-1):
  for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
 f.extend([tuple(range(N-1,-1,-1)),tuple((len(rings)-1)*N+i for i in range(N))]);return mesh(n,v,f,m)
def patch(n,v,m,th=.008):
 o=mesh(n,v,[tuple(range(len(v)))],m);mod=o.modifiers.new('leather or cloth thickness','SOLIDIFY');mod.thickness=th;bev=o.modifiers.new('soft panel edges','BEVEL');bev.width=.003;bev.segments=2;return o
def rivet(p):ell('small peened rivet',p,(.008,.005,.008),'bronze',8,5)
def belt(n,z,rx,ry,m,width=.04):
 return loft(n,[(z-width/2,0,0,rx,ry,0),(z+width/2,0,0,rx,ry,0)],m,28)
def buckle(p,w=.045,h=.052):
 x,y,z=p
 for a,b in [((x-w/2,y,z-h/2),(x+w/2,y,z-h/2)),((x-w/2,y,z+h/2),(x+w/2,y,z+h/2)),((x-w/2,y,z-h/2),(x-w/2,y,z+h/2)),((x+w/2,y,z-h/2),(x+w/2,y,z+h/2)),((x,y-.003,z),(x+w/2,y-.003,z))]:tube('forged buckle', [a,b],[.004,.004],'steel_edge',6)
# Adult anatomy: 1.86m height, head about .26m.
for s in [-1,1]:
 x=s*.115
 loft('creased wool trouser',[(.39,x,0,.064,.067,0),(.53,x,-.005,.075,.079,.09),(.58,x,-.02,.079,.076,.06),(.63,x,-.015,.08,.085,.08),(.72,x,.005,.091,.092,.04),(.84,x,.02,.10,.105,.025),(1.00,x,.015,.11,.11,0)],'pants',20)
 # shaped tall riding boot, foot overlaps naturally
 loft('shaped leather riding boot',[(.10,x,0,.064,.066,0),(.18,x,.015,.061,.061,.025),(.23,x,.02,.057,.055,.03),(.33,x,.013,.062,.062,.025),(.43,x,0,.075,.071,.02),(.49,x,0,.08,.075,0)],'leather',20)
 ell('rounded boot vamp',(x,-.075,.075),(.079,.157,.062),'leather_hi',20,10)
 ell('layered leather sole',(x,-.07,.028),(.083,.16,.023),'black',20,8)
 # instep folds and shin seam
 for z,ry in [(.17,.066),(.22,.062),(.29,.065),(.43,.075)]:
  tube('boot wear fold',[(x-.05,-ry+.01,z+.012),(x,-ry-.008,z),(x+.05,-ry+.01,z-.006)],[.008,.009,.006],'leather_hi')
 tube('boot stitched shin',[(x+.045,-.055,.19),(x+.049,-.061,.34),(x+.052,-.061,.46)],[.003]*3,'edge',5)
 for z in [.26,.40]:
  box('boot ankle strap',(x,-.066,z),(.13,.018,.025),'leather_hi',.005);buckle((x+s*.035,-.078,z),.027,.026)
# torso shaped waist/ribs/shoulders
loft('fitted layered leather cuirass',[(.93,0,0,.19,.116,0),(1.02,0,0,.17,.12,0),(1.15,0,.005,.17,.125,0),(1.30,0,.008,.21,.14,0),(1.43,0,.015,.23,.13,0),(1.48,0,.025,.18,.10,0)],'leather',28)
# asymmetric overlapping front breast panels
for s in [-1,1]:
 for j in range(3):
  z=1.08+j*.105;v=[(s*.012,-.137,z-.025),(s*(.16+j*.015),-.095,z+.035),(s*(.18+j*.015),-.10,z+.13),(s*.014,-.146,z+.085)]
  patch('diagonal reinforced cuirass panel',v,'leather_hi' if j%2 else 'leather')
  for p in [v[0],v[1]]:rivet((p[0],p[1]-.012,p[2]+.012))
# skirt overlapping tapered tassets following body not box slabs
for i in range(9):
 a=2*pi*i/9;v=[]
 for z,r,da in [(1.0,.20,-.27),(1.0,.20,.27),(.73,.25,.24),(.71,.25,-.24)]:v.append((r*sin(a+da),-r*.65*cos(a+da),z))
 patch('layered leather skirt tasset',v,'leather_hi' if i%3 else 'leather',.012)
 rivet((v[0][0],v[0][1]-.005,v[0][2]-.025))
 # inset seam down lower edges
 tube('tasset stitched edge',[Vector(v[0])*.95+Vector(v[3])*.05,Vector(v[0])*.08+Vector(v[3])*.92],[.0025,.0025],'edge',5)
belt('wide waist sword belt',1.015,.205,.139,'leather_hi',.06);buckle((-.015,-.146,1.015),.065,.065)
# crossing harness strips cut over chest surface
for s in [-1,1]:
 v=[(s*.18,-.10,1.45),(s*.21,-.10,1.425),(-s*.115,-.157,1.06),(-s*.15,-.145,1.08)]
 patch('cross body baldric',v,'leather_hi',.009)
 for t in [.2,.5,.8]:
  p=Vector(v[0]).lerp(Vector(v[3]),t);rivet((p.x,p.y-.012,p.z))
buckle((.105,-.156,1.30),.038,.047)
# sleeve arms lowered and slightly out, natural taper; hands at thigh
for s in [-1,1]:
 shoulder=(s*.22,.005,1.43);elbow=(s*.295,-.015,1.17);wrist=(s*.33,-.065,.98)
 tube('linen upper sleeve',[shoulder,(s*.26,-.003,1.36),(s*.285,-.004,1.27),elbow],[.083,.087,.075,.068],'cloth',16)
 # loose diagonal cloth wrinkles distinct from armored cylinders
 for j in range(5):
  z=1.20+j*.035;x=s*(.292-j*.008)
  tube('linen sleeve fold',[(x-.044,-.052,z+.015),(x,-.075,z),(x+.045,-.05,z-.008)],[.007,.011,.006],'cloth',8)
 tube('leather forearm gauntlet',[elbow,(s*.31,-.04,1.08),wrist],[.071,.060,.047],'leather',16)
 # long rounded dorsal vambrace follows arm
 patch('curved dorsal steel vambrace',[(s*.26,-.071,1.17),(s*.335,-.067,1.17),(s*.365,-.10,.99),(s*.30,-.113,.98)],'steel',.015)
 for j in range(2):
  z=1.04+j*.095;box('vambrace leather fastening',(s*.325,-.109,z),(.075,.016,.025),'leather_hi',.005);rivet((s*.30,-.122,z))
 palm=(s*.34,-.075,.925);ell('anatomical glove palm',palm,(.044,.028,.063),'leather_hi',16,10)
 # separate curled finger segments, small knuckles
 for j in range(4):
  x=s*(.312+j*.018);z=.91-(.009 if j in [0,3] else 0)
  tube('individual curled glove finger',[(x,-.091,z),(x,-.108,z-.031),(x,-.092,z-.049)],[.010,.011,.008],'leather_hi',8)
  ell('glove knuckle',(x,-.102,z),(.011,.009,.012),'leather',10,6)
 tube('opposed glove thumb',[(s*.30,-.07,.947),(s*.286,-.103,.923),(s*.30,-.115,.90)],[.016,.013,.010],'leather_hi',8)
# Rounded layered shoulder steel, one dominant rather than two cubes
for side in [-1,1]:
 for layer in range(2 if side==1 else 1):
  x=side*(.225+layer*.025);z=1.445-layer*.06
  v=[];f=[];N=16;rows=5
  for j in range(rows):
   t=(.15+j*.31)
   for i in range(N):
    a=2*pi*i/N;v.append((x+.125*sin(t)*cos(a),.006+.112*sin(t)*sin(a),z+.075*cos(t)))
  for j in range(rows-1):
   for i in range(N):f.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
  f.append(tuple(range(N-1,-1,-1)))
  o=mesh('curved overlapping steel pauldron',v,f,'steel');mod=o.modifiers.new('steel shell thickness','SOLIDIFY');mod.thickness=.009
  tube('rolled pauldron rim',v[-N:]+[v[-N]],[.006]*(N+1),'steel_edge',6)
  for i in [9,11,13]:rivet(v[-N+i])
# neck and facial sculpt constructed from shaped smooth rings
loft('neck',[(1.44,0,.01,.058,.056,0),(1.58,0,.015,.051,.052,0)],'skin',16)
loft('adult head shaped jaw and cheek planes',[(1.57,0,-.005,.035,.038,0),(1.595,0,-.002,.056,.052,0),(1.64,0,0,.067,.062,0),(1.69,0,.006,.079,.066,0),(1.735,0,.012,.079,.070,0),(1.78,0,.014,.076,.068,0),(1.815,0,.016,.059,.052,0),(1.835,0,.016,.016,.019,0)],'skin',24)
for s in [-1,1]:
 ell('ear',(s*.078,.013,1.70),(.016,.025,.035),'skin',12,8)
 ell('sculpted cheekbone',(s*.043,-.048,1.686),(.032,.022,.023),'skin',16,10)
 ell('eye socket',(s*.034,-.054,1.727),(.030,.015,.014),'leather',16,8)
 ell('eyeball',(s*.033,-.065,1.726),(.022,.009,.009),'eye',16,8)
 ell('iris',(s*.032,-.073,1.726),(.007,.002,.007),'iris',12,8)
 tube('upper eyelid',[(s*.013,-.067,1.73),(s*.033,-.075,1.736),(s*.053,-.063,1.731)],[.003,.004,.003],'skin_hi',6)
 tube('strong expressive eyebrow',[(s*.012,-.065,1.746),(s*.035,-.071,1.752),(s*.057,-.056,1.746)],[.005,.006,.003],'hair',7)
# projected nose with actual bridge, nostrils, narrow mouth and lower lip
ell('nose bridge',(0,-.060,1.712),(.013,.019,.032),'skin_hi',14,10)
ell('nose tip',(0,-.081,1.692),(.017,.020,.012),'skin',14,8)
for s in [-1,1]:ell('nostril',(s*.012,-.080,1.684),(.007,.006,.004),'lip',10,6)
tube('upper lip',[(-.022,-.057,1.656),(-.008,-.066,1.659),(0,-.067,1.656),(.009,-.066,1.659),(.023,-.057,1.656)],[.003]*5,'lip',6)
ell('lower lip',(0,-.061,1.649),(.021,.007,.004),'skin_hi',14,8)
# dark short beard mesh patches around chin/jaw, not giant geometric cube
for s in [-1,1]:
 tube('short sideburn',[(s*.067,-.019,1.748),(s*.068,-.029,1.692),(s*.052,-.037,1.65)],[.009,.011,.008],'hair',8)
 for j in range(7):
  x=s*(.008+j*.006);z=1.61+j*.004;y=-.043-j*.0007
  tube('trimmed beard strand',[(x,y,z+.022),(x,y-.004,z)],[.004,.002],'hair_hi',5)
# hair cap and swept curved individual locks, continuous tapered strands
ell('hair undercap',(0,.022,1.799),(.078,.067,.05),'hair',20,12)
for i in range(28):
 a=2*pi*i/28;x=.067*cos(a);y=.015+.060*sin(a)
 pts=[(x*.7,y*.7,1.81),(x*.95-.014,y-.013,1.845+random.random()*.016),(x-.025,y-.037,1.82),(x-.031,y-.044,1.78+random.random()*.025)]
 tube('swept sculpted hair lock',pts,[.017,.018,.013,.001],'hair_hi' if i%4==0 else 'hair',7)
# draped neck wrap with multiple folds, loose front triangle and shoulder tail
for j in range(3):
 points=[]
 for i in range(25):
  a=2*pi*i/24;points.append((.082*cos(a),.018+.072*sin(a),1.52+j*.020+.014*sin(a+.7)))
 tube('wrapped teal scarf fold',points,[.018]*25,'teal_hi' if j==1 else 'teal',8)
patch('scarf front drape',[(-.13,-.04,1.56),(.075,-.07,1.52),(.005,-.16,1.37),(-.11,-.13,1.43)],'teal',.012)
for j in range(3):tube('scarf fall crease',[(-.10+j*.055,-.10,1.53),(-.065+j*.033,-.159,1.43)],[.006,.003],'teal_hi',6)
# full gridded cape with undulating cloth folds and ragged hem, much less flat
v=[];f=[];nx=16;ny=18
for j in range(ny):
 t=j/(ny-1)
 for i in range(nx):
  u=i/(nx-1);x=(u-.5)*(.38+.21*t);y=.175+.075*t+.025*sin(u*7*pi)*(t+.1);z=1.51-.86*t-.06*sin(pi*u)+(.025*sin(i*5.3) if j==ny-1 else 0);v.append((x,y,z))
for j in range(ny-1):
 for i in range(nx-1):
  if j==ny-2 and i in [1,9,13]:continue
  f.append((j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i))
o=mesh('draped teal travel cape with torn hem',v,f,'teal');o.modifiers.new('cloth thickness','SOLIDIFY').thickness=.008
# gear and realistic small utility details
box('belt pouch',(-.20,-.02,.96),(.09,.10,.14),'leather_hi',.025);box('pouch flap',(-.20,-.073,1.01),(.095,.018,.06),'leather',.01);rivet((-.20,-.088,.99))
ell('amber oil flask',(.205,-.065,.945),(.039,.029,.05),'amber',16,10)
tube('flask neck',[(.205,-.065,.974),(.205,-.065,1.02)],[.017,.012],'steel',12)
box('flask leather cradle',(.205,-.096,.94),(.018,.012,.085),'leather',.004)
# bedroll tucked behind shoulder
roll=tube('rolled blanket',[(-.13,.17,1.43),(.15,.17,1.43)],[.065,.065],'cloth',20)
for x in [-.09,.10]:
 pts=[(x,.17+.069*cos(a*2*pi/18),1.43+.069*sin(a*2*pi/18)) for a in range(19)];tube('bedroll straps',pts,[.009]*19,'leather',6)
# sword held downwards with a local gear root transform via point mapping
hand=Vector((-.35,-.10,.91));axis=Vector((-.26,-.025,-.965)).normalized();right=Vector((axis.z,0,-axis.x)).normalized();front=Vector((0,-1,0))
def sp(x,y,z):return hand+right*x+front*y+axis*z
tube('wrapped sword grip',[sp(0,0,-.09),sp(0,0,.065)],[.019,.019],'leather',12)
for j in range(7):tube('grip binding ring',[sp(.020*cos(a*2*pi/12),.020*sin(a*2*pi/12),-.08+j*.021) for a in range(13)],[.0025]*13,'edge',5)
ell('steel sword pommel',sp(0,0,-.115),(.027,.022,.03),'steel',12,8)
tube('swept sword guard',[sp(-.11,0,.07),sp(-.065,0,.085),sp(0,0,.075),sp(.065,0,.085),sp(.11,0,.07)],[.012,.010,.014,.010,.012],'steel_edge',8)
verts=[sp(-.026,0,.10),sp(.026,0,.10),sp(.021,0,.65),sp(0,0,.83),sp(-.021,0,.65),sp(0,.007,.10),sp(0,.006,.65),sp(0,-.007,.10),sp(0,-.006,.65)]
mesh('forged blade bevels',verts,[(0,5,6,4),(5,1,2,6),(4,6,3),(6,2,3),(1,7,8,2),(7,0,4,8),(2,8,3),(8,4,3)],'steel_edge',False)
# render studio - image proof first
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=72;scene.cycles.use_denoising=False
scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.world.color=(.18,.18,.18)
bpy.ops.object.camera_add(location=(2.7,-6,3.2));cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.25
cam.rotation_euler=(Vector((0,0,.94))-cam.location).to_track_quat('-Z','Y').to_euler()
for name,loc,power,size in [('large warm key',(-3,-4,6),450,4),('soft fill',(4,-2,3),190,3),('rim',(2,4,4),500,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.view_transform='AgX';scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.render.filepath=BASE+'/previews/player_refined_mesh.png';bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT');root.select_set(True)
for o in root.children_recursive:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=BASE+'/models/model_player_refined.glb',export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
# fixed actual model renders, not concept images
scene.render.resolution_x=512;scene.render.resolution_y=512;cam.data.ortho_scale=2.2
for a,d in zip([45,135,225,315],['front_right','back_right','back_left','front_left']):
 az=math.radians(a);cam.location=(5*sin(az),-5*cos(az),.94+5*math.tan(math.radians(32)));cam.rotation_euler=(Vector((0,0,.94))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=BASE+'/sprites/model_player_refined_'+d+'.png';bpy.ops.render.render(write_still=True)
scene.render.filepath='//renders/'
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('player_refined.blend')))
dg=bpy.context.evaluated_depsgraph_get();tri=0
for o in root.children_recursive:
 if o.type=='MESH':
  eo=o.evaluated_get(dg);me=eo.to_mesh();me.calc_loop_triangles();tri+=len(me.loop_triangles);eo.to_mesh_clear()
json.dump({'path_base':'relative_to_this_manifest','final_art_accepted':False,'id':'model_player_refined','story_id':'char_player','status':'unapproved procedural higher-detail static proof, not concept-fidelity final sculpt','triangles':tri,'mesh_parts':len(root.children_recursive),'rig':False,'animations':[],'units':'meters','forward_blender':'-Y','up_blender':'Z','up_glb':'Y','license':'No public license selected','provenance':'Original procedural geometry and flat PBR materials created for this project; no third-party meshes or textures.','files':['models/model_player_refined.glb','../../../source-art/player-refined/player_refined.blend','previews/player_refined_mesh.png'],'sprite_size':[512,512],'camera_elevation':32},open(BASE+'/manifest.json','w'),ensure_ascii=False,indent=2)
print('REFINED_BUILD_COMPLETE',tri)
