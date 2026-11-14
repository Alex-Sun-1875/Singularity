"""Author hair guides as artwork; use native import, Bezier sampling and binding.
Curved arch ribbons with alpha strand tips replace the rejected solid hulls.
"""
from pathlib import Path
import bpy,json,hashlib,math,sys,random
from mathutils import Vector,Matrix
from mathutils.geometry import interpolate_bezier
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
import cocos_native_characters as native
SOURCE=BASE.parent/'3d-hairstyles-v1';KIT=ROOT/'src/.tools/quaternius-ready-kits/universal-base-characters-standard/Universal Base Characters[Standard]/Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)'
MODE=sys.argv[sys.argv.index('--')+1]if '--'in sys.argv and len(sys.argv)>sys.argv.index('--')+1 else'pilot'

def digest(o):
 return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices])).encode()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
original=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];head=next(o for o in original if o.get('nativePart')=='head');scalp=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
proof={'nonHairMeshHashes':{o.name:digest(o)for o in original if o.get('nativePart')!='hair'},'actionHash':pipeline.curves(),'bindHash':pipeline.skeleton(rig)}
manifest=json.loads((SOURCE/'manifest.json').read_text(encoding='utf-8'))
material=bpy.data.materials.new('Hair_Strands_v2');material.use_nodes=True;tree=material.node_tree;bs=tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.74;bs.inputs['Metallic'].default_value=0
uvnode=tree.nodes.new('ShaderNodeUVMap');uvnode.uv_map='UVMap'
def texture(name,data=False):
 n=tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(BASE/'textures'/name));n.image.colorspace_settings.name='Non-Color'if data else'sRGB';tree.links.new(uvnode.outputs['UV'],n.inputs['Vector']);return n
color=texture('hair-strands-color.png');tree.links.new(color.outputs['Color'],bs.inputs['Base Color']);tree.links.new(color.outputs['Alpha'],bs.inputs['Alpha']);normal=texture('hair-strands-normal.png',True);nm=tree.nodes.new('ShaderNodeNormalMap');nm.uv_map='UVMap';tree.links.new(normal.outputs['Color'],nm.inputs['Color']);tree.links.new(nm.outputs[0],bs.inputs['Normal'])
material.surface_render_method='DITHERED';material.use_transparency_overlap=False

def bind(obj):
 obj.parent=rig;obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=Matrix.Identity(4);obj.vertex_groups.clear();g=obj.vertex_groups.new(name='Head');g.add(range(len(obj.data.vertices)),1,'REPLACE')
 for mod in list(obj.modifiers):obj.modifiers.remove(mod)
 mod=obj.modifiers.new('Original Head binding','ARMATURE');mod.object=rig

def rootcap(style):
 sr,meshes=native.imported(KIT/'Hair_Buzzed.gltf');cap=meshes[0];correction=rig.data.bones['Head'].matrix_local@sr.data.bones['Head'].matrix_local.inverted()
 for v in cap.data.vertices:v.co=correction@v.co
 native.transfer(cap,rig);bpy.data.objects.remove(sr,do_unlink=True);pipeline.select([cap])
 for mod in list(cap.modifiers):cap.modifiers.remove(mod)
 sub=cap.modifiers.new('Authored scalp refinement','SUBSURF');sub.levels=1;bpy.ops.object.modifier_apply(modifier=sub.name)
 wrap=cap.modifiers.new('Native skull fit','SHRINKWRAP');wrap.target=head;wrap.wrap_method='NEAREST_SURFACEPOINT';wrap.wrap_mode='OUTSIDE_SURFACE';wrap.offset=.0018;bpy.ops.object.modifier_apply(modifier=wrap.name)
 for name in [l.name for l in cap.data.uv_layers][1:]:cap.data.uv_layers.remove(cap.data.uv_layers[name])
 cap.data.uv_layers[0].name='UVMap'
 slot=['curly','dante','nero','vergil'].index(style)
 for p in cap.data.polygons:
  values=[]
  for li in p.loop_indices:
   co=cap.data.vertices[cap.data.loops[li].vertex_index].co;u=(math.atan2(co.x,-(co.y-.015))+math.pi)/(2*math.pi);v=max(0,min(1,(co.z-1.635)/.185));values.append((li,u,v))
  seam=max(x[1]for x in values)-min(x[1]for x in values)>.5
  for li,u,v in values:
   if seam:u=0 if u<.5 else 1
   cap.data.uv_layers[0].data[li].uv=((slot*512+8+u*496)/2048,(8+v*496)/2048)
 cap.data.materials.clear();cap.data.materials.append(material)
 for p in cap.data.polygons:p.material_index=0;p.use_smooth=True
 return cap

def surface(theta,phi,lift=.002):
 approx=Vector((.079*math.sin(theta)*math.sin(phi),.015-.104*math.sin(theta)*math.cos(phi),1.693+.118*math.cos(theta)))
 near,n,_,_=scalp.find_nearest(approx)
 return near+n*lift if near is not None else approx

def sampled(points,steps=5):
 p=[Vector(v)for v in points];out=[]
 for i in range(len(p)-1):
  h1=p[i]+(p[i+1]-(p[i-1]if i else p[i]))/6;h2=p[i+1]-((p[i+2]if i+2<len(p)else p[i+1])-p[i])/6
  out+=list(interpolate_bezier(p[i],h1,h2,p[i+1],steps+1))[:-1]
 result=out+[p[-1]]
 for i,co in enumerate(result):
  near,n,_,distance=scalp.find_nearest(co)
  if near is not None and distance<.025 and (co-near).dot(n)<.002:result[i]=near+n*.002
 return result

def ribbon_mesh(guides):
 verts=[];faces=[];uvs=[];rng=random.Random(937)
 for guide in guides:
  points=sampled(guide['points']);n=len(points);slot=guide.get('slot',rng.randrange(4));width=guide['width'];arch=guide.get('arch',.0022)
  radial=points[0]-Vector((0,.015,1.69));radial.normalize();tan=(points[1]-points[0]).normalized();basis=tan.cross(radial)
  if basis.length<.1:basis=Vector((1,0,0))
  basis.normalize();offset=len(verts)
  sections=8
  for i,p in enumerate(points):
   t=i/(n-1);tangent=(points[min(n-1,i+1)]-points[max(0,i-1)]).normalized();side=basis-tangent*basis.dot(tangent)
   if side.length<.05:side=tangent.cross(Vector((0,0,1)))
   side.normalize();outward=side.cross(tangent).normalized();envelope=max(.045,(.85+.15*math.sin(math.pi*t))*(max(0,1-t**4))**.35)
   for j in range(sections):
    angle=2*math.pi*j/sections;s=math.cos(angle);u=(s+1)/2;pos=p+side*(s*width*.72*envelope)+outward*(math.sin(angle)*arch*1.65*envelope)
    verts.append(tuple(pos));uvs.append(((slot*512+8+u*496)/2048,.25+(8+(1-t)*1520)/2048))
  for i in range(n-1):
   for j in range(sections):
    a=offset+i*sections+j;an=offset+i*sections+(j+1)%sections;b=a+sections;bn=an+sections;faces.append((a,an,bn,b))
 mesh=bpy.data.meshes.new('Layered arched hair ribbons');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('HairRibbonLayers',mesh);bpy.context.scene.collection.objects.link(obj);obj.parent=rig;obj.matrix_parent_inverse=Matrix.Identity(4);obj.matrix_basis=Matrix.Identity(4);uv=mesh.uv_layers.new(name='UVMap')
 for p in mesh.polygons:
  p.use_smooth=True
  for li in p.loop_indices:uv.data[li].uv=uvs[mesh.loops[li].vertex_index]
 mesh.materials.append(material);return obj

def curls():
 guides=[];rng=random.Random(731)
 # The drawing's pronounced off-centre swept fringe, in individual broad waves.
 front=[[(.050,.012,1.807),(.030,-.033,1.846),(-.012,-.071,1.848),(-.045,-.096,1.817),(-.046,-.098,1.783),(-.029,-.097,1.777)],
 [(.066,.002,1.794),(.052,-.040,1.835),(.018,-.079,1.846),(-.011,-.100,1.820),(-.021,-.100,1.790)],
 [(.030,.035,1.808),(.004,-.003,1.851),(-.038,-.043,1.842),(-.069,-.066,1.806),(-.064,-.073,1.770)],
 [(.059,-.004,1.795),(.083,-.030,1.817),(.091,-.056,1.789),(.087,-.061,1.751),(.076,-.064,1.738)],
 [(-.025,.022,1.809),(-.054,-.003,1.831),(-.087,-.034,1.805),(-.094,-.044,1.768),(-.084,-.048,1.738)]]
 for k,p in enumerate(front):
  near,n,_,_=scalp.find_nearest(Vector(p[0]));p[0]=tuple(near+n*.001)
  guides.append({'points':p,'width':.026 if k<3 else .020,'arch':.0038,'slot':k%4})
  for child in range(2):
   q=[(x+(child-.5)*.004,y+.002,z+(child-.5)*.003)for x,y,z in p];guides.append({'points':q,'width':.012,'arch':.0017,'slot':(k+child+1)%4})
 # Side/back waves are hand-zoned, with alternating S flow and staggered ends.
 for row,theta in enumerate([.22,.50,.80,1.10,1.39,1.66]):
  count=[9,12,15,17,17,14][row]
  for k in range(count):
   phi=2*math.pi*(k+.38*(row%2))/count
   if math.cos(phi)>.48:continue
   length=.58+rng.uniform(-.08,.12);points=[]
   for j in range(9):
    t=j/8;th=theta+length*t-.065*math.sin(math.pi*t);angle=phi+(.15 if row%2 else-.15)*math.sin(t*math.pi*2)*math.sin(math.pi*t)**.3
    lift=.0025+(.010 if row<3 else .007)*math.sin(math.pi*t);p=surface(th,angle,lift)
    if j==8:p.z+=.004
    points.append(tuple(p))
   width=.021 if row<3 else .017
   guides.append({'points':points,'width':width,'arch':.003,'slot':(k+row)%4})
   # Wispy upper sheet breaks the broad wave edges without making tubes.
   q=[(x+rng.uniform(-.0015,.0015),y+rng.uniform(-.0015,.0015),z+.002)for x,y,z in points]
   guides.append({'points':q,'width':width*.65,'arch':.0017,'slot':(k+row+2)%4})
 # Swept crown ridges connect the fringe to the back without a flat cap.
 for k,x in enumerate([-.055,-.032,-.008,.016,.040]):
  near,n,_,_=scalp.find_nearest(Vector((x,.028,1.80)));points=[tuple(near+n*.001),(x-.009,.030,1.844),(x-.016,.065,1.831),(x-.006,.094,1.797),(x+.006,.102,1.768)]
  guides.append({'points':points,'width':.021,'arch':.003,'slot':k%4})
 return guides

def add_layer(guides,points,width,slot=0,arch=.002,children=1):
 near,n,_,_=scalp.find_nearest(Vector(points[0]));points[0]=tuple(near+n*.001)
 guides.append({'points':points,'width':width,'slot':slot%4,'arch':arch})
 for j in range(children):
  q=[(x+(j-.5)*.0015,y+.0008,z+.0015)for x,y,z in points]
  guides.append({'points':q,'width':width*.60,'slot':(slot+j+1)%4,'arch':arch*.6})

def curtains():
 guides=[]
 for side in [-1,1]:
  for k,y in enumerate([-.072,-.050,-.028,-.006,.016,.038,.062,.080]):
   near,n,_,_=scalp.find_nearest(Vector((side*.007,y,1.80)));z=near.z;drift=-.026 if y<-.025 else .045
   points=[tuple(near+n*.001),(side*.028,y+drift*.1,z+.025),(side*.062,y+drift*.3,z+.008),(side*.079,y+drift*.7,z-.042),(side*.078,y+drift,max(1.635,z-.118)),(side*.071,y+drift+.002,max(1.64,z-.108))]
   add_layer(guides,points,.021 if k<4 else .018,k,arch=.0026,children=2)
  # Individual curtain fringe tips frame the eyes instead of covering them.
  for k in range(3):
   x=side*(.009+k*.005);points=[(x,-.064,1.790),(side*(.026+k*.006),-.091,1.815),(side*(.060+k*.005),-.105,1.770),(side*(.076+k*.002),-.100,1.702),(side*(.073+k*.002),-.096,1.687+k*.003)]
   add_layer(guides,points,.018,k+1,arch=.0023,children=1)
 for row,theta in enumerate([.75,1.12,1.46]):
  for k in range(11):
   phi=1.72+(2*math.pi-3.44)*k/10;points=[]
   for j in range(6):
    t=j/5;p=surface(theta+.82*t,phi+.04*math.sin(t*math.pi),.002+.004*math.sin(t*math.pi));p.x+=.002*math.sin(t*4+k);points.append(tuple(p))
   add_layer(guides,points,.015,row+k,arch=.0018,children=1)
 return guides

def crop():
 guides=[];k=0
 for y in [-.065,-.038,-.011,.016,.043,.070,.092]:
  for x in [-.063,-.039,-.014,.012,.038,.062]:
   radius=(x/.082)**2+((y-.015)/.113)**2
   if radius>.90:continue
   guess=Vector((x,y,1.693+.118*math.sqrt(1-radius)));near,n,_,_=scalp.find_nearest(guess);root=near+n*.0015
   points=[tuple(root),tuple(root+n*.010+Vector((.001*math.sin(k),-.006,0))),tuple(root+n*.027+Vector((.002*math.sin(k),-.014,.001))),tuple(root+n*.022+Vector((.003*math.sin(k),-.027,-.002)))]
   add_layer(guides,points,.012,k,arch=.0016,children=1);k+=1
 for side in [-1,1]:
  for j,theta in enumerate([1.03,1.25,1.43]):
   for k,phi in enumerate([1.18,1.48,1.80,2.12]):
    points=[tuple(surface(theta+.18*t,side*(phi+.18*t),.002+.0015*math.sin(t*math.pi)))for t in [0,.33,.67,1]]
    add_layer(guides,points,.008,j+k,arch=.0007,children=0)
 return guides

def swept():
 guides=[]
 for k,x in enumerate([-.068,-.054,-.040,-.026,-.012,.002,.016,.030,.044,.058,.070]):
  ax=abs(x);z=1.771+.020*math.sin(math.pi*ax/.083)
  points=[(x,-.082+ax*.18,z),(x*.97,-.052,1.820-ax*.12),(x*.91,.006,1.848-ax*.20),(x*.85,.066,1.820-ax*.22),(x*.78,.112,1.752-ax*.12)]
  add_layer(guides,points,.018,k,arch=.0028,children=2)
 for side in [-1,1]:
  for row,theta in enumerate([.92,1.14,1.36,1.52]):
   for k,phi in enumerate([1.10,1.38,1.66,1.94]):
    points=[tuple(surface(theta+.22*t,side*(phi+.32*t),.002+.002*math.sin(t*math.pi)))for t in [0,.25,.5,.75,1]]
    add_layer(guides,points,.011,row+k,arch=.0012,children=1)
 for k in range(9):
  phi=2.15+k*.25;points=[tuple(surface(1.48+.49*t,phi+.06*t,.002+.001*math.sin(t*math.pi)))for t in [0,.33,.67,1]]
  add_layer(guides,points,.010,k,arch=.001,children=0)
 return guides

stylesToBuild=['curly']if MODE=='pilot'else['curly','dante','nero','vergil']
allGuides={}
for style in stylesToBuild:
 guide={'curly':curls,'dante':curtains,'nero':crop,'vergil':swept}[style]();allGuides[style]=guide;cap=rootcap(style);cards=ribbon_mesh(guide);bpy.context.view_layer.update();assert all(abs(cap.matrix_world[i][j]-cards.matrix_world[i][j])<1e-6 for i in range(4)for j in range(4));pipeline.select([cap,cards]);bpy.context.view_layer.objects.active=cap;bpy.ops.object.join();hair=bpy.context.object
 for name in next(s for s in manifest['hairstyles']if s['id']==style)['nodes']:
  old=bpy.data.objects.get(name)
  if old:bpy.data.objects.remove(old,do_unlink=True)
 hair.name='raphael_native_hair_'+style.title()+'_Strands';hair['nativePart']='hair';hair['hairstyleId']=style;bind(hair)
 for s in manifest['hairstyles']:
  if s['id']==style:s['nodes']=[hair.name];s['triangles']=pipeline.triangles(hair)

manifest['materials']=[m for m in manifest['materials']if 'hair'not in m.get('parts',[])or MODE=='pilot'and m['runtimeName']!='Hair_2D_Reference_v6']+[{'runtimeName':material.name,'parts':['hair'],'maps':{'albedo':'../hairstyles-v2/textures/hair-strands-color.png','normal':'../hairstyles-v2/textures/hair-strands-normal.png'},'sourcePBR':{'effectiveFactors':{'roughness':.74,'metallic':0}},'alphaClip':True,'doubleSided':True,'alphaThreshold':.22}]
manifest['parts']['hair']['nodes']=[n for s in manifest['hairstyles']for n in s['nodes']]
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert len(objects)==16 and {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']
manifest.update(appearanceRevision='hairstyles-v2-'+MODE,appearanceReview=(BASE/'README.md').relative_to(ROOT).as_posix(),source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),triangles=sum(pipeline.triangles(o)for o in objects))
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
bpy.context.scene.frame_set(0);pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
for o in objects:o.hide_render=False
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
for o in objects:
 if o.get('nativePart')=='hair':o.hide_render=o.get('hairstyleId')!='curly'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n');(BASE/'guides.json').write_text(json.dumps(allGuides,indent=2)+'\n',encoding='utf-8',newline='\n');proof.update(mode=MODE,guides={k:len(v)for k,v in allGuides.items()},faceBodyUnchanged=True,all14ActionsUnchanged=True);(BASE/'preservation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8',newline='\n')
print('STRAND_GROOM_EXPORTED',proof['guides'],manifest['triangles'],flush=True)
